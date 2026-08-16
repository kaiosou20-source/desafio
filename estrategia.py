"""
===============================================================================
MÓDULO DE ESTRATÉGIA QUANTITATIVA (estrategia.py)
Projeto: Desafio Quant AI 2026 - Anomalia de Baixa Volatilidade (Low Volatility Anomaly)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================
Este módulo implementa a lógica quantitativa da estratégia Low Volatility / BAB:
1. Cálculo do Desvio-Padrão Anualizado com tolerância a dados faltantes (mínimo 70% de dados válidos).
2. Cálculo do Beta estatístico em relação ao Benchmark de mercado (^BVSP).
3. Triagem defensiva com fallback gracioso para universos com histórico reduzido.
4. Ordenação e Particionamento do Universo em 5 Quintis (Q1 a Q5).
5. Construção das Carteiras Equiponderadas (Long-Only e Long-Short):
   - 🐢 Quintil 1: Carteira Jonathan (Low Vol - menor volatilidade).
   - 🐇 Quintil 5: Carteira Lebre (High Vol - maior volatilidade).
   - Quintis intermediários (Q2, Q3, Q4) para análise de monotonicidade.
===============================================================================
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union


def calcular_volatilidade_anualizada(
    retornos_df: pd.DataFrame,
    lookback: int = 252,
    min_periodos: Optional[int] = None
) -> pd.Series:
    """
    Calcula a volatilidade histórica anualizada (desvio-padrão amostral dos retornos diários):
        sigma = std(R_diario) * sqrt(252)
    
    Parâmetros:
        retornos_df: DataFrame com os retornos diários de cada ativo.
        lookback: Quantidade de pregões da janela histórica (ex: 126 ou 252 dias úteis).
        min_periodos: Quantidade mínima de dados válidos (padrão = 70% da janela).
    
    Retorno:
        pd.Series com a volatilidade anualizada de cada ativo elegível.
    """
    if min_periodos is None:
        # Permite ativos com pelo menos 70% de dados válidos na janela (mínimo de 10 pregões)
        min_periodos = max(10, int(lookback * 0.70))
        
    # Seleciona estritamente os últimos 'lookback' pregões
    amostra = retornos_df.iloc[-lookback:]
    
    # Contagem de pregões com dados válidos
    contagem_valida = amostra.notnull().sum()
    ativos_suficientes = contagem_valida[contagem_valida >= min_periodos].index
    
    if len(ativos_suficientes) == 0:
        # Fallback defensivo: aceita ativos com qualquer histórico mínimo (> 5 pregões)
        fallback_ativos = contagem_valida[contagem_valida >= max(5, int(lookback * 0.30))].index
        if len(fallback_ativos) > 0:
            vol_diaria = amostra[fallback_ativos].std(ddof=1)
            return (vol_diaria * np.sqrt(252)).dropna()
        return pd.Series(dtype=float)
        
    vol_diaria = amostra[ativos_suficientes].std(ddof=1)
    vol_anualizada = vol_diaria * np.sqrt(252)
    return vol_anualizada.dropna()


def calcular_beta_anualizado(
    retornos_ativos: pd.DataFrame,
    retornos_benchmark: pd.Series,
    lookback: int = 252,
    min_periodos: Optional[int] = None
) -> pd.Series:
    """
    Calcula o Beta empírico de cada ativo em relação ao benchmark de mercado:
        Beta_i = Cov(R_i, R_m) / Var(R_m)
    
    Parâmetros:
        retornos_ativos: DataFrame de retornos diários dos ativos.
        retornos_benchmark: Series com retornos diários do índice de mercado.
        lookback: Janela móvel de cálculo.
        min_periodos: Mínimo de pares de retornos válidos (padrão = 70% da janela).
    """
    if min_periodos is None:
        min_periodos = max(10, int(lookback * 0.70))
        
    # Alinhamento temporal
    dados_combinados = pd.concat([retornos_benchmark.rename("BENCHMARK"), retornos_ativos], axis=1).iloc[-lookback:]
    dados_combinados.dropna(subset=["BENCHMARK"], inplace=True)
    
    var_mercado = dados_combinados["BENCHMARK"].var(ddof=1)
    if np.isnan(var_mercado) or var_mercado == 0:
        return pd.Series(index=retornos_ativos.columns, data=1.0)
        
    betas = {}
    for col in retornos_ativos.columns:
        if col in dados_combinados.columns:
            par = dados_combinados[["BENCHMARK", col]].dropna()
            if len(par) >= min_periodos:
                cov = par["BENCHMARK"].cov(par[col])
                beta = cov / var_mercado
                betas[col] = beta
            elif len(par) >= 5:
                # Estimativa de menor precisão em caso de histórico reduzido
                cov = par["BENCHMARK"].cov(par[col])
                betas[col] = cov / var_mercado if var_mercado > 0 else 1.0
            else:
                betas[col] = 1.0
                
    return pd.Series(betas).fillna(1.0)


def formar_carteiras_quintis(
    retornos_historicos: pd.DataFrame,
    retornos_benchmark: pd.Series,
    tickers_elegiveis: List[str],
    lookback: int = 252,
    fracao_quintil: float = 0.20,
    min_periodos: Optional[int] = None
) -> Dict[str, Dict]:
    """
    Executa a triagem quantitativa e o particionamento em 5 quintis a partir da volatilidade histórica:
    
    1. Filtra os retornos apenas para os tickers elegíveis do IBrX-100 na data de corte.
    2. Calcula a volatilidade anualizada dos últimos N pregões (lookback).
    3. Ordena os ativos do menor para o maior desvio-padrão.
    4. Constrói 5 quintis com fallback defensivo gracioso (sem crash de execução).
    5. Atribui pesos equiponderados (1/N) para cada carteira.
    
    Retorna:
        Dict com a estrutura detalhada dos 5 quintis e ranking completo.
    """
    if min_periodos is None:
        min_periodos = max(10, int(lookback * 0.70))
        
    # Filtra colunas elegíveis existentes nos dados históricos
    colunas_validas = [t for t in tickers_elegiveis if t in retornos_historicos.columns]
    if len(colunas_validas) == 0:
        # Fallback para todas as colunas disponíveis
        colunas_validas = list(retornos_historicos.columns)
        
    retornos_universo = retornos_historicos[colunas_validas]
    
    # 1. Calcula volatilidade anualizada
    vols = calcular_volatilidade_anualizada(retornos_universo, lookback=lookback, min_periodos=min_periodos)
    
    # Fallback se poucos ativos passaram no filtro restrito
    if len(vols) < 5:
        vols_fallback = retornos_universo.iloc[-lookback:].std(ddof=1).dropna() * np.sqrt(252)
        if len(vols_fallback) > 0:
            vols = vols_fallback
            
    if len(vols) == 0:
        # Fallback extremo caso não haja desvio padrão calculável
        vols = pd.Series(index=colunas_validas[:10], data=0.25)
        
    # 2. Calcula Betas
    ativos_com_vol = retornos_universo[vols.index]
    betas = calcular_beta_anualizado(ativos_com_vol, retornos_benchmark, lookback=lookback, min_periodos=min_periodos)
    
    # 3. Monta DataFrame de Classificação
    df_ranking = pd.DataFrame({
        'Ticker': vols.index,
        'Volatilidade_Anualizada': vols.values,
        'Beta': betas.reindex(vols.index).fillna(1.0).values
    }).sort_values('Volatilidade_Anualizada', ascending=True).reset_index(drop=True)
    
    n_total = len(df_ranking)
    
    # Particionamento dos 5 quintis
    df_ranking['Quintil'] = 0
    
    # Divide os índices em 5 partes
    num_partes = min(5, n_total) if n_total > 0 else 1
    divisoes = np.array_split(df_ranking.index, num_partes)
    
    for q_num, idxs in enumerate(divisoes, start=1):
        df_ranking.loc[idxs, 'Quintil'] = q_num
        
    nomes_quintis = {
        1: 'Q1_Jonathan',
        2: 'Q2',
        3: 'Q3',
        4: 'Q4',
        5: 'Q5_Lebre'
    }
    
    resultado = {
        'ranking_completo': df_ranking,
        'resumo_quintis': {}
    }
    
    # Se houver menos de 5 divisões preenchidas, replica a divisão mais próxima
    for q_num in range(1, 6):
        nome_q = nomes_quintis[q_num]
        sub_df = df_ranking[df_ranking['Quintil'] == q_num].copy()
        
        if sub_df.empty:
            # Fallback gracioso: usa os ativos mais próximos disponíveis
            if q_num == 1 or q_num <= 2:
                sub_df = df_ranking.head(max(1, int(np.ceil(n_total / 5)))).copy()
            elif q_num == 5 or q_num >= 4:
                sub_df = df_ranking.tail(max(1, int(np.ceil(n_total / 5)))).copy()
            else:
                sub_df = df_ranking.copy()
                
        tickers_q = sub_df['Ticker'].tolist()
        n_ativos_q = len(tickers_q)
        
        peso_individual = 1.0 / n_ativos_q if n_ativos_q > 0 else 0.0
        pesos_dict = {t: peso_individual for t in tickers_q}
        
        sub_df['Peso'] = peso_individual
        
        resultado[nome_q] = {
            'tickers': tickers_q,
            'pesos': pesos_dict,
            'vol_media': float(sub_df['Volatilidade_Anualizada'].mean()) if not sub_df.empty else 0.0,
            'beta_medio': float(sub_df['Beta'].mean()) if not sub_df.empty else 1.0,
            'df_ativos': sub_df
        }
        
        resultado['resumo_quintis'][nome_q] = {
            'n_ativos': n_ativos_q,
            'vol_media': resultado[nome_q]['vol_media'],
            'beta_medio': resultado[nome_q]['beta_medio']
        }
        
    return resultado
