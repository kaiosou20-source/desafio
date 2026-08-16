"""
===============================================================================
MÓDULO DE ESTRATÉGIA QUANTITATIVA (estrategia.py)
Projeto: Desafio Quant AI 2026 - Tese 2 (Anomalia de Baixa Volatilidade)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================
Este módulo implementa a lógica quantitativa da estratégia Low Volatility / BAB:
1. Cálculo do Desvio-Padrão Anualizado (Volatilidade histórica móvel de 252 pregões).
2. Cálculo do Beta estatístico em relação ao Benchmark de mercado (^BVSP).
3. Filtro de Liquidez e Suficiência Amostral (mínimo de 80% de pregões válidos).
4. Ordenação e Particionamento do Universo em 5 Quintis (Q1 a Q5).
5. Construção das Carteiras Equiponderadas (Long-Only):
   - 🐢 Quintil 1: Carteira Jonathan (Low Vol - 20% menos voláteis).
   - 🐇 Quintil 5: Carteira Lebre (High Vol - 20% mais voláteis).
   - Quintis intermediários (Q2, Q3, Q4) para análise de monotonicidade.
===============================================================================
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional


def calcular_volatilidade_anualizada(
    retornos_df: pd.DataFrame,
    lookback: int = 252,
    min_periodos: int = 180
) -> pd.Series:
    """
    Calcula a volatilidade histórica anualizada (desvio-padrão amostral dos retornos diários):
        sigma = std(R_diario) * sqrt(252)
    
    Parâmetros:
        retornos_df: DataFrame com os retornos diários de cada ativo.
        lookback: Quantidade de pregões da janela histórica (padrão = 252 dias úteis).
        min_periodos: Quantidade mínima de dados válidos para aceitar o ativo (evita ruído).
    
    Retorno:
        pd.Series com a volatilidade anualizada de cada ativo elegível.
    """
    # Seleciona estritamente os últimos 'lookback' pregões
    amostra = retornos_df.iloc[-lookback:]
    
    # Contagem de pregões com dados válidos
    contagem_valida = amostra.notnull().sum()
    ativos_suficientes = contagem_valida[contagem_valida >= min_periodos].index
    
    if len(ativos_suficientes) == 0:
        return pd.Series(dtype=float)
        
    vol_diaria = amostra[ativos_suficientes].std(ddof=1)
    vol_anualizada = vol_diaria * np.sqrt(252)
    return vol_anualizada.dropna()


def calcular_beta_anualizado(
    retornos_ativos: pd.DataFrame,
    retornos_benchmark: pd.Series,
    lookback: int = 252,
    min_periodos: int = 180
) -> pd.Series:
    """
    Calcula o Beta empírico de cada ativo em relação ao benchmark de mercado:
        Beta_i = Cov(R_i, R_m) / Var(R_m)
    
    Parâmetros:
        retornos_ativos: DataFrame de retornos diários dos ativos.
        retornos_benchmark: Series com retornos diários do índice de mercado.
        lookback: Janela móvel de cálculo (252 pregões).
        min_periodos: Mínimo de pares de retornos válidos.
    """
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
            else:
                betas[col] = np.nan
                
    return pd.Series(betas).dropna()


def formar_carteiras_quintis(
    retornos_historicos: pd.DataFrame,
    retornos_benchmark: pd.Series,
    tickers_elegiveis: List[str],
    lookback: int = 252,
    fracao_quintil: float = 0.20,
    min_periodos: int = 180
) -> Dict[str, Dict]:
    """
    Executa a triagem quantitativa e o particionamento em 5 quintis a partir da volatilidade histórica:
    
    1. Filtra os retornos apenas para os tickers elegíveis do IBrX-100 na data de corte.
    2. Calcula a volatilidade anualizada dos últimos 252 pregões.
    3. Ordena os ativos do menor para o maior desvio-padrão.
    4. Constrói 5 quintis (Q1 = Low Vol / Jonathan 🐢 até Q5 = High Vol / Lebre 🐇).
    5. Atribui pesos equiponderados (1/N) para cada carteira (Long-Only).
    
    Retorna:
        Dict com a estrutura:
        {
            'Q1_Jonathan': {'tickers': [...], 'pesos': {...}, 'vol_media': float, 'beta_medio': float, 'df_ativos': pd.DataFrame},
            'Q2': {...},
            'Q3': {...},
            'Q4': {...},
            'Q5_Lebre': {...},
            'ranking_completo': pd.DataFrame
        }
    """
    # Filtra colunas elegíveis existentes nos dados históricos
    colunas_validas = [t for t in tickers_elegiveis if t in retornos_historicos.columns]
    if len(colunas_validas) < 10:
        raise ValueError(f"❌ Quantidade insuficiente de ativos elegíveis com cotações ({len(colunas_validas)}). Mínimo esperado: 10.")
        
    retornos_universo = retornos_historicos[colunas_validas]
    
    # 1. Calcula volatilidade anualizada
    vols = calcular_volatilidade_anualizada(retornos_universo, lookback=lookback, min_periodos=min_periodos)
    if len(vols) < 10:
        raise ValueError(f"❌ Apenas {len(vols)} ativos possuem histórico suficiente de {lookback} pregões. Impossível formar quintis com segurança.")
        
    # 2. Calcula Betas
    betas = calcular_beta_anualizado(retornos_universo[vols.index], retornos_benchmark, lookback=lookback, min_periodos=min_periodos)
    
    # 3. Monta DataFrame de Classificação
    df_ranking = pd.DataFrame({
        'Ticker': vols.index,
        'Volatilidade_Anualizada': vols.values,
        'Beta': betas.reindex(vols.index).values
    }).sort_values('Volatilidade_Anualizada', ascending=True).reset_index(drop=True)
    
    n_total = len(df_ranking)
    # Define a divisão dos 5 quintis (20% por padrão)
    tamanho_quintil = int(np.ceil(n_total * fracao_quintil))
    
    # Atribuição dos quintis
    df_ranking['Quintil'] = 0
    # Q1: Menor volatilidade
    q1_idx = df_ranking.index[:tamanho_quintil]
    # Q5: Maior volatilidade
    q5_idx = df_ranking.index[-tamanho_quintil:]
    
    # Particionamento dos 5 quintis para análise completa de monotonicidade
    divisoes = np.array_split(df_ranking.index, 5)
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
    
    for q_num in range(1, 6):
        nome_q = nomes_quintis[q_num]
        sub_df = df_ranking[df_ranking['Quintil'] == q_num].copy()
        tickers_q = sub_df['Ticker'].tolist()
        n_ativos_q = len(tickers_q)
        
        # Pesos equiponderados (1/N)
        peso_individual = 1.0 / n_ativos_q if n_ativos_q > 0 else 0.0
        pesos_dict = {t: peso_individual for t in tickers_q}
        sub_df['Peso'] = peso_individual
        
        resultado[nome_q] = {
            'tickers': tickers_q,
            'pesos': pesos_dict,
            'n_ativos': n_ativos_q,
            'vol_media': sub_df['Volatilidade_Anualizada'].mean(),
            'beta_medio': sub_df['Beta'].mean(),
            'df_ativos': sub_df
        }
        
        resultado['resumo_quintis'][nome_q] = {
            'n_ativos': n_ativos_q,
            'vol_media': sub_df['Volatilidade_Anualizada'].mean(),
            'beta_medio': sub_df['Beta'].mean()
        }
        
    return resultado
