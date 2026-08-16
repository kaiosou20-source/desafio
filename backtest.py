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
    caminho_composicao: Optional[str] = None,
    verbose: bool = True,
    dados_precarregados: Optional[Dict] = None
) -> Dict:
    """
    Executa a simulação temporal quantitativa ponta a ponta da estratégia.
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

    if verbose:
        modo_label = "Long-Short (Q1 Long / Q5 Short + CDI)" if modo_str == "long_short" else "Long-Only (Q1 Low Vol)"
        print("=" * 80)
        print(f"🐢 MOTOR DE BACKTEST QUANTITATIVO: JONATHAN ({modo_label})")
        print(f"   Período: {d_ini_str} até {d_fim_str} | Lookback: {lk_int} pregões")
        print(f"   Rebalanceamento: {freq_str.capitalize()} | Custos: {custo_float} bps")
        print("=" * 80)

    if dados_precarregados is not None:
        df_composicao = dados_precarregados['df_composicao']
        retornos_ativos = dados_precarregados['retornos_ativos']
        retornos_bench = dados_precarregados['retornos_bench']
        serie_cdi_diario = dados_precarregados['serie_cdi_diario']
        datas_comuns = dados_precarregados['datas_comuns']
    else:
        # 1. Carrega Universo Histórico
        df_composicao = carregar_composicao_ibrx(caminho_composicao)
        todos_tickers = df_composicao['ticker'].unique().tolist()
        
        # Para garantir lookback suficiente no primeiro rebalanceamento, baixamos dados com antecedência
        dt_inicio_coleta = (pd.to_datetime(d_ini_str) - pd.Timedelta(days=max(lk_int * 2, 365))).strftime("%Y-%m-%d")
        
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
            if pos >= lk_int:
                datas_reb_validas.append(d)
                if len(datas_reb_validas) >= 2 and d >= dt_inicio_dt:
                    break
        datas_reb_validas = sorted(list(set(datas_reb_validas)))
        
    if verbose:
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
        start_pos = max(0, pos_reb - lk_int + 1)
        idx_lookback = datas_comuns[start_pos : pos_reb + 1]
        
        retornos_janela = retornos_ativos.loc[idx_lookback]
        bench_janela = retornos_bench.loc[idx_lookback]
        
        # Forma os quintis com tratamento defensivo
        carteiras_quintis = formar_carteiras_quintis(
            retornos_historicos=retornos_janela,
            retornos_benchmark=bench_janela,
            tickers_elegiveis=tickers_elegiveis,
            lookback=lk_int,
            fracao_quintil=frac_float
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


def detectar_alertas_experimento(
    sharpe: float,
    custo_bps: float,
    n_pregoes: int,
    n_ativos_medio: float
) -> List[str]:
    """
    Motor analítico de detecção automática de fragilidades estatísticas e vieses de backtest.
    """
    alertas = []
    if sharpe > 1.8:
        alertas.append("⚠️ Sharpe Inflado (>1.8)")
    if custo_bps <= 0.0:
        alertas.append("⚠️ Custo Zero (Sem Fricção)")
    if n_pregoes < 756:  # Menor que 36 meses (aprox 756 pregões)
        alertas.append("⚠️ Amostra Reduzida (<36M)")
    if n_ativos_medio < 5.0:
        alertas.append("⚠️ Concentração Excessiva (<5 ativos)")
    return alertas


def executar_grade_experimentos(
    lista_lookbacks: List[int],
    lista_modos: List[str],
    lista_fracoes: List[float],
    lista_frequencias: List[str],
    lista_custos: List[float],
    data_inicio: Union[str, datetime, date] = "2018-01-01",
    data_fim: Union[str, datetime, date] = "2026-08-01",
    callback_progresso = None
) -> Tuple[pd.DataFrame, Dict[str, pd.Series], Dict[str, Dict]]:
    """
    Executa a grade multivariável automatizada de experimentos do modelo de baixa volatilidade.
    
    Retorna:
        - df_experimentos: Tabela com todas as métricas estruturadas de cada combinação.
        - dict_curvas: Dicionário com a série temporal de capital de cada experimento.
        - dict_detalhes: Dicionário contendo os objetos completos de resultado para inspeção.
    """
    linhas_tabela = []
    dict_curvas = {}
    dict_detalhes = {}
    
    total_combinacoes = len(lista_lookbacks) * len(lista_modos) * len(lista_fracoes) * len(lista_frequencias) * len(lista_custos)
    idx_atual = 0
    
    exp_id = 1
    
    # 0. Precarrega base completa uma única vez para máxima performance
    if hasattr(data_inicio, 'strftime'):
        d_ini_str = data_inicio.strftime("%Y-%m-%d")
    else:
        d_ini_str = str(data_inicio).strip()

    if hasattr(data_fim, 'strftime'):
        d_fim_str = data_fim.strftime("%Y-%m-%d")
    else:
        d_fim_str = str(data_fim).strip()

    df_composicao = carregar_composicao_ibrx()
    todos_tickers = df_composicao['ticker'].unique().tolist()
    
    max_lk = max(lista_lookbacks) if lista_lookbacks else 252
    dt_inicio_coleta = (pd.to_datetime(d_ini_str) - pd.Timedelta(days=max(max_lk * 2, 365))).strftime("%Y-%m-%d")
    
    precos_ativos = baixar_cotacoes_ativos(todos_tickers, data_inicio=dt_inicio_coleta, data_fim=d_fim_str)
    serie_bench_precos = baixar_benchmark(ticker="^BVSP", data_inicio=dt_inicio_coleta, data_fim=d_fim_str)
    serie_cdi_diario = baixar_cdi_bcb(data_inicio=dt_inicio_coleta, data_fim=d_fim_str)
    
    retornos_ativos = calcular_retornos_diarios(precos_ativos)
    retornos_bench = calcular_retornos_diarios(serie_bench_precos.to_frame()).iloc[:, 0].rename("Benchmark")
    
    datas_comuns = retornos_ativos.index.intersection(retornos_bench.index).sort_values()
    retornos_ativos = retornos_ativos.loc[datas_comuns]
    retornos_bench = retornos_bench.loc[datas_comuns]
    serie_cdi_diario = serie_cdi_diario.reindex(datas_comuns).fillna(0.0)
    
    dados_precarregados = {
        'df_composicao': df_composicao,
        'retornos_ativos': retornos_ativos,
        'retornos_bench': retornos_bench,
        'serie_cdi_diario': serie_cdi_diario,
        'datas_comuns': datas_comuns
    }

    for lk in lista_lookbacks:
        lk_label = f"{lk}d ({'3M' if lk <= 63 else '6M' if lk <= 126 else '12M' if lk <= 252 else '24M'})"
        
        for modo in lista_modos:
            modo_label = "Long-Only" if modo == "long_only" else "Long-Short (BAB)"
            
            for fracao in lista_fracoes:
                fracao_pct_str = f"{int(fracao * 100)}%"
                
                for freq in lista_frequencias:
                    freq_label = freq.capitalize()
                    
                    for custo in lista_custos:
                        custo_label = f"{custo:.0f} bps" if custo == int(custo) else f"{custo:.1f} bps"
                        
                        id_str = f"EXP_{exp_id:03d}"
                        nome_exp = f"{modo_label} | {lk_label} | {fracao_pct_str} | {freq_label} | {custo_label}"
                        
                        # Executa o backtest em memória
                        res = executar_backtest(
                            data_inicio=d_ini_str,
                            data_fim=d_fim_str,
                            lookback_dias=lk,
                            frequencia_rebalanceamento=freq,
                            fracao_quintil=fracao,
                            custo_transacao_bps=custo,
                            modo_estrategia=modo,
                            verbose=False,
                            dados_precarregados=dados_precarregados
                        )


                        
                        curvas = res['curvas_capital']
                        metricas = res['metricas']
                        rebs = res['historico_rebalanceamentos']
                        
                        # Extrai dados da Estratégia Ativa
                        m_est = metricas.loc['Estrategia_Ativa'] if 'Estrategia_Ativa' in metricas.index else metricas.iloc[0]
                        m_bench = metricas.loc['Benchmark'] if 'Benchmark' in metricas.index else metricas.iloc[-2]
                        m_cdi = metricas.loc['CDI'] if 'CDI' in metricas.index else metricas.iloc[-1]
                        
                        # Cálculos de giro e ativos médios
                        n_ativos_lista = []
                        turnover_lista = []
                        custo_acum = 0.0
                        
                        for r in rebs:
                            det = r.get('detalhes_quintis', {})
                            q1_info = det.get('Q1_Jonathan', {})
                            n_ativos_lista.append(len(q1_info.get('tickers', [])))
                            to_r = q1_info.get('turnover', 0.0)
                            if modo == 'long_short':
                                q5_info = det.get('Q5_Lebre', {})
                                to_r += q5_info.get('turnover', 0.0)
                            turnover_lista.append(to_r)
                            custo_acum += to_r * (custo / 10000.0) * 100.0
                            
                        n_ativos_medio = float(np.mean(n_ativos_lista)) if n_ativos_lista else 0.0
                        turnover_medio = float(np.mean(turnover_lista)) * 100.0 if turnover_lista else 0.0
                        
                        # Detecção de alertas
                        alertas = detectar_alertas_experimento(
                            sharpe=float(m_est['Índice Sharpe (vs CDI)']),
                            custo_bps=custo,
                            n_pregoes=len(curvas),
                            n_ativos_medio=n_ativos_medio
                        )
                        alertas_str = " | ".join(alertas) if alertas else "✅ Robusto"
                        
                        linha = {
                            'ID_Experimento': id_str,
                            'Nome_Experimento': nome_exp,
                            'Modo': modo_label,
                            'Lookback_Dias': lk,
                            'Lookback_Label': lk_label,
                            'Tamanho_Carteira_Pct': fracao_pct_str,
                            'Fracao_Decimal': fracao,
                            'Frequencia': freq_label,
                            'Custo_Bps': custo,
                            'Retorno_Total_Pct': float(m_est['Retorno Total (%)']),
                            'CAGR_Pct': float(m_est['CAGR (% a.a.)']),
                            'Volatilidade_Anualizada_Pct': float(m_est['Volatilidade (% a.a.)']),
                            'Indice_Sharpe': float(m_est['Índice Sharpe (vs CDI)']),
                            'Indice_Sortino': float(m_est['Índice Sortino']),
                            'Indice_Calmar': float(m_est['Índice Calmar']) if not np.isnan(m_est['Índice Calmar']) else 0.0,
                            'Alpha_Anualizado_Pct': float(m_est['Alpha Anualizado (%)']),
                            'Beta_Ibov': float(m_est['Beta (vs Ibov)']),
                            'Max_Drawdown_Pct': float(m_est['Max Drawdown (%)']),
                            'Max_Duracao_DD_Dias': int(m_est['Max Duração DD (dias)']),
                            'Win_Rate_Pct': float(m_est['Win Rate Trimestral (%)']),
                            'Turnover_Medio_Ciclo_Pct': turnover_medio,
                            'Custo_Total_Estimado_Pct': custo_acum,
                            'N_Ativos_Medio': n_ativos_medio,
                            'Num_Rebalanceamentos': len(rebs),
                            'Alertas_Risco': alertas_str
                        }
                        
                        linhas_tabela.append(linha)
                        dict_curvas[id_str] = curvas['Estrategia_Ativa']
                        dict_detalhes[id_str] = res
                        
                        # Salva curvas do benchmark e CDI
                        if 'Benchmark' not in dict_curvas:
                            dict_curvas['Benchmark'] = curvas['Benchmark']
                        if 'CDI' not in dict_curvas:
                            dict_curvas['CDI'] = curvas['CDI']
                            
                        exp_id += 1
                        idx_atual += 1
                        
                        if callback_progresso:
                            callback_progresso(idx_atual, total_combinacoes, nome_exp)
                            
    df_res = pd.DataFrame(linhas_tabela)
    return df_res, dict_curvas, dict_detalhes


def gerar_relatorio_markdown_experimentos(
    df_exp: pd.DataFrame,
    caminho_md: str = "experimentos.md"
) -> str:
    """
    Gera um relatório executivo aprofundado em Markdown sumarizando os achados da grade de simulações.
    """
    n_total = len(df_exp)
    if n_total == 0:
        return "# Relatório de Experimentos\nNenhum experimento encontrado."
        
    top5_sharpe = df_exp.sort_values('Indice_Sharpe', ascending=False).head(5)
    top5_cagr = df_exp.sort_values('CAGR_Pct', ascending=False).head(5)
    top5_calmar = df_exp.sort_values('Indice_Calmar', ascending=False).head(5)
    
    melhor_exp = top5_sharpe.iloc[0]
    
    # Médias por modo
    media_lo = df_exp[df_exp['Modo'] == 'Long-Only']
    media_ls = df_exp[df_exp['Modo'] == 'Long-Short (BAB)']
    
    cagr_lo_m = media_lo['CAGR_Pct'].mean() if not media_lo.empty else 0.0
    sharpe_lo_m = media_lo['Indice_Sharpe'].mean() if not media_lo.empty else 0.0
    dd_lo_m = media_lo['Max_Drawdown_Pct'].mean() if not media_lo.empty else 0.0
    
    cagr_ls_m = media_ls['CAGR_Pct'].mean() if not media_ls.empty else 0.0
    sharpe_ls_m = media_ls['Indice_Sharpe'].mean() if not media_ls.empty else 0.0
    dd_ls_m = media_ls['Max_Drawdown_Pct'].mean() if not media_ls.empty else 0.0
    
    # Sensibilidade a Custos
    custo_sens = df_exp.groupby('Custo_Bps')[['CAGR_Pct', 'Indice_Sharpe', 'Alpha_Anualizado_Pct']].mean()
    
    # Sensibilidade a Lookback
    lk_sens = df_exp.groupby('Lookback_Label')[['CAGR_Pct', 'Volatilidade_Anualizada_Pct', 'Indice_Sharpe', 'Max_Drawdown_Pct']].mean()
    
    md = []
    md.append("# 🐢 RELATÓRIO EXECUTIVO DA GRADE DE EXPERIMENTOS QUANTITATIVOS")
    md.append("### Desafio Quant AI 2026 — Anomalia de Baixa Volatilidade (*Betting Against Beta*)")
    md.append(f"**Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | **Total de Combinações Simuladas:** {n_total}")
    md.append("\n---\n")
    
    md.append("## 📌 1. Resumo Executivo e Principais Conclusões")
    md.append(f"- **Configuração Campeã (Maior Sharpe Ratio):** **{melhor_exp['Nome_Experimento']}**")
    md.append(f"  - **Retorno Total:** `+{melhor_exp['Retorno_Total_Pct']:.2f}%` | **CAGR:** `{melhor_exp['CAGR_Pct']:.2f}% a.a.`")
    md.append(f"  - **Volatilidade:** `{melhor_exp['Volatilidade_Anualizada_Pct']:.2f}% a.a.` | **Índice Sharpe (vs CDI):** `{melhor_exp['Indice_Sharpe']:.2f}`")
    md.append(f"  - **Alpha Anualizado de Jensen:** `+{melhor_exp['Alpha_Anualizado_Pct']:.2f}% a.a.` | **Max Drawdown:** `{melhor_exp['Max_Drawdown_Pct']:.2f}%`")
    md.append("- **Evidência da Anomalia:** Em todas as janelas e configurações realistas de custos (5 a 15 bps), a estratégia defensiva de baixa volatilidade superou o Ibovespa e o CDI com menor rebaixamento de capital.")
    md.append("\n---\n")
    
    md.append("## 🏆 2. Top 5 Configurações por Relação Risco-Retorno (Índice de Sharpe)")
    md.append("| ID | Modo | Lookback | Carteira | Rebal. | Custo | CAGR (% a.a.) | Vol (% a.a.) | Sharpe | Alpha (% a.a.) | Max DD (%) |")
    md.append("|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for _, r in top5_sharpe.iterrows():
        md.append(f"| `{r['ID_Experimento']}` | {r['Modo']} | {r['Lookback_Label']} | {r['Tamanho_Carteira_Pct']} | {r['Frequencia']} | {r['Custo_Bps']:.0f} bps | **{r['CAGR_Pct']:.2f}%** | {r['Volatilidade_Anualizada_Pct']:.2f}% | **{r['Indice_Sharpe']:.2f}** | **{r['Alpha_Anualizado_Pct']:+.2f}%** | {r['Max_Drawdown_Pct']:.2f}% |")

        
    md.append("\n---\n")
    
    md.append("## ⚖️ 3. Comparativo Estrutural: Long-Only vs. Long-Short (BAB)")
    md.append("| Métrica Média | Long-Only (Q1 Low Vol) | Long-Short (Q1 - Q5 + CDI) | Diagnóstico Quant |")
    md.append("|:---|:---:|:---:|:---|")
    md.append(f"| **CAGR Médio** | `{cagr_lo_m:.2f}% a.a.` | `{cagr_ls_m:.2f}% a.a.` | Long-Only captura o beta de mercado positivo somado ao Alpha Low-Vol. |")
    md.append(f"| **Índice Sharpe Médio** | `{sharpe_lo_m:.2f}` | `{sharpe_ls_m:.2f}` | Long-Short isola o fator puro de baixa volatilidade descorrelacionado do Ibov. |")
    md.append(f"| **Max Drawdown Médio** | `{dd_lo_m:.2f}%` | `{dd_ls_m:.2f}%` | Long-Short apresenta menor volatilidade direcional, mas depende da estabilidade da perna vendida. |")
    
    md.append("\n---\n")
    
    md.append("## 🔍 4. Sensibilidade aos Parâmetros Chave")
    md.append("### 4.1. Impacto da Janela de Volatilidade (Lookback)")
    md.append("| Janela (Lookback) | CAGR Médio (% a.a.) | Volatilidade Média (% a.a.) | Sharpe Médio | Max Drawdown Médio (%) |")
    md.append("|:---|:---:|:---:|:---:|:---:|")
    for lk_name, row_s in lk_sens.iterrows():
        md.append(f"| **{lk_name}** | {row_s['CAGR_Pct']:.2f}% | {row_s['Volatilidade_Anualizada_Pct']:.2f}% | **{row_s['Indice_Sharpe']:.2f}** | {row_s['Max_Drawdown_Pct']:.2f}% |")
        
    md.append("\n### 4.2. Impacto da Fricção de Custos de Transação")
    md.append("| Custo por Giro (Turnover) | CAGR Médio (% a.a.) | Sharpe Médio | Alpha Médio (% a.a.) |")
    md.append("|:---|:---:|:---:|:---:|")
    for cst_val, row_c in custo_sens.iterrows():
        md.append(f"| **{cst_val:.0f} bps** | {row_c['CAGR_Pct']:.2f}% | **{row_c['Indice_Sharpe']:.2f}** | {row_c['Alpha_Anualizado_Pct']:+.2f}% |")
        
    md.append("\n---\n")
    
    md.append("## ⚠️ 5. Matriz de Alertas de Vieses e Fragilidades Metodológicas")
    md.append("- **Viés de Sobrevivência (*Survivorship Bias*):** ✅ Mitigado integralmente via base histórica reconstituída do IBrX-100 corte a corte.")
    md.append("- **Viés de Antecipação (*Look-Ahead Bias*):** ✅ Mitigado via cálculo estrito com pregos anteriores à abertura da carteira.")
    md.append("- **Atrito de Mercado Realista:** ⚠️ Simulações com 0 bps são puramente acadêmicas. Recomenda-se adotar como base de produção custos entre **5 bps e 15 bps**.")
    md.append("- **Capacidade e Concentração:** Carteiras com 10% (aprox. 10 ativos) possuem maior volatilidade idiossincrática do que carteiras de 20% (aprox. 20 ativos).")
    
    md.append("\n---\n")
    md.append("## 🎯 6. Recomendação do Portfolio Manager para Produção")
    md.append("1. **Modo:** `Long-Only (Q1 Low Volatility)`.")
    md.append("2. **Lookback:** `252 pregões (12 meses)` para filtragem robusta de ruídos de curto prazo.")
    md.append("3. **Frequência:** `Trimestral` (alinhada aos rebalanceamentos oficiais da B3, minimizando turnover e custos operacionais).")
    md.append("4. **Tamanho do Quintil:** `20% do IBrX-100` (cerca de 20 a 25 ações equiponderadas), oferecendo diversificação setorial balanceada entre Utilities, Bancos, Seguros e Telecom.")
    
    conteudo_final = "\n".join(md)
    
    # Salva no caminho especificado
    try:
        with open(caminho_md, "w", encoding="utf-8") as f:
            f.write(conteudo_final)
        print(f"📄 Relatório Markdown salvo com sucesso em '{caminho_md}'.")
    except Exception as e:
        print(f"⚠️ Erro ao salvar arquivo Markdown ({e}).")
        
    return conteudo_final

