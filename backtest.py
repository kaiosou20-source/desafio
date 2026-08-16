"""
===============================================================================
MÓDULO DE MOTOR DE BACKTEST QUANTITATIVO (backtest.py)
Projeto: Desafio Quant AI 2026 - Tese 2 (Anomalia de Baixa Volatilidade)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================
Este módulo implementa o motor de simulação temporal estrita e cálculo de métricas:
1. Rebalanceamento sistemático periódico (Trimestral) sem viés de antecipação (look-ahead).
2. Dedução realista de custos de transação/giro com base no Turnover.
3. Rastreamento simultâneo das curvas de capital:
   - 🐢 Jonathan (Q1 - Low Vol)
   - 🐇 A Lebre (Q5 - High Vol)
   - Quintis Intermediários (Q2, Q3, Q4)
   - 📊 Benchmark de Mercado (Ibovespa / IBrX)
   - 💵 Taxa Livre de Risco (CDI diário BCB)
4. Cálculo abrangente de KPIs de Performance e Risco:
   - Retorno Total, CAGR, Volatilidade Anualizada, Sharpe (vs CDI e vs 0),
   - Sortino, Calmar, Max Drawdown, Tempo de Recuperação, Beta, Alpha de Jensen,
   - Turnover médio e Win Rate.
===============================================================================
"""

import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, date

from dados import (
    carregar_composicao_ibrx,
    obter_universo_valido,
    baixar_cdi_bcb,
    baixar_cotacoes_ativos,
    baixar_benchmark,
    calcular_retornos_diarios,
    obter_datas_rebalanceamento
)
from estrategia import formar_carteiras_quintis


