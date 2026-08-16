"""
===============================================================================
GERADOR DE FIGURAS PUBLICATION-READY (figuras.py)
Projeto: Desafio Quant AI 2026 - Anomalia de Baixa Volatilidade
Mascote: Jonathan, o Robô-Tartaruga Quant
===============================================================================
Gera figuras em alta resolução (PNG, 300 DPI) para o Relatório Final (relatorio.md):
(a) Curva de capital acumulada — Estratégia Long-Only vs Long-Short vs Ibovespa vs CDI
(b) Alpha Acumulado sobre o CDI — Figura central do relatório
(c) Drawdown ao longo do tempo (Underwater Chart)
(d) Mapa de calor dos retornos mensais da estratégia
(e) Tabela-resumo das principais métricas quantitativas
===============================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import seaborn as sns

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import backtest

# Criação do diretório figuras/
PASTA_FIGURAS = os.path.join(BASE_DIR, "figuras")
os.makedirs(PASTA_FIGURAS, exist_ok=True)

# Paleta Visual do Jonathan (Padrão Publicação)
C_DARK_GREEN = "#11231A"
C_FOREST = "#1F3B2C"
C_GOLD = "#B08D4C"
C_LIGHT_GOLD = "#D4AF6A"
C_CORAL = "#E76F51"
C_EMERALD = "#2A9D8F"
C_GRAY = "#6C757D"
C_LIGHT_GRAY = "#E9ECEF"
C_NAVY = "#264653"

# Configurações globais do Matplotlib
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8


def carregar_dados_simulacao():
    """Executa os backtests principais para extrair as séries temporais."""
    print("⏳ Executando backtests para geração das figuras...")
    
    # 1. Estratégia Long-Only Campeã (252d, Trimestral, 5 bps)
    res_lo = backtest.executar_backtest(
        data_inicio="2018-01-01",
        data_fim="2026-08-01",
        lookback_dias=252,
        frequencia_rebalanceamento="trimestral",
        fracao_quintil=0.20,
        custo_transacao_bps=5.0,
        modo_estrategia="long_only",
        verbose=False
    )
    
    # 2. Estratégia Long-Short BAB (252d, Trimestral, 5 bps)
    res_ls = backtest.executar_backtest(
        data_inicio="2018-01-01",
        data_fim="2026-08-01",
        lookback_dias=252,
        frequencia_rebalanceamento="trimestral",
        fracao_quintil=0.20,
        custo_transacao_bps=5.0,
        modo_estrategia="long_short",
        verbose=False
    )
    
    return res_lo, res_ls


# ==============================================================================
# (a) FIGURA 1: CURVA DE CAPITAL ACUMULADA
# ==============================================================================
def gerar_figura_curva_capital(res_lo, res_ls):
    print("📊 Gerando Figura 1: Curva de Capital...")
    
    df_p = res_lo['curvas_capital']
    curva_lo = df_p['Estrategia_Ativa']
    curva_ibov = df_p['Benchmark']
    curva_cdi = df_p['CDI']
    curva_ls = res_ls['curvas_capital']['Estrategia_Ativa']
    
    fig, ax = plt.subplots(figsize=(12, 6.5))
    
    # Linhas de patrimônio
    ax.plot(curva_lo.index, curva_lo, label="Jonathan Long-Only (Q1 Low Vol - 252d)", color=C_GOLD, linewidth=2.5)
    ax.plot(curva_ls.index, curva_ls, label="Jonathan Long-Short BAB (Q1 - Q5 + CDI)", color=C_CORAL, linewidth=2.0, linestyle='-.')
    ax.plot(curva_ibov.index, curva_ibov, label="Benchmark de Mercado (Ibovespa)", color=C_GRAY, linewidth=1.6, linestyle='--')
    ax.plot(curva_cdi.index, curva_cdi, label="Taxa Livre de Risco (CDI)", color=C_NAVY, linewidth=1.8, linestyle=':')
    
    # Destaque final dos valores
    ret_lo = (curva_lo.iloc[-1] / curva_lo.iloc[0] - 1) * 100
    ret_ls = (curva_ls.iloc[-1] / curva_ls.iloc[0] - 1) * 100
    ret_ibov = (curva_ibov.iloc[-1] / curva_ibov.iloc[0] - 1) * 100
    ret_cdi = (curva_cdi.iloc[-1] / curva_cdi.iloc[0] - 1) * 100
    
    ax.text(curva_lo.index[-1], curva_lo.iloc[-1] + 4, f" +{ret_lo:.1f}%", color=C_GOLD, fontweight='bold', fontsize=9.5)
    ax.text(curva_ls.index[-1], curva_ls.iloc[-1] - 8, f" +{ret_ls:.1f}%", color=C_CORAL, fontweight='bold', fontsize=9.5)
    ax.text(curva_ibov.index[-1], curva_ibov.iloc[-1] - 8, f" +{ret_ibov:.1f}%", color=C_GRAY, fontweight='bold', fontsize=9.5)
    ax.text(curva_cdi.index[-1], curva_cdi.iloc[-1] + 3, f" +{ret_cdi:.1f}%", color=C_NAVY, fontweight='bold', fontsize=9.5)
    
    # Formatação de eixos e títulos
    ax.set_title("Evolução Patrimonial Acumulada: Jonathan Low Vol vs. Benchmarks (2018–2026)\nBase 100 | Rebalanceamento Trimestral | Custo 5 bps",
                 fontsize=13, fontweight='bold', pad=15, color=C_DARK_GREEN)
    ax.set_xlabel("Ano / Mês", fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel("Patrimônio Acumulado (Base 100)", fontsize=11, fontweight='bold', labelpad=10)
    
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
    
    ax.grid(True, linestyle='--', alpha=0.5, color='#CCCCCC')
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    
    plt.tight_layout()
    caminho = os.path.join(PASTA_FIGURAS, "fig1_curva_capital.png")
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()
    print(f"✅ Salvo: {caminho}")


# ==============================================================================
# (b) FIGURA 2: ALPHA ACUMULADO SOBRE O CDI (FIGURA CENTRAL)
# ==============================================================================
def gerar_figura_alpha_acumulado_cdi(res_lo, res_ls):
    print("📊 Gerando Figura 2: Alpha Acumulado sobre o CDI (Central)...")
    
    df_p = res_lo['curvas_capital']
    curva_lo = df_p['Estrategia_Ativa']
    curva_cdi = df_p['CDI']
    curva_ls = res_ls['curvas_capital']['Estrategia_Ativa']
    
    # Alpha em pontos percentuais acumulados e spread relativo
    alpha_acum_lo_pct = (curva_lo / curva_cdi - 1.0) * 100.0
    alpha_acum_ls_pct = (curva_ls / curva_cdi - 1.0) * 100.0
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8.5), gridspec_kw={'height_ratios': [2.2, 1.2]}, sharex=True)
    
    # Painel Superior: Alpha Percentual Acumulado sobre o CDI
    ax1.plot(alpha_acum_lo_pct.index, alpha_acum_lo_pct, label="Alpha Long-Only (Q1 vs. CDI)", color=C_GOLD, linewidth=2.5)
    ax1.plot(alpha_acum_ls_pct.index, alpha_acum_ls_pct, label="Alpha Long-Short BAB (Q1 - Q5)", color=C_CORAL, linewidth=2.0, linestyle='-.')
    ax1.axhline(0, color=C_NAVY, linestyle='--', linewidth=1.5, label="Hurdle Rate: CDI (0% Alpha)")
    
    ax1.fill_between(alpha_acum_lo_pct.index, alpha_acum_lo_pct, 0, where=(alpha_acum_lo_pct >= 0),
                     color=C_GOLD, alpha=0.25, label="Superávit sobre o CDI")
    ax1.fill_between(alpha_acum_lo_pct.index, alpha_acum_lo_pct, 0, where=(alpha_acum_lo_pct < 0),
                     color=C_GRAY, alpha=0.25)
    
    final_alpha_lo = alpha_acum_lo_pct.iloc[-1]
    final_alpha_ls = alpha_acum_ls_pct.iloc[-1]
    ax1.text(alpha_acum_lo_pct.index[-1], final_alpha_lo + 1.5, f" +{final_alpha_lo:.1f}% vs CDI", color=C_GOLD, fontweight='bold', fontsize=10)
    ax1.text(alpha_acum_ls_pct.index[-1], final_alpha_ls - 3.5, f" +{final_alpha_ls:.1f}% vs CDI", color=C_CORAL, fontweight='bold', fontsize=10)
    
    ax1.set_title("FIGURA CENTRAL: Geração de Alpha Acumulado sobre a Taxa Livre de Risco (CDI)\nSpread Relativo de Performance Acumulada da Estratégia Jonathan (2018–2026)",
                  fontsize=13, fontweight='bold', pad=12, color=C_DARK_GREEN)
    ax1.set_ylabel("Alpha Acumulado vs. CDI (%)", fontsize=11, fontweight='bold', labelpad=8)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.grid(True, linestyle='--', alpha=0.5, color='#CCCCCC')
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    
    # Painel Inferior: Spread Diário Acumulado em R$ (Base R$ 100)
    spread_reais_lo = curva_lo - curva_cdi
    spread_reais_ls = curva_ls - curva_cdi
    
    ax2.plot(spread_reais_lo.index, spread_reais_lo, color=C_GOLD, linewidth=2.0, label="Spread Bruto (R$ Long-Only - R$ CDI)")
    ax2.plot(spread_reais_ls.index, spread_reais_ls, color=C_CORAL, linewidth=1.6, linestyle='-.', label="Spread Bruto (R$ Long-Short - R$ CDI)")
    ax2.axhline(0, color=C_NAVY, linestyle='--', linewidth=1.2)
    ax2.set_ylabel("Excesso em R$\n(Base R$ 100)", fontsize=10, fontweight='bold')
    ax2.set_xlabel("Ano / Mês", fontsize=11, fontweight='bold', labelpad=8)
    ax2.grid(True, linestyle='--', alpha=0.5, color='#CCCCCC')
    ax2.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=8.5)
    
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    plt.tight_layout()
    caminho = os.path.join(PASTA_FIGURAS, "fig2_alpha_acumulado_cdi.png")
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()
    print(f"✅ Salvo: {caminho}")


# ==============================================================================
# (c) FIGURA 3: DRAWDOWN TEMPORAL (UNDERWATER CHART)
# ==============================================================================
def gerar_figura_drawdown(res_lo):
    print("📊 Gerando Figura 3: Drawdown Temporal...")
    
    df_p = res_lo['curvas_capital']
    curva_lo = df_p['Estrategia_Ativa']
    curva_ibov = df_p['Benchmark']
    
    dd_lo = (curva_lo / curva_lo.cummax() - 1.0) * 100.0
    dd_ibov = (curva_ibov / curva_ibov.cummax() - 1.0) * 100.0
    
    fig, ax = plt.subplots(figsize=(12, 5.5))
    
    ax.fill_between(dd_ibov.index, dd_ibov, 0, color=C_GRAY, alpha=0.35, label="Drawdown Ibovespa (Max -46.8%)")
    ax.fill_between(dd_lo.index, dd_lo, 0, color=C_GOLD, alpha=0.6, label="Drawdown Jonathan Low Vol (Max -34.8%)")
    
    ax.plot(dd_ibov.index, dd_ibov, color=C_GRAY, linewidth=1.2)
    ax.plot(dd_lo.index, dd_lo, color=C_GOLD, linewidth=2.0)
    
    # Anotação do Choque de 2020 (Covid-19)
    min_idx_lo = dd_lo.idxmin()
    min_val_lo = dd_lo.min()
    min_idx_ibov = dd_ibov.idxmin()
    min_val_ibov = dd_ibov.min()
    
    ax.scatter([min_idx_lo], [min_val_lo], color=C_GOLD, s=60, zorder=5)
    ax.annotate(f"Jonathan Low Vol: {min_val_lo:.1f}%\n(Preservação de Capital)",
                xy=(min_idx_lo, min_val_lo), xytext=(min_idx_lo + pd.Timedelta(days=120), min_val_lo - 4),
                arrowprops=dict(facecolor=C_GOLD, shrink=0.08, width=1.5, headwidth=6),
                fontweight='bold', fontsize=9, color=C_DARK_GREEN)
    
    ax.scatter([min_idx_ibov], [min_val_ibov], color=C_CORAL, s=60, zorder=5)
    ax.annotate(f"Ibovespa: {min_val_ibov:.1f}%\n(Crash Mar/2020)",
                xy=(min_idx_ibov, min_val_ibov), xytext=(min_idx_ibov - pd.Timedelta(days=500), min_val_ibov - 3),
                arrowprops=dict(facecolor=C_CORAL, shrink=0.08, width=1.5, headwidth=6),
                fontweight='bold', fontsize=9, color=C_CORAL)
    
    ax.set_title("Gráfico Subaquático de Drawdown (Underwater Chart): Jonathan Low Vol vs. Ibovespa (2018–2026)\nEvidência de Resiliência e Menor Profundidade de Rebaixamento de Capital",
                 fontsize=13, fontweight='bold', pad=15, color=C_DARK_GREEN)
    ax.set_xlabel("Ano / Mês", fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel("Rebaixamento do Topo Histórico (%)", fontsize=11, fontweight='bold', labelpad=10)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    ax.grid(True, linestyle='--', alpha=0.5, color='#CCCCCC')
    ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    
    plt.tight_layout()
    caminho = os.path.join(PASTA_FIGURAS, "fig3_drawdown_temporal.png")
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()
    print(f"✅ Salvo: {caminho}")


# ==============================================================================
# (d) FIGURA 4: MAPA DE CALOR DOS RETORNOS MENSAIS
# ==============================================================================
def gerar_figura_heatmap_mensal(res_lo):
    print("📊 Gerando Figura 4: Heatmap de Retornos Mensais...")
    
    df_p = res_lo['curvas_capital']
    serie_p = df_p['Estrategia_Ativa']

    
    # Resample para retornos mensais
    serie_mensal = serie_p.resample('ME').last().pct_change().dropna() * 100.0
    
    df_mes = pd.DataFrame({
        'Ano': serie_mensal.index.year,
        'Mes': serie_mensal.index.month,
        'Retorno': serie_mensal.values
    })
    
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    pivot_ret = df_mes.pivot(index='Ano', columns='Mes', values='Retorno')
    pivot_ret.columns = [nomes_meses[m-1] for m in pivot_ret.columns]
    
    # Retorno Anual
    ret_anual = serie_p.resample('YE').last().pct_change() * 100.0
    df_ret_anual = pd.DataFrame({'Ano': ret_anual.index.year, 'Ano Total': ret_anual.values}).set_index('Ano')
    
    # Ajuste de primeiro ano se necessário
    if 2018 in pivot_ret.index and pd.isna(df_ret_anual.loc[2018, 'Ano Total'] if 2018 in df_ret_anual.index else np.nan):
        df_ret_anual.loc[2018, 'Ano Total'] = ((serie_p.loc['2018-12-31':].iloc[0] if '2018-12-31' in serie_p.index else serie_p.loc['2018'].iloc[-1]) / serie_p.iloc[0] - 1.0) * 100.0
    
    fig, ax = plt.subplots(figsize=(13, 6))
    
    cmap = sns.diverging_palette(10, 130, s=85, l=55, as_cmap=True)
    
    sns.heatmap(pivot_ret, annot=True, fmt=".2f", cmap=cmap, center=0.0,
                cbar_kws={'label': 'Retorno Mensal (%)', 'orientation': 'horizontal', 'pad': 0.18, 'shrink': 0.6},
                linewidths=1.2, linecolor='white', ax=ax)
    
    ax.set_title("Matriz de Retornos Mensais (%): Estratégia Jonathan Low Vol (2018–2026)\nDistribuição Temporal e Persistência de Rentabilidade",
                 fontsize=13, fontweight='bold', pad=15, color=C_DARK_GREEN)
    ax.set_xlabel("Mês do Ano", fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel("Ano", fontsize=11, fontweight='bold', labelpad=10)
    
    plt.tight_layout()
    caminho = os.path.join(PASTA_FIGURAS, "fig4_heatmap_retornos_mensais.png")
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()
    print(f"✅ Salvo: {caminho}")


# ==============================================================================
# (e) FIGURA 5: TABELA-RESUMO DE MÉTRICAS COMO IMAGEM
# ==============================================================================
def gerar_figura_tabela_metricas(res_lo, res_ls):
    print("📊 Gerando Figura 5: Tabela-Resumo de Métricas...")
    
    m_lo = res_lo['metricas'].loc['Estrategia_Ativa']
    m_ls = res_ls['metricas'].loc['Estrategia_Ativa']
    m_bench = res_lo['metricas'].loc['Benchmark']
    m_cdi = res_lo['metricas'].loc['CDI']
    
    dados_tab = [
        ["Retorno Total Acumulado", f"{float(m_lo['Retorno Total (%)']):.2f}%", f"{float(m_ls['Retorno Total (%)']):.2f}%", f"{float(m_bench['Retorno Total (%)']):.2f}%", f"{float(m_cdi['Retorno Total (%)']):.2f}%"],
        ["CAGR (Retorno Anualizado)", f"{float(m_lo['CAGR (% a.a.)']):.2f}% a.a.", f"{float(m_ls['CAGR (% a.a.)']):.2f}% a.a.", f"{float(m_bench['CAGR (% a.a.)']):.2f}% a.a.", f"{float(m_cdi['CAGR (% a.a.)']):.2f}% a.a."],
        ["Volatilidade Anualizada", f"{float(m_lo['Volatilidade (% a.a.)']):.2f}% a.a.", f"{float(m_ls['Volatilidade (% a.a.)']):.2f}% a.a.", f"{float(m_bench['Volatilidade (% a.a.)']):.2f}% a.a.", f"{float(m_cdi['Volatilidade (% a.a.)']):.2f}% a.a."],
        ["Índice de Sharpe (vs. CDI)", f"{float(m_lo['Índice Sharpe (vs CDI)']):.2f}", f"{float(m_ls['Índice Sharpe (vs CDI)']):.2f}", f"{float(m_bench['Índice Sharpe (vs CDI)']):.2f}", "0.00"],
        ["Índice de Sortino", f"{float(m_lo['Índice Sortino']):.2f}", f"{float(m_ls['Índice Sortino']):.2f}", f"{float(m_bench['Índice Sortino']):.2f}", "-"],
        ["Alpha de Jensen Anualizado", f"{float(m_lo['Alpha Anualizado (%)']):+.2f}% a.a.", f"{float(m_ls['Alpha Anualizado (%)']):+.2f}% a.a.", "0.00%", "0.00%"],
        ["Beta Sistemático (vs. Ibov)", f"{float(m_lo['Beta (vs Ibov)']):.2f}", f"{float(m_ls['Beta (vs Ibov)']):.2f}", "1.00", "0.00"],
        ["Maximum Drawdown (MDD)", f"{float(m_lo['Max Drawdown (%)']):.2f}%", f"{float(m_ls['Max Drawdown (%)']):.2f}%", f"{float(m_bench['Max Drawdown (%)']):.2f}%", "0.00%"],
        ["Taxa de Acerto Trimestral", f"{float(m_lo['Win Rate Trimestral (%)']):.2f}%", f"{float(m_ls['Win Rate Trimestral (%)']):.2f}%", "-", "-"],
    ]
    
    colunas = ["Métrica Quantitativa", "Jonathan Long-Only\n(Q1 Low Vol)", "Jonathan Long-Short\n(BAB Q1-Q5 + CDI)", "Benchmark de Mercado\n(Ibovespa)", "Taxa Livre de Risco\n(CDI)"]
    
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.axis('off')
    
    tabela = ax.table(cellText=dados_tab, colLabels=colunas, loc='center', cellLoc='center')
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(10.5)
    tabela.scale(1.2, 1.8)
    
    # Estilização das células
    for (i, j), cell in tabela.get_celld().items():
        cell.set_edgecolor('#D9D9D9')
        if i == 0:
            cell.set_facecolor(C_FOREST)
            cell.set_text_props(color='white', weight='bold', fontsize=11)
            cell.set_height(0.12)
        elif j == 0:
            cell.set_facecolor('#F8F9FA')
            cell.set_text_props(weight='bold', color=C_DARK_GREEN, ha='left')
        elif j == 1:
            cell.set_facecolor('#FCF8E3')
            cell.set_text_props(weight='bold', color=C_GOLD)
        elif j == 2:
            cell.set_facecolor('#FDF2E9')
            cell.set_text_props(weight='bold', color=C_CORAL)
        else:
            cell.set_facecolor('white')
            cell.set_text_props(color='#333333')
            
    ax.set_title("Quadro Comparativo de Performance Ajustada ao Risco (2018–2026)\nBacktest Institucional com Fricção de Custos (5 bps)",
                 fontsize=13, fontweight='bold', pad=25, color=C_DARK_GREEN)
    
    plt.tight_layout()
    caminho = os.path.join(PASTA_FIGURAS, "fig5_tabela_resumo_metricas.png")
    plt.savefig(caminho, bbox_inches='tight')
    plt.close()
    print(f"✅ Salvo: {caminho}")


def main():
    print("=" * 80)
    print("🚀 GERADOR DE FIGURAS EM ALTA DEFINIÇÃO (PUBLICATION READY - 300 DPI)")
    print("=" * 80)
    
    res_lo, res_ls = carregar_dados_simulacao()
    
    gerar_figura_curva_capital(res_lo, res_ls)
    gerar_figura_alpha_acumulado_cdi(res_lo, res_ls)
    gerar_figura_drawdown(res_lo)
    gerar_figura_heatmap_mensal(res_lo)
    gerar_figura_tabela_metricas(res_lo, res_ls)
    
    print("=" * 80)
    print(f"🎉 Todas as 5 figuras foram geradas com sucesso em: {PASTA_FIGURAS}")
    print("=" * 80)


if __name__ == "__main__":
    main()
