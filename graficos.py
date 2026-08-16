"""
===============================================================================
MÓDULO DE GERAÇÃO DE RELATÓRIOS VISUAIS (graficos.py)
Projeto: Desafio Quant AI 2026 - Tese 2 (Anomalia de Baixa Volatilidade)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================
Este módulo gera gráficos profissionais em alta resolução (300 DPI) com a
identidade visual oficial do Jonathan:
- Fundo Principal / Superfície: Verde-petróleo escuro (#1F3B2C e #11231A)
- Jonathan (Q1 Low Vol): Dourado envelhecido (#B08D4C / #D4AF6A)
- A Lebre (Q5 High Vol): Coral / Terracota (#E76F51)
- Benchmark (Ibovespa): Cinza claro (#D9D9D9)
- CDI: Branco puro (#FFFFFF)

Gráficos gerados e salvos em reports/:
1. curva_capital.png (Escalas Linear e Logarítmica)
2. drawdown_subaquatico.png (Rebaixamento Histórico Subaquático)
3. dispersao_quintis.png (Quebra da Relação CAPM e Análise dos 5 Quintis)
4. heatmap_retornos.png (Retornos Mensais e Anuais do Jonathan)
5. composicao_ultimo_rebalanceamento.png (Ativos e Setores da Carteira Atual)
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
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from typing import Dict, Optional



# Paleta Visual Oficial do Jonathan
CORES = {
    'fundo_escuro': '#11231A',
    'card_escuro': '#1F3B2C',
    'jonathan_gold': '#B08D4C',
    'jonathan_light_gold': '#D4AF6A',
    'lebre_coral': '#E76F51',
    'benchmark_gray': '#D9D9D9',
    'cdi_white': '#FFFFFF',
    'grid_color': '#2A4E3B',
    'text_light': '#E8EFEA',
    'text_muted': '#9BB5A4',
    'q2': '#3A6B52',
    'q3': '#5B8C74',
    'q4': '#99855B'
}


def aplicar_estilo_jonathan():
    """Configura parâmetros globais do Matplotlib para o tema escuro do Jonathan."""
    plt.rcParams.update({
        'figure.facecolor': CORES['fundo_escuro'],
        'axes.facecolor': CORES['card_escuro'],
        'axes.edgecolor': CORES['grid_color'],
        'axes.labelcolor': CORES['text_light'],
        'axes.titlesize': 14,
        'axes.labelsize': 11,
        'xtick.color': CORES['text_muted'],
        'ytick.color': CORES['text_muted'],
        'text.color': CORES['text_light'],
        'grid.color': CORES['grid_color'],
        'grid.linestyle': '--',
        'grid.alpha': 0.6,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Arial', 'Helvetica']
    })


def gerar_grafico_curva_capital(
    df_curvas: pd.DataFrame,
    caminho_saida: str = "reports/curva_capital.png"
):
    """
    Gera o gráfico comparativo da Curva de Capital (Jonathan vs Lebre vs Ibov vs CDI)
    em dois painéis (Escala Linear e Escala Logarítmica).
    """
    aplicar_estilo_jonathan()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'hspace': 0.15})
    
    datas = df_curvas.index
    
    # Painel 1: Escala Linear
    ax1.plot(datas, df_curvas['Q1_Jonathan'], label='Q1: Jonathan (Low Vol)', color=CORES['jonathan_gold'], linewidth=2.8)
    ax1.plot(datas, df_curvas['Benchmark'], label='Benchmark (Ibovespa)', color=CORES['benchmark_gray'], linewidth=1.8, linestyle='--')
    ax1.plot(datas, df_curvas['CDI'], label='CDI (Taxa Livre de Risco)', color=CORES['cdi_white'], linewidth=1.8, linestyle=':')
    ax1.plot(datas, df_curvas['Q5_Lebre'], label='Q5: A Lebre (High Vol)', color=CORES['lebre_coral'], linewidth=2.0)
    
    ax1.set_title('Evolucao do Capital Acumulado (Base 100) - Escala Linear', fontsize=14, fontweight='bold', pad=12)
    ax1.set_ylabel('Valor do Portfolio (R$)', fontsize=11)
    ax1.grid(True)
    ax1.legend(loc='upper left', framealpha=0.85, facecolor=CORES['card_escuro'], edgecolor=CORES['jonathan_gold'])
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
    
    # Painel 2: Escala Logarítmica
    ax2.plot(datas, df_curvas['Q1_Jonathan'], label='Jonathan (Low Vol)', color=CORES['jonathan_gold'], linewidth=2.8)
    ax2.plot(datas, df_curvas['Benchmark'], label='Ibovespa', color=CORES['benchmark_gray'], linewidth=1.8, linestyle='--')
    ax2.plot(datas, df_curvas['CDI'], label='CDI', color=CORES['cdi_white'], linewidth=1.8, linestyle=':')
    ax2.plot(datas, df_curvas['Q5_Lebre'], label='A Lebre (High Vol)', color=CORES['lebre_coral'], linewidth=2.0)
    
    ax2.set_yscale('log')
    ax2.set_title('Evolucao do Capital Acumulado - Escala Logaritmica (Composicao de Juros)', fontsize=13, fontweight='bold', pad=10)
    ax2.set_ylabel('Valor em Escala Log', fontsize=11)
    ax2.set_xlabel('Ano', fontsize=11)
    ax2.grid(True, which='both', linestyle='--', alpha=0.5)
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))

    # Rodapé com Metáfora
    fig.text(0.5, 0.01, 'Jonathan: "Nao corro riscos desnecessarios. Acumulo tempo a favor. Consistencia hoje, liberdade sempre."',
             ha='center', fontsize=10, fontstyle='italic', color=CORES['jonathan_light_gold'])

    
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📊 [Gráfico Salvo] {caminho_saida}")


def gerar_grafico_drawdown(
    df_curvas: pd.DataFrame,
    caminho_saida: str = "reports/drawdown_subaquatico.png"
):
    """
    Gera o gráfico de Drawdown Subaquático (Underwater Drawdown) comparando as quedas
    do Jonathan, da Lebre e do Benchmark de mercado.
    """
    aplicar_estilo_jonathan()
    fig, ax = plt.subplots(figsize=(14, 7))
    
    datas = df_curvas.index
    
    dd_jonathan = (df_curvas['Q1_Jonathan'] / df_curvas['Q1_Jonathan'].cummax() - 1.0) * 100.0
    dd_lebre = (df_curvas['Q5_Lebre'] / df_curvas['Q5_Lebre'].cummax() - 1.0) * 100.0
    dd_bench = (df_curvas['Benchmark'] / df_curvas['Benchmark'].cummax() - 1.0) * 100.0
    
    ax.fill_between(datas, dd_lebre, 0, color=CORES['lebre_coral'], alpha=0.25, label='Drawdown A Lebre (High Vol)')
    ax.plot(datas, dd_lebre, color=CORES['lebre_coral'], linewidth=1.5, alpha=0.8)
    
    ax.fill_between(datas, dd_bench, 0, color=CORES['benchmark_gray'], alpha=0.15, label='Drawdown Ibovespa')
    ax.plot(datas, dd_bench, color=CORES['benchmark_gray'], linewidth=1.2, linestyle='--', alpha=0.7)
    
    ax.fill_between(datas, dd_jonathan, 0, color=CORES['jonathan_gold'], alpha=0.45, label='Drawdown Jonathan (Low Vol)')
    ax.plot(datas, dd_jonathan, color=CORES['jonathan_gold'], linewidth=2.2)
    
    ax.set_title('Grafico de Drawdown Subaquatico (Underwater Chart) - Resiliencia e Preservacao', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Rebaixamento a partir da Maxima (%)', fontsize=11)
    ax.set_xlabel('Ano', fontsize=11)
    ax.grid(True)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.legend(loc='lower left', framealpha=0.85, facecolor=CORES['card_escuro'], edgecolor=CORES['jonathan_gold'])
    
    # Linha zero
    ax.axhline(0, color=CORES['text_muted'], linestyle='-', linewidth=1.0)
    
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📊 [Gráfico Salvo] {caminho_saida}")


def gerar_grafico_dispersao_quintis(
    df_metricas: pd.DataFrame,
    df_curvas: pd.DataFrame,
    caminho_saida: str = "reports/dispersao_quintis.png"
):
    """
    Gera o gráfico de Dispersão e Análise Monotônica dos 5 Quintis (Q1 a Q5).
    Demonstra empiricamente a anomalia de baixa volatilidade e a quebra da reta clássica do CAPM.
    """
    aplicar_estilo_jonathan()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Extrai quintis
    colunas_q = ['Q1_Jonathan', 'Q2', 'Q3', 'Q4', 'Q5_Lebre']
    nomes_exibicao = ['Q1 (Jonathan)', 'Q2', 'Q3', 'Q4', 'Q5 (Lebre)']
    cores_q = [CORES['jonathan_gold'], CORES['q2'], CORES['q3'], CORES['q4'], CORES['lebre_coral']]
    
    n_pregoes = len(df_curvas)
    anos = n_pregoes / 252.0
    
    vols = []
    cagrs = []
    sharpes = []
    betas = []
    
    ret_cdi_acum = (df_curvas['CDI'].iloc[-1] / df_curvas['CDI'].iloc[0]) ** (1.0 / anos) - 1.0
    
    for q in colunas_q:
        cagr = ((df_curvas[q].iloc[-1] / df_curvas[q].iloc[0]) ** (1.0 / anos) - 1.0) * 100.0
        ret_d = df_curvas[q].pct_change().dropna()
        vol = ret_d.std() * np.sqrt(252) * 100.0
        sharpe = (cagr/100.0 - ret_cdi_acum) / (vol/100.0) if vol > 0 else 0.0
        
        bench_ret = df_curvas['Benchmark'].pct_change().dropna()
        beta = ret_d.cov(bench_ret) / bench_ret.var()
        
        vols.append(vol)
        cagrs.append(cagr)
        sharpes.append(sharpe)
        betas.append(beta)
        
    # Painel 1: Dispersão Risco (Volatilidade) vs Retorno Anualizado (CAGR)
    for i in range(len(colunas_q)):
        ax1.scatter(vols[i], cagrs[i], color=cores_q[i], s=250, zorder=5, edgecolors='white', linewidth=1.5)
        ax1.annotate(
            f" {nomes_exibicao[i]}\n (Sharpe: {sharpes[i]:.2f})",
            (vols[i], cagrs[i]),
            textcoords="offset points",
            xytext=(10, -5),
            fontsize=10,
            fontweight='bold',
            color=cores_q[i]
        )
        
    # Ponto do Benchmark
    cagr_b = ((df_curvas['Benchmark'].iloc[-1] / df_curvas['Benchmark'].iloc[0]) ** (1.0 / anos) - 1.0) * 100.0
    vol_b = df_curvas['Benchmark'].pct_change().dropna().std() * np.sqrt(252) * 100.0
    ax1.scatter(vol_b, cagr_b, color=CORES['benchmark_gray'], s=200, marker='s', zorder=5, edgecolors='black')
    ax1.annotate(" Benchmark (Ibov)", (vol_b, cagr_b), textcoords="offset points", xytext=(10, -5), fontsize=10, color=CORES['benchmark_gray'])
    
    # Reta teórica CAPM (ilustrativa)
    ax1.plot([min(vols)*0.9, max(vols)*1.1], [ret_cdi_acum*100, ret_cdi_acum*100 + (cagr_b - ret_cdi_acum*100)*1.4],
             color='gray', linestyle=':', label='Previsao Teorica CAPM (Linear)', alpha=0.6)
    
    ax1.set_title('Dispersao Empirica: Risco vs. Retorno por Quintil', fontsize=13, fontweight='bold', pad=12)
    ax1.set_xlabel('Volatilidade Anualizada (%)', fontsize=11)
    ax1.set_ylabel('Retorno Anualizado - CAGR (%)', fontsize=11)
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.legend(loc='lower right', facecolor=CORES['card_escuro'])
    
    # Painel 2: Índice de Sharpe por Quintil (Monotonicidade da Anomalia)
    barras = ax2.bar(nomes_exibicao, sharpes, color=cores_q, edgecolor=CORES['grid_color'], width=0.6)
    ax2.axhline(0, color=CORES['text_muted'], linestyle='-', linewidth=1.0)
    
    for barra in barras:
        yval = barra.get_height()
        ax2.text(
            barra.get_x() + barra.get_width()/2.0,
            yval + (0.02 if yval >= 0 else -0.05),
            f"{yval:.2f}",
            ha='center',
            va='bottom' if yval >= 0 else 'top',
            fontsize=11,
            fontweight='bold',
            color=CORES['text_light']
        )
        
    ax2.set_title('Indice de Sharpe (vs. CDI) por Quintil de Volatilidade', fontsize=13, fontweight='bold', pad=12)
    ax2.set_ylabel('Indice de Sharpe', fontsize=11)
    ax2.grid(True, axis='y')
    
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📊 [Gráfico Salvo] {caminho_saida}")


def gerar_heatmap_retornos(
    df_retornos_mensais: pd.DataFrame,
    caminho_saida: str = "reports/heatmap_retornos.png"
):
    """
    Gera o Mapa de Calor dos retornos mensais e anuais da estratégia Jonathan (Q1 Low Vol).
    """
    aplicar_estilo_jonathan()
    fig, ax = plt.subplots(figsize=(14, max(5, len(df_retornos_mensais) * 0.7)))
    
    # Cores customizadas: Coral para perdas, Verde-Petróleo e Dourado para ganhos
    cmap = sns.diverging_palette(15, 140, s=85, l=45, n=15, as_cmap=True)
    
    sns.heatmap(
        df_retornos_mensais,
        annot=True,
        fmt=".1f",
        cmap=cmap,
        center=0,
        cbar_kws={'label': 'Retorno (%)'},
        linewidths=1.2,
        linecolor=CORES['fundo_escuro'],
        ax=ax,
        annot_kws={'size': 10, 'weight': 'bold'}
    )
    
    ax.set_title('Mapa de Calor de Retornos Mensais e Anuais - Jonathan (Q1 Low Vol)', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Ano', fontsize=11)
    ax.set_xlabel('Mes', fontsize=11)
    
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📊 [Gráfico Salvo] {caminho_saida}")


def gerar_grafico_composicao_atual(
    ultimo_rebalanceamento: Dict,
    caminho_saida: str = "reports/composicao_ultimo_rebalanceamento.png"
):
    """
    Gera gráfico de barras horizontais com a composição da carteira do Jonathan
    no último rebalanceamento, destacando ticker e volatilidade anualizada calculada.
    """
    if not ultimo_rebalanceamento or 'detalhes_quintis' not in ultimo_rebalanceamento:
        print("⚠️ Sem dados de último rebalanceamento para gerar gráfico de composição.")
        return
        
    aplicar_estilo_jonathan()
    df_q1 = ultimo_rebalanceamento['detalhes_quintis']['Q1_Jonathan']['df_ativos']
    df_q1 = df_q1.sort_values('Volatilidade_Anualizada', ascending=False)
    
    fig, ax = plt.subplots(figsize=(12, max(6, len(df_q1) * 0.45)))
    
    vols_pct = df_q1['Volatilidade_Anualizada'] * 100.0
    tickers = [t.replace('.SA', '') for t in df_q1['Ticker']]
    
    barras = ax.barh(tickers, vols_pct, color=CORES['jonathan_gold'], edgecolor=CORES['grid_color'], height=0.65)
    
    for barra in barras:
        w = barra.get_width()
        ax.text(
            w + 0.5,
            barra.get_y() + barra.get_height()/2.0,
            f"{w:.1f}%",
            va='center',
            fontsize=9.5,
            fontweight='bold',
            color=CORES['text_light']
        )
        
    data_str = pd.to_datetime(ultimo_rebalanceamento['data_rebalanceamento']).strftime('%d/%m/%Y')
    ax.set_title(f'Carteira Jonathan (Q1 Low Vol) - Ativos Selecionados em {data_str}', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Volatilidade Historica Anualizada (252 pregoes) (%)', fontsize=11)
    ax.grid(True, axis='x')
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📊 [Gráfico Salvo] {caminho_saida}")



def gerar_todos_relatorios_visuais(resultado_backtest: Dict, pasta_reports: str = "reports"):
    """
    Executa a geração e salvamento em lote de todos os 5 gráficos oficiais do projeto.
    """
    os.makedirs(pasta_reports, exist_ok=True)
    print("\n🎨 Gerando conjunto completo de relatórios gráficos do Jonathan...")
    
    df_curvas = resultado_backtest['curvas_capital']
    df_metricas = resultado_backtest['metricas']
    df_mensais = resultado_backtest['retornos_mensais_jonathan']
    ultimo_reb = resultado_backtest.get('ultimo_rebalanceamento')
    
    gerar_grafico_curva_capital(df_curvas, os.path.join(pasta_reports, 'curva_capital.png'))
    gerar_grafico_drawdown(df_curvas, os.path.join(pasta_reports, 'drawdown_subaquatico.png'))
    gerar_grafico_dispersao_quintis(df_metricas, df_curvas, os.path.join(pasta_reports, 'dispersao_quintis.png'))
    gerar_heatmap_retornos(df_mensais, os.path.join(pasta_reports, 'heatmap_retornos.png'))
    gerar_grafico_composicao_atual(ultimo_reb, os.path.join(pasta_reports, 'composicao_ultimo_rebalanceamento.png'))
    
    print("✅ Todos os 5 gráficos foram salvos com sucesso em 'reports/'!\n")