def executar_backtest(

    data_inicio: Union[str, datetime, date, pd.Timestamp] = "2018-01-01",
    data_fim: Union[str, datetime, date, pd.Timestamp] = "2026-08-01",
    lookback_dias: int = 252,
    frequencia_rebalanceamento: str = "trimestral",
    fracao_quintil: float = 0.20,
    custo_transacao_bps: float = 5.0,
    modo_estrategia: str = "long_only",
    caminho_composicao: Optional[str] = None
) -> Dict:
    """
    Executa a simulação temporal quantitativa ponta a ponta da estratégia.
    
    Parâmetros:
        data_inicio: Data inicial da simulação (YYYY-MM-DD ou datetime/date).
        data_fim: Data final da simulação (YYYY-MM-DD ou datetime/date).
        lookback_dias: Janela móvel de cálculo de volatilidade (126 = 6 meses, 252 = 12 meses).
        frequencia_rebalanceamento: 'trimestral', 'mensal', 'semestral' ou 'anual'.
        fracao_quintil: Proporção de cada quintil (0.20 = 20%).
        custo_transacao_bps: Custo de corretagem/slippage em bps (5 bps = 0.05% por giro).
        modo_estrategia: 'long_only' (apenas Q1 Low Vol) ou 'long_short' (Long Q1 Low Vol / Short Q5 High Vol + CDI).
        caminho_composicao: Caminho para o CSV de composição histórica do IBrX-100.
        
    Retorna:
        Dict com curvas de capital, retornos diários, métricas comparativas e histórico de rebalanceamentos.
    """
    # 0. Normalização e Validação Robusta de Parâmetros
    if hasattr(data_inicio, 'strftime'):
        d_ini_str = data_inicio.strftime("%Y-%m-%d")
    else:
        d_ini_str = str(data_inicio).strip()

    if hasattr(data_fim, 'strftime'):
        d_fim_str = data_fim.strftime("%Y-%m-%d")
    else:
        d_fim_str = str(data_fim).strip()

    lk_int = int(lookback_dias)
    freq_str = str(frequencia_rebalanceamento).strip().lower()
    frac_float = float(fracao_quintil)
    custo_float = float(custo_transacao_bps)
    modo_str = str(modo_estrategia).strip().lower()

    modo_label = "Long-Short (Q1 Long / Q5 Short + CDI)" if modo_str == "long_short" else "Long-Only (Q1 Low Vol)"
    print("=" * 80)
    print(f"🐢 MOTOR DE BACKTEST QUANTITATIVO: JONATHAN ({modo_label})")
    print(f"   Período: {d_ini_str} até {d_fim_str} | Lookback: {lk_int} pregões")
    print(f"   Rebalanceamento: {freq_str.capitalize()} | Custos: {custo_float} bps")
    print("=" * 80)

    # 1. Carrega Universo Histórico
    df_composicao = carregar_composicao_ibrx(caminho_composicao)
    todos_tickers = df_composicao['ticker'].unique().tolist()
    
    # Para garantir lookback suficiente no primeiro rebalanceamento, baixamos dados com antecedência
    dt_inicio_coleta = (pd.to_datetime(d_ini_str) - pd.Timedelta(days=lk_int * 2)).strftime("%Y-%m-%d")
    
    # 2. Ingestão de Cotações, Benchmark e CDI
    precos_ativos = baixar_cotacoes_ativos(todos_tickers, data_inicio=dt_inicio_coleta, data_fim=d_fim_str)
    serie_bench_precos = baixar_benchmark(ticker="^BVSP", data_inicio=dt_inicio_coleta, data_fim=d_fim_str)
    serie_cdi_diario = baixar_cdi_bcb(data_inicio=dt_inicio_coleta, data_fim=d_fim_str)
    
    # 3. Calcula Retornos Diários
    retornos_ativos = calcular_retornos_diarios(precos_ativos)
    retornos_bench = calcular_retornos_diarios(serie_bench_precos.to_frame()).iloc[:, 0].rename("Benchmark")
    
    # Alinha datas de negociação
    datas_comuns = retornos_ativos.index.intersection(retornos_bench.index).sort_values()
    retornos_ativos = retornos_ativos.loc[datas_comuns]
    retornos_bench = retornos_bench.loc[datas_comuns]
    serie_cdi_diario = serie_cdi_diario.reindex(datas_comuns).fillna(0.0)
    
    # 4. Determina as Datas de Rebalanceamento
    datas_reb_todas = obter_datas_rebalanceamento(datas_comuns, frequencia=freq_str)
    
    # Filtra as datas de rebalanceamento que possuem lookback suficiente e ocorrem no período desejado
    dt_inicio_dt = pd.to_datetime(d_ini_str)
    datas_reb_validas = []
    for d in datas_reb_todas:
        pos = datas_comuns.get_loc(d)
        if pos >= lk_int and d >= dt_inicio_dt:
            datas_reb_validas.append(d)

            
    if len(datas_reb_validas) < 2:
        # Se a primeira data de rebalanceamento for posterior, inclui a data inicial com lookback disponível
        for d in datas_reb_todas:
            pos = datas_comuns.get_loc(d)
            if pos >= lookback_dias:
                datas_reb_validas.append(d)
                if len(datas_reb_validas) >= 2 and d >= dt_inicio_dt:
                    break
        datas_reb_validas = sorted(list(set(datas_reb_validas)))
        
    print(f"📅 Total de rebalanceamentos programados: {len(datas_reb_validas)}")
    
    # 5. Estruturas para simulação diária
    nomes_estrategias = ['Q1_Jonathan', 'Q2', 'Q3', 'Q4', 'Q5_Lebre']
    
    # DataFrame para registrar retornos diários de cada estratégia
    data_primeiro_reb = datas_reb_validas[0]
    datas_simulacao = datas_comuns[datas_comuns >= data_primeiro_reb]
    
    df_retornos_sim = pd.DataFrame(index=datas_simulacao, columns=nomes_estrategias + ['Benchmark', 'CDI'], dtype=float)
    df_retornos_sim['Benchmark'] = retornos_bench.loc[datas_simulacao]
    df_retornos_sim['CDI'] = serie_cdi_diario.loc[datas_simulacao]
    
    historico_rebalanceamentos = []
    pesos_anteriores = {nome: {} for nome in nomes_estrategias}
    
    # Custo em formato decimal: 5 bps = 5 / 10000 = 0.0005
    taxa_custo_decimal = (custo_transacao_bps / 10000.0)
    
    # 6. Loop de Rebalanceamentos Pontuais (Point-in-Time)
    for i in range(len(datas_reb_validas)):
        d_reb = datas_reb_validas[i]
        d_prox = datas_reb_validas[i + 1] if i + 1 < len(datas_reb_validas) else datas_simulacao[-1]
        
        # Universo de ativos elegíveis do IBrX na data de corte
        tickers_elegiveis = obter_universo_valido(d_reb, df_composicao)
        
        # Filtra estritamente a janela histórica até o dia de rebalanceamento d_reb
        pos_reb = datas_comuns.get_loc(d_reb)
        idx_lookback = datas_comuns[pos_reb - lookback_dias + 1 : pos_reb + 1]
        
        retornos_janela = retornos_ativos.loc[idx_lookback]
        bench_janela = retornos_bench.loc[idx_lookback]
        
        # Forma os quintis
        carteiras_quintis = formar_carteiras_quintis(
            retornos_historicos=retornos_janela,
            retornos_benchmark=bench_janela,
            tickers_elegiveis=tickers_elegiveis,
            lookback=lookback_dias,
            fracao_quintil=fracao_quintil
        )
        
        # Período de sustentação da carteira: do dia seguinte a d_reb até d_prox
        idx_periodo = datas_simulacao[(datas_simulacao > d_reb) & (datas_simulacao <= d_prox)]
        if len(idx_periodo) == 0 and d_reb == datas_simulacao[-1]:
            continue
            
        registro_reb = {
            'data_rebalanceamento': d_reb,
            'proximo_rebalanceamento': d_prox,
            'n_dias_periodo': len(idx_periodo),
            'detalhes_quintis': {}
        }
        
        for nome in nomes_estrategias:
            info_q = carteiras_quintis[nome]
            pesos_novos = info_q['pesos']
            tickers_q = info_q['tickers']
            
            # Cálculo do Turnover e Custos de Transação
            todos_tickers_giro = set(list(pesos_anteriores[nome].keys()) + list(pesos_novos.keys()))
            turnover = 0.5 * sum([
                abs(pesos_novos.get(t, 0.0) - pesos_anteriores[nome].get(t, 0.0))
                for t in todos_tickers_giro
            ])
            custo_giro = turnover * taxa_custo_decimal
            
            pesos_anteriores[nome] = pesos_novos
            
            registro_reb['detalhes_quintis'][nome] = {
                'tickers': tickers_q,
                'vol_media_ex_ante': info_q['vol_media'],
                'beta_medio_ex_ante': info_q['beta_medio'],
                'turnover': turnover,
                'custo_transacao': custo_giro,
                'df_ativos': info_q['df_ativos']
            }
            
            if len(idx_periodo) > 0:
                # Retornos diários equiponderados da carteira no período
                sub_retornos = retornos_ativos.loc[idx_periodo, tickers_q].copy().fillna(0.0)
                ret_diario_carteira = sub_retornos.mean(axis=1)
                
                # Desconta o custo de transação no primeiro pregão útil do novo ciclo
                primeiro_dia = idx_periodo[0]
                ret_diario_carteira.loc[primeiro_dia] -= custo_giro
                
                df_retornos_sim.loc[idx_periodo, nome] = ret_diario_carteira
                
        historico_rebalanceamentos.append(registro_reb)

    # 7. Limpeza e Construção das Curvas de Capital (Base 100)
    df_retornos_validos = df_retornos_sim.dropna(subset=['Q1_Jonathan', 'Q5_Lebre']).copy()
    
    # Define a série de retorno da estratégia ativa
    if modo_estrategia == "long_short":
        # Long Q1 (Low Vol) / Short Q5 (High Vol) + Colateral remunerado a CDI
        df_retornos_validos['Estrategia_Ativa'] = (
            df_retornos_validos['Q1_Jonathan'] - df_retornos_validos['Q5_Lebre']
        ) + df_retornos_validos['CDI']
    else:
        # Long-Only (Q1 Low Vol)
        df_retornos_validos['Estrategia_Ativa'] = df_retornos_validos['Q1_Jonathan']
        
    df_curvas_capital = pd.DataFrame(index=df_retornos_validos.index)
    for col in df_retornos_validos.columns:
        df_curvas_capital[col] = 100.0 * (1.0 + df_retornos_validos[col]).cumprod()
        
    # 8. Cálculo Completo de Métricas de Performance e Risco
    tabela_metricas = calcular_quadro_metricas(df_retornos_validos, df_curvas_capital, modo_estrategia=modo_estrategia)
    
    # 9. Quadro Comparativo Resumido (Estratégia vs. IBrX-100 vs. CDI)
    tabela_comparativa_resumida = obter_quadro_comparativo_resumido(tabela_metricas, modo_estrategia=modo_estrategia)
    
    # 10. Retornos Mensais e Anuais para o Heatmap
    tabela_mensal_estrategia = gerar_tabela_retornos_mensais(df_retornos_validos['Estrategia_Ativa'])

    resultado_final = {
        'curvas_capital': df_curvas_capital,
        'retornos_diarios': df_retornos_validos,
        'metricas': tabela_metricas,
        'metricas_comparativas': tabela_comparativa_resumida,
        'retornos_mensais_jonathan': tabela_mensal_estrategia,
        'historico_rebalanceamentos': historico_rebalanceamentos,
        'ultimo_rebalanceamento': historico_rebalanceamentos[-1] if historico_rebalanceamentos else None,
        'parametros': {
            'data_inicio': str(df_retornos_validos.index.min().date()),
            'data_fim': str(df_retornos_validos.index.max().date()),
            'lookback_dias': lookback_dias,
            'frequencia': frequencia_rebalanceamento,
            'fracao_quintil': fracao_quintil,
            'custo_bps': custo_transacao_bps,
            'modo_estrategia': modo_estrategia
        }
    }
    
    return resultado_final


def obter_quadro_comparativo_resumido(df_metricas: pd.DataFrame, modo_estrategia: str = "long_only") -> pd.DataFrame:
    """
    Retorna o quadro comparativo executivo de 6 métricas essenciais:
    (Estratégia vs. IBrX-100 / Ibovespa vs. CDI)
    - Retorno Total (%)
    - Retorno Anualizado (CAGR)
    - Volatilidade Anualizada
    - Índice de Sharpe (vs. CDI)
    - Alpha Anualizado (%)
    - Maximum Drawdown (MDD %)
    """
    nome_est = "🐢 Estratégia (Long-Short Low/High Vol)" if modo_estrategia == "long_short" else "🐢 Estratégia (Low Vol Long-Only)"
    
    mapa_linhas = {
        'Estrategia_Ativa': nome_est,
        'Benchmark': '📊 IBrX-100 / Ibovespa',
        'CDI': '💵 CDI (Taxa Livre de Risco)'
    }
    
    cols_desejadas = [
        'Retorno Total (%)',
        'CAGR (% a.a.)',
        'Volatilidade (% a.a.)',
        'Índice Sharpe (vs CDI)',
        'Alpha Anualizado (%)',
        'Max Drawdown (%)'
    ]
    
    linhas = []
    nomes_index = []
    
    for chave_orig, nome_exib in mapa_linhas.items():
        if chave_orig in df_metricas.index:
            row = df_metricas.loc[chave_orig, cols_desejadas].copy()
            linhas.append(row)
            nomes_index.append(nome_exib)
            
    df_res = pd.DataFrame(linhas, index=nomes_index)
    df_res.columns = [
        'Retorno Total',
        'Retorno Anualizado (CAGR)',
        'Volatilidade Anualizada',
        'Índice de Sharpe',
        'Alpha Anualizado',
        'Maximum Drawdown (MDD)'
    ]
    return df_res



def calcular_quadro_metricas(
    df_retornos: pd.DataFrame,
    df_curvas: pd.DataFrame,
    modo_estrategia: str = "long_only"
) -> pd.DataFrame:
    """
    Computa um quadro rigoroso e completo de métricas quantitativas de desempenho e risco.
    """
    n_pregoes = len(df_retornos)
    anos = n_pregoes / 252.0
    
    ret_cdi_diario = df_retornos['CDI']
    ret_cdi_acum = (1.0 + ret_cdi_diario).prod() - 1.0
    cagr_cdi = (1.0 + ret_cdi_acum) ** (1.0 / anos) - 1.0 if anos > 0 else 0.0
    
    ret_bench_diario = df_retornos['Benchmark']
    ret_bench_acum = (1.0 + ret_bench_diario).prod() - 1.0
    cagr_bench = (1.0 + ret_bench_acum) ** (1.0 / anos) - 1.0 if anos > 0 else 0.0
    var_bench = ret_bench_diario.var(ddof=1)
    
    metricas = {}
    
    for col in df_retornos.columns:
        serie_ret = df_retornos[col]
        serie_curva = df_curvas[col]
        
        # 1. Retorno Total Acumulado (%)
        ret_acum = (serie_curva.iloc[-1] / serie_curva.iloc[0] - 1.0) * 100.0
        
        # 2. CAGR (% a.a.)
        cagr = ((serie_curva.iloc[-1] / serie_curva.iloc[0]) ** (1.0 / anos) - 1.0) * 100.0 if anos > 0 else 0.0
        
        # 3. Volatilidade Anualizada (% a.a.)
        vol_anual = serie_ret.std(ddof=1) * np.sqrt(252) * 100.0
        
        # 4. Drawdowns e Max Drawdown
        picos = serie_curva.cummax()
        drawdowns = (serie_curva - picos) / picos
        max_drawdown = drawdowns.min() * 100.0
        
        # Duração máxima do Drawdown em pregões
        em_drawdown = drawdowns < 0
        duracao_atual = 0
        max_duracao_dd = 0
        for is_dd in em_drawdown:
            if is_dd:
                duracao_atual += 1
                if duracao_atual > max_duracao_dd:
                    max_duracao_dd = duracao_atual
            else:
                duracao_atual = 0
                
        # 5. Índice de Sharpe (vs. CDI)
        cagr_dec = cagr / 100.0
        vol_dec = vol_anual / 100.0
        sharpe_cdi = (cagr_dec - cagr_cdi) / vol_dec if vol_dec > 0 else 0.0
        
        # 6. Índice de Sharpe Absoluto (vs. 0)
        sharpe_zero = cagr_dec / vol_dec if vol_dec > 0 else 0.0
        
        # 7. Índice de Sortino (vs. CDI)
        excesso_cdi = serie_ret - ret_cdi_diario
        downside_ret = excesso_cdi[excesso_cdi < 0]
        downside_std = np.sqrt((downside_ret ** 2).mean()) * np.sqrt(252) if len(downside_ret) > 0 else 0.0
        sortino = (cagr_dec - cagr_cdi) / downside_std if downside_std > 0 else 0.0
        
        # 8. Índice de Calmar (CAGR / |Max Drawdown|)
        calmar = cagr_dec / (abs(max_drawdown) / 100.0) if max_drawdown < 0 else np.nan
        
        # 9. Beta vs. Benchmark
        cov_bench = serie_ret.cov(ret_bench_diario)
        beta = cov_bench / var_bench if var_bench > 0 else 1.0
        
        # 10. Alpha de Jensen Anualizado (%)
        # Alpha = (CAGR_p - CAGR_cdi) - Beta * (CAGR_bench - CAGR_cdi)
        alpha_jensen = ((cagr_dec - cagr_cdi) - beta * (cagr_bench - cagr_cdi)) * 100.0
        
        # 11. Win Rate vs. Benchmark (por trimestre móvel de 63 pregões)
        janela_trim = 63
        if len(serie_ret) >= janela_trim:
            roll_strat = serie_curva.pct_change(janela_trim).dropna()
            roll_bench = df_curvas['Benchmark'].pct_change(janela_trim).dropna()
            idx_roll = roll_strat.index.intersection(roll_bench.index)
            win_rate = (roll_strat.loc[idx_roll] > roll_bench.loc[idx_roll]).mean() * 100.0
        else:
            win_rate = 50.0

        metricas[col] = {
            'Retorno Total (%)': ret_acum,
            'CAGR (% a.a.)': cagr,
            'Volatilidade (% a.a.)': vol_anual,
            'Índice Sharpe (vs CDI)': sharpe_cdi,
            'Índice Sortino': sortino,
            'Índice Calmar': calmar,
            'Max Drawdown (%)': max_drawdown,
            'Max Duração DD (dias)': int(max_duracao_dd),
            'Beta (vs Ibov)': beta,
            'Alpha Anualizado (%)': alpha_jensen,
            'Win Rate Trimestral (%)': win_rate
        }
        
    df_metricas = pd.DataFrame(metricas).T
    return df_metricas



def gerar_tabela_retornos_mensais(retornos_diarios_serie: pd.Series) -> pd.DataFrame:
    """
    Gera tabela de retornos percentuais organizados por Ano e Mês (para mapa de calor).
    """
    df_mensal = retornos_diarios_serie.resample('ME').apply(lambda r: (1.0 + r).prod() - 1.0) * 100.0
    
    tabela = pd.DataFrame({
        'Ano': df_mensal.index.year,
        'Mes': df_mensal.index.month,
        'Retorno': df_mensal.values
    })
    
    pivot = tabela.pivot(index='Ano', columns='Mes', values='Retorno')
    meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    pivot.columns = [meses_nomes[m - 1] for m in pivot.columns]
    
    # Adiciona coluna com Retorno Anual Acumulado
    retornos_anuais = retornos_diarios_serie.resample('YE').apply(lambda r: (1.0 + r).prod() - 1.0) * 100.0
    retornos_anuais.index = retornos_anuais.index.year
    pivot['Ano Total'] = retornos_anuais.reindex(pivot.index)
    
    return pivot.round(2)
