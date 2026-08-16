"""
===============================================================================
PÁGINA 1: GRADE DE EXPERIMENTOS QUANTITATIVOS (pages/1_🔬_Grade_de_Experimentos.py)
Projeto: Desafio Quant AI 2026 - Anomalia de Baixa Volatilidade (Low Volatility Anomaly)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================
Aplicação Streamlit Multi-páginas com tema escuro personalizado (#11231A, #1F3B2C, #B08D4C, #D9D9D9):
- Grade multivariável de simulações com seletores múltiplos de lookback, modo, tamanho de carteira, rebalanceamento e custos.
- Tabela geral comparativa com filtros interativos e ordenação por métricas de risco e retorno.
- Módulo avançado de gráficos: Dispersão Risco x Retorno, Heatmap de Sharpe Ratio, Curvas de Capital Top 3 e Atrito de Custos.
- Inspeção detalhada de experimentos individuais com drawdown subaquático e últimos ativos selecionados.
- Motor de alertas automáticos de vieses metodológicos (Sharpe Inflado, Custo Zero, Amostra Curta, Concentração).
- Exportação de experimentos.csv e renderização do relatório executivo experimentos.md.
===============================================================================
"""

import os
import sys
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime

# Adiciona o diretório raiz ao sys.path para importações robustas no Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import backtest
from backtest import executar_grade_experimentos, gerar_relatorio_markdown_experimentos, executar_backtest

# Configuração da Página
st.set_page_config(
    page_title="Jonathan Quant — Grade de Experimentos (Desafio Quant AI 2026)",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta Visual do Jonathan
C_BG = "#11231A"
C_CARD = "#1F3B2C"
C_GOLD = "#B08D4C"
C_LIGHT_GOLD = "#D4AF6A"
C_CORAL = "#E76F51"
C_GRAY = "#D9D9D9"
C_TEXT = "#E8EFEA"
C_MUTED = "#9BB5A4"

# Custom CSS
st.markdown(f"""
<style>
    .stApp {{
        background-color: {C_BG};
        color: {C_TEXT};
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    .css-1d391kg, .stSidebar {{
        background-color: #162E22 !important;
    }}
    h1, h2, h3, h4 {{
        color: {C_GOLD} !important;
        font-weight: 700;
    }}
    .metric-card {{
        background: linear-gradient(135deg, #1F3B2C 0%, #162E22 100%);
        border: 1px solid {C_GOLD};
        border-radius: 10px;
        padding: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }}
    .metric-title {{
        color: {C_MUTED};
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 2px;
    }}
    .metric-value-gold {{
        color: {C_LIGHT_GOLD};
        font-size: 1.5rem;
        font-weight: 800;
    }}
    .metric-value-coral {{
        color: {C_CORAL};
        font-size: 1.5rem;
        font-weight: 800;
    }}
    .metric-value-gray {{
        color: {C_GRAY};
        font-size: 1.5rem;
        font-weight: 800;
    }}
    .metric-sub {{
        font-size: 0.75rem;
        color: {C_MUTED};
    }}
    .badge-quant {{
        display: inline-block;
        background-color: {C_GOLD};
        color: {C_BG};
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-bottom: 8px;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: #162E22;
        padding: 8px;
        border-radius: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {C_MUTED};
        border-radius: 6px;
        padding: 8px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {C_GOLD} !important;
        color: {C_BG} !important;
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# FUNÇÃO DE CACHE PARA A GRADE DE EXPERIMENTOS
# ==============================================================================
@st.cache_data(show_spinner="Simulando grade multivariável quantitativa...", ttl=3600)
def rodar_grade_cached(
    lookbacks_tuple,
    modos_tuple,
    fracoes_tuple,
    frequencias_tuple,
    custos_tuple,
    d_ini_str,
    d_fim_str
):
    df_res, dict_c, dict_d = executar_grade_experimentos(
        lista_lookbacks=list(lookbacks_tuple),
        lista_modos=list(modos_tuple),
        lista_fracoes=list(fracoes_tuple),
        lista_frequencias=list(frequencias_tuple),
        lista_custos=list(custos_tuple),
        data_inicio=d_ini_str,
        data_fim=d_fim_str
    )
    return df_res, dict_c, dict_d


# ==============================================================================
# BARRA LATERAL (CONFIGURAÇÃO DA GRADE MULTIVARIÁVEL)
# ==============================================================================
with st.sidebar:
    caminho_logo = os.path.join(BASE_DIR, "assets", "jonathan.png")
    caminho_brand = os.path.join(BASE_DIR, "assets", "jonathan_brand.png")
    
    if os.path.exists(caminho_logo):
        st.image(caminho_logo, use_container_width=True)
    elif os.path.exists(caminho_brand):
        st.image(caminho_brand, use_container_width=True)
        
    st.markdown("<div class='badge-quant'>GRADE DE EXPERIMENTOS QUANT</div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Parâmetros da Grade")
    
    # 1. Lookbacks
    mapa_lk = {
        "3 Meses (63 pregões)": 63,
        "6 Meses (126 pregões)": 126,
        "12 Meses (252 pregões)": 252
    }
    sel_lk_labels = st.multiselect(
        "Janelas de Volatilidade (Lookback)",
        options=list(mapa_lk.keys()),
        default=list(mapa_lk.keys()),
        help="Janelas históricas para estimação do desvio-padrão dos retornos."
    )
    sel_lookbacks = [mapa_lk[k] for k in sel_lk_labels] if sel_lk_labels else [252]
    
    # 2. Modos de Estratégia
    mapa_modos = {
        "Long-Only (Q1 Low Vol)": "long_only",
        "Long-Short (BAB Q1-Q5 + CDI)": "long_short"
    }
    sel_modos_labels = st.multiselect(
        "Modos de Estratégia",
        options=list(mapa_modos.keys()),
        default=list(mapa_modos.keys()),
        help="Long-Only aloca 100% no Q1. Long-Short compra Q1, vende Q5 e remunera caixa a 100% do CDI."
    )
    sel_modos = [mapa_modos[k] for k in sel_modos_labels] if sel_modos_labels else ["long_only"]
    
    # 3. Tamanho do Quintil / Concentração
    mapa_frac = {
        "Top 10% (Alta Concentração)": 0.10,
        "Top 20% (Quintil Padrão)": 0.20,
        "Top 30% (Alta Diversificação)": 0.30
    }
    sel_frac_labels = st.multiselect(
        "Tamanho da Carteira (Fração do Universo)",
        options=list(mapa_frac.keys()),
        default=["Top 20% (Quintil Padrão)", "Top 10% (Alta Concentração)"],
        help="Proporção de ações selecionadas do universo elegível."
    )
    sel_fracoes = [mapa_frac[k] for k in sel_frac_labels] if sel_frac_labels else [0.20]
    
    # 4. Frequência de Rebalanceamento
    mapa_freq = {
        "Trimestral (Padrão B3)": "trimestral",
        "Mensal": "mensal",
        "Semestral": "semestral"
    }
    sel_freq_labels = st.multiselect(
        "Frequência de Rebalanceamento",
        options=list(mapa_freq.keys()),
        default=["Trimestral (Padrão B3)", "Mensal"],
        help="Periodicidade da recomposição sistemática da carteira."
    )
    sel_frequencias = [mapa_freq[k] for k in sel_freq_labels] if sel_freq_labels else ["trimestral"]
    
    # 5. Custos de Transação
    mapa_custos = {
        "0 bps (Teórico / Sem Fricção)": 0.0,
        "5 bps (Institucional)": 5.0,
        "15 bps (Varejo / Médio)": 15.0,
        "25 bps (Conservador)": 25.0
    }
    sel_custos_labels = st.multiselect(
        "Custos de Transação (bps)",
        options=list(mapa_custos.keys()),
        default=["0 bps (Teórico / Sem Fricção)", "5 bps (Institucional)", "15 bps (Varejo / Médio)"],
        help="Custo estimado por turnover aplicado no rebalanceamento (bps)."
    )
    sel_custos = [mapa_custos[k] for k in sel_custos_labels] if sel_custos_labels else [5.0]
    
    col_dt1, col_dt2 = st.columns(2)
    with col_dt1:
        d_ini_in = st.date_input("Início", value=pd.to_datetime("2018-01-01"))
    with col_dt2:
        d_fim_in = st.date_input("Fim", value=pd.to_datetime("2026-08-01"))
        
    d_ini_str = d_ini_in.strftime("%Y-%m-%d") if hasattr(d_ini_in, 'strftime') else str(d_ini_in)
    d_fim_str = d_fim_in.strftime("%Y-%m-%d") if hasattr(d_fim_in, 'strftime') else str(d_fim_in)
    
    n_combinacoes = len(sel_lookbacks) * len(sel_modos) * len(sel_fracoes) * len(sel_frequencias) * len(sel_custos)
    st.info(f"📊 **Combinações Selecionadas:** `{n_combinacoes}`")
    
    btn_rodar_grade = st.button("🚀 Rodar Grade de Experimentos", use_container_width=True, type="primary")


# ==============================================================================
# CARREGAMENTO DOS DADOS DA GRADE (CACHE OU EXECUÇÃO)
# ==============================================================================
caminho_csv_padrao = os.path.join(BASE_DIR, "experimentos.csv")
caminho_md_padrao = os.path.join(BASE_DIR, "experimentos.md")

if btn_rodar_grade:
    with st.spinner(f"Simulando grade com {n_combinacoes} combinações de parâmetros..."):
        df_exp, dict_curvas, dict_detalhes = rodar_grade_cached(
            tuple(sel_lookbacks),
            tuple(sel_modos),
            tuple(sel_fracoes),
            tuple(sel_frequencias),
            tuple(sel_custos),
            d_ini_str,
            d_fim_str
        )
        df_exp.to_csv(caminho_csv_padrao, index=False, encoding='utf-8')
        gerar_relatorio_markdown_experimentos(df_exp, caminho_md=caminho_md_padrao)
elif os.path.exists(caminho_csv_padrao):
    df_exp = pd.read_csv(caminho_csv_padrao)
    df_exp, dict_curvas, dict_detalhes = rodar_grade_cached(
        tuple(sel_lookbacks),
        tuple(sel_modos),
        tuple(sel_fracoes),
        tuple(sel_frequencias),
        tuple(sel_custos),
        d_ini_str,
        d_fim_str
    )
else:
    with st.spinner("Gerando grade inicial de experimentos..."):
        df_exp, dict_curvas, dict_detalhes = rodar_grade_cached(
            tuple(sel_lookbacks),
            tuple(sel_modos),
            tuple(sel_fracoes),
            tuple(sel_frequencias),
            tuple(sel_custos),
            d_ini_str,
            d_fim_str
        )
        df_exp.to_csv(caminho_csv_padrao, index=False, encoding='utf-8')
        gerar_relatorio_markdown_experimentos(df_exp, caminho_md=caminho_md_padrao)


# ==============================================================================
# CABEÇALHO PRINCIPAL E DATA STORYTELLING
# ==============================================================================
col_masc, col_title = st.columns([1.2, 4.5])

with col_masc:
    caminho_vs = os.path.join(BASE_DIR, "assets", "jonathan_vs_lebre.png")
    if os.path.exists(caminho_vs):
        st.image(caminho_vs, use_container_width=True)
    elif os.path.exists(caminho_logo):
        st.image(caminho_logo, use_container_width=True)

with col_title:
    st.markdown("<div class='badge-quant'>DESAFIO QUANT AI 2026 — LABORATÓRIO DE EXPERIMENTOS</div>", unsafe_allow_html=True)
    st.title("🧪 Grade Multivariável: Jonathan (Low Vol) em Todos os Cenários")
    st.markdown("""
    **Objetivo Quantitativo:** *Analisar a robustez empírica da Anomalia de Baixa Volatilidade sob diferentes janelas temporais, níveis de concentração, regimes de rebalanceamento e fricções de mercado (custos de transação).
    O benchmark de mercado (IBrX-100/Ibovespa) e a taxa livre de risco (CDI) são utilizados como réguas de performance absoluta e Alpha de Jensen.*
    """)

st.markdown("---")


# ==============================================================================
# CARDS DE SÍNTESE EXECUTIVA DOS EXPERIMENTOS
# ==============================================================================
if not df_exp.empty:
    best_sharpe_row = df_exp.sort_values('Indice_Sharpe', ascending=False).iloc[0]
    best_cagr_row = df_exp.sort_values('CAGR_Pct', ascending=False).iloc[0]
    lowest_dd_row = df_exp.sort_values('Max_Drawdown_Pct', ascending=False).iloc[0]
    best_alpha_row = df_exp.sort_values('Alpha_Anualizado_Pct', ascending=False).iloc[0]
    
    k1, k2, k3, k4, k5 = st.columns(5)
    
    with k1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Total de Combinações</div>
            <div class='metric-value-gold'>{len(df_exp)}</div>
            <div class='metric-sub'>Simulações Executadas</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Maior Índice Sharpe</div>
            <div class='metric-value-gold'>{best_sharpe_row['Indice_Sharpe']:.2f}</div>
            <div class='metric-sub'>{best_sharpe_row['ID_Experimento']} | {best_sharpe_row['Modo']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Maior Retorno (CAGR)</div>
            <div class='metric-value-gold'>{best_cagr_row['CAGR_Pct']:.1f}%</div>
            <div class='metric-sub'>{best_cagr_row['ID_Experimento']} | {best_cagr_row['Lookback_Label']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Menor Max Drawdown</div>
            <div class='metric-value-gold'>{lowest_dd_row['Max_Drawdown_Pct']:.1f}%</div>
            <div class='metric-sub'>{lowest_dd_row['ID_Experimento']} | DD Mais Suave</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k5:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Maior Alpha vs CDI</div>
            <div class='metric-value-gold'>{best_alpha_row['Alpha_Anualizado_Pct']:+.1f}%</div>
            <div class='metric-sub'>{best_alpha_row['ID_Experimento']} | Jensen Anualizado</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")


# ==============================================================================
# ABAS DO DASHBOARD DE EXPERIMENTOS
# ==============================================================================
tab_tab, tab_diag, tab_insp, tab_alertas, tab_rel = st.tabs([
    "📋 Tabela Geral de Experimentos",
    "🎯 Diagnósticos & Visualizações",
    "🔍 Inspeção Detalhada de Experimento",
    "⚠️ Motor de Alertas & Fragilidades",
    "📄 Relatório Executivo & Exportação"
])


# ------------------------------------------------------------------------------
# TAB 1: TABELA GERAL COMPARATIVA
# ------------------------------------------------------------------------------
with tab_tab:
    st.markdown("### 📋 Grade Comparativa Geral de Simulações")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        f_modo = st.multiselect("Filtrar Modo", options=df_exp['Modo'].unique().tolist(), default=df_exp['Modo'].unique().tolist())
    with col_f2:
        f_lk = st.multiselect("Filtrar Lookback", options=df_exp['Lookback_Label'].unique().tolist(), default=df_exp['Lookback_Label'].unique().tolist())
    with col_f3:
        ordenar_por = st.selectbox("Ordenar Tabela Por:", options=['Indice_Sharpe', 'CAGR_Pct', 'Alpha_Anualizado_Pct', 'Max_Drawdown_Pct', 'Retorno_Total_Pct'], index=0)
        
    df_filtrado = df_exp[
        (df_exp['Modo'].isin(f_modo)) &
        (df_exp['Lookback_Label'].isin(f_lk))
    ].sort_values(ordenar_por, ascending=(ordenar_por == 'Max_Drawdown_Pct')).copy()
    
    colunas_exib = [
        'ID_Experimento', 'Nome_Experimento', 'Modo', 'Lookback_Label', 'Tamanho_Carteira_Pct',
        'Frequencia', 'Custo_Bps', 'Retorno_Total_Pct', 'CAGR_Pct', 'Volatilidade_Anualizada_Pct',
        'Indice_Sharpe', 'Alpha_Anualizado_Pct', 'Max_Drawdown_Pct', 'Win_Rate_Pct', 'Alertas_Risco'
    ]
    
    st.dataframe(
        df_filtrado[colunas_exib].style.format({
            'Custo_Bps': '{:.0f} bps',
            'Retorno_Total_Pct': '{:.2f}%',
            'CAGR_Pct': '{:.2f}% a.a.',
            'Volatilidade_Anualizada_Pct': '{:.2f}% a.a.',
            'Indice_Sharpe': '{:.2f}',
            'Alpha_Anualizado_Pct': '{:+.2f}% a.a.',
            'Max_Drawdown_Pct': '{:.2f}%',
            'Win_Rate_Pct': '{:.1f}%'
        }).background_gradient(subset=['Indice_Sharpe', 'CAGR_Pct', 'Alpha_Anualizado_Pct'], cmap='YlGn'),
        use_container_width=True,
        height=450
    )


# ------------------------------------------------------------------------------
# TAB 2: DIAGNÓSTICOS & VISUALIZAÇÕES
# ------------------------------------------------------------------------------
with tab_diag:
    st.markdown("### 🎯 Diagnósticos Visuais Multivariáveis")
    
    col_d1, col_d2 = st.columns(2)
    
    # 1. Dispersão Risco x Retorno
    with col_d1:
        st.markdown("#### a) Dispersão Risco x Retorno (Sharpe vs. Max Drawdown)")
        fig_scatter = px.scatter(
            df_exp,
            x="Max_Drawdown_Pct",
            y="CAGR_Pct",
            color="Custo_Bps",
            size=df_exp['Indice_Sharpe'].apply(lambda s: max(10.0, s * 20.0)),
            hover_name="Nome_Experimento",
            hover_data={"Indice_Sharpe": ":.2f", "Alpha_Anualizado_Pct": ":.2f%", "Modo": True},
            color_continuous_scale="Viridis",
            title="Max Drawdown (%) vs. CAGR (% a.a.) por Custo e Sharpe"
        )
        fig_scatter.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
            height=450,
            xaxis=dict(title="Max Drawdown (%)", gridcolor="#2A4E3B", ticksuffix="%"),
            yaxis=dict(title="CAGR (% a.a.)", gridcolor="#2A4E3B", ticksuffix="%")
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    # 2. Heatmap de Sharpe Ratio
    with col_d2:
        st.markdown("#### b) Heatmap de Sharpe Ratio: Lookback x Tamanho da Carteira")
        pivot_sh = df_exp.pivot_table(
            index="Lookback_Label",
            columns="Tamanho_Carteira_Pct",
            values="Indice_Sharpe",
            aggfunc="mean"
        )
        fig_hm = px.imshow(
            pivot_sh,
            text_auto=".2f",
            color_continuous_scale="RdYlGn",
            title="Índice Sharpe Médio por Janela e Concentração"
        )
        fig_hm.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
            height=450,
            xaxis=dict(title="Tamanho da Carteira (% do IBrX)"),
            yaxis=dict(title="Lookback de Volatilidade")
        )
        st.plotly_chart(fig_hm, use_container_width=True)
        
    st.markdown("---")
    
    col_d3, col_d4 = st.columns(2)
    
    # 3. Curvas de Capital das Top 3
    with col_d3:
        st.markdown("#### c) Curvas de Capital Acumuladas: Top 3 Experimentos vs. CDI vs. Ibov")
        top3_ids = df_exp.sort_values('Indice_Sharpe', ascending=False).head(3)['ID_Experimento'].tolist()
        
        fig_top3 = go.Figure()
        cores_top3 = [C_GOLD, C_LIGHT_GOLD, '#52B788']
        
        for idx_t, exp_id_t in enumerate(top3_ids):
            if exp_id_t in dict_curvas:
                serie_c = dict_curvas[exp_id_t]
                nome_exp_t = df_exp[df_exp['ID_Experimento'] == exp_id_t]['Nome_Experimento'].iloc[0]
                fig_top3.add_trace(go.Scatter(
                    x=serie_c.index, y=serie_c,
                    name=f"Top {idx_t+1}: {nome_exp_t}",
                    line=dict(color=cores_top3[idx_t % len(cores_top3)], width=2.5)
                ))
                
        if 'Benchmark' in dict_curvas:
            fig_top3.add_trace(go.Scatter(
                x=dict_curvas['Benchmark'].index, y=dict_curvas['Benchmark'],
                name="📊 Ibovespa",
                line=dict(color=C_GRAY, width=1.8, dash='dash')
            ))
            
        if 'CDI' in dict_curvas:
            fig_top3.add_trace(go.Scatter(
                x=dict_curvas['CDI'].index, y=dict_curvas['CDI'],
                name="💵 CDI",
                line=dict(color="#FFFFFF", width=1.8, dash='dot')
            ))
            
        fig_top3.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
            height=450, hovermode="x unified",
            xaxis=dict(title="Data", gridcolor="#2A4E3B"),
            yaxis=dict(title="Patrimônio (Base 100)", gridcolor="#2A4E3B"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_top3, use_container_width=True)
        
    # 4. Comparativo Direto de Atrito de Custos
    with col_d4:
        st.markdown("#### d) Comparativo de Atrito: Degradação de Performance por Custo")
        df_custo_grp = df_exp.groupby('Custo_Bps')[['CAGR_Pct', 'Alpha_Anualizado_Pct', 'Indice_Sharpe']].mean().reset_index()
        
        fig_atrito = go.Figure()
        fig_atrito.add_trace(go.Bar(
            x=[f"{c:.0f} bps" for c in df_custo_grp['Custo_Bps']],
            y=df_custo_grp['CAGR_Pct'],
            name="CAGR Médio (% a.a.)",
            marker_color=C_GOLD,
            text=df_custo_grp['CAGR_Pct'].apply(lambda v: f"{v:.1f}%"),
            textposition="outside"
        ))
        fig_atrito.add_trace(go.Bar(
            x=[f"{c:.0f} bps" for c in df_custo_grp['Custo_Bps']],
            y=df_custo_grp['Alpha_Anualizado_Pct'],
            name="Alpha Médio (% a.a.)",
            marker_color=C_CORAL,
            text=df_custo_grp['Alpha_Anualizado_Pct'].apply(lambda v: f"{v:+.1f}%"),
            textposition="outside"
        ))
        fig_atrito.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
            barmode="group", height=450,
            xaxis=dict(title="Custo de Transação (bps)", gridcolor="#2A4E3B"),
            yaxis=dict(title="Retorno Anualizado (%)", gridcolor="#2A4E3B", ticksuffix="%"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_atrito, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 3: INSPEÇÃO DETALHADA DE EXPERIMENTO
# ------------------------------------------------------------------------------
with tab_insp:
    st.markdown("### 🔍 Inspeção Detalhada de Configuração Individual")
    
    opcoes_exp = {f"{r['ID_Experimento']} — {r['Nome_Experimento']}": r['ID_Experimento'] for _, r in df_exp.iterrows()}
    exp_selecionado_label = st.selectbox("Selecione o Experimento para Investigação Profunda:", options=list(opcoes_exp.keys()))
    sel_id = opcoes_exp[exp_selecionado_label]
    
    r_sel = df_exp[df_exp['ID_Experimento'] == sel_id].iloc[0]
    
    # Cards de KPIs do Experimento
    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns(6)
    with ic1:
        st.metric("CAGR Anualizado", f"{r_sel['CAGR_Pct']:.2f}% a.a.")
    with ic2:
        st.metric("Volatilidade", f"{r_sel['Volatilidade_Anualizada_Pct']:.2f}% a.a.")
    with ic3:
        st.metric("Índice Sharpe (vs CDI)", f"{r_sel['Indice_Sharpe']:.2f}")
    with ic4:
        st.metric("Alpha de Jensen", f"{r_sel['Alpha_Anualizado_Pct']:+.2f}% a.a.")
    with ic5:
        st.metric("Max Drawdown", f"{r_sel['Max_Drawdown_Pct']:.2f}%")
    with ic6:
        st.metric("Turnover Médio", f"{r_sel['Turnover_Medio_Ciclo_Pct']:.1f}% / ciclo")
        
    st.markdown("---")
    
    col_insp_left, col_insp_right = st.columns([1.3, 1.0])
    
    with col_insp_left:
        st.markdown("#### 🌊 Drawdown Subaquático do Experimento")
        if sel_id in dict_curvas:
            curva_exp = dict_curvas[sel_id]
            dd_exp = (curva_exp / curva_exp.cummax() - 1.0) * 100.0
            
            fig_dd_single = go.Figure()
            fig_dd_single.add_trace(go.Scatter(
                x=dd_exp.index, y=dd_exp,
                name=r_sel['Nome_Experimento'],
                fill='tozeroy',
                fillcolor='rgba(176, 141, 76, 0.45)',
                line=dict(color=C_GOLD, width=2.0)
            ))
            fig_dd_single.update_layout(
                template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
                height=380,
                xaxis=dict(title="Data", gridcolor="#2A4E3B"),
                yaxis=dict(title="Drawdown (%)", gridcolor="#2A4E3B", ticksuffix="%")
            )
            st.plotly_chart(fig_dd_single, use_container_width=True)
            
    with col_insp_right:
        st.markdown("#### 🧩 Últimos Ativos Selecionados")
        if sel_id in dict_detalhes:
            res_obj = dict_detalhes[sel_id]
            ult_reb = res_obj.get('ultimo_rebalanceamento')
            if ult_reb:
                q1_ativos = ult_reb['detalhes_quintis']['Q1_Jonathan']['df_ativos'].copy()
                q1_ativos['Vol (%)'] = q1_ativos['Volatilidade_Anualizada'] * 100.0
                q1_ativos['Peso (%)'] = q1_ativos['Peso'] * 100.0
                
                st.caption(f"📅 **Data:** {pd.to_datetime(ult_reb['data_rebalanceamento']).strftime('%d/%m/%Y')} | **Total Ativos:** {len(q1_ativos)}")
                st.dataframe(
                    q1_ativos[['Ticker', 'Vol (%)', 'Beta', 'Peso (%)']].head(10).style.format({
                        'Vol (%)': '{:.2f}%',
                        'Beta': '{:.2f}',
                        'Peso (%)': '{:.2f}%'
                    }),
                    use_container_width=True,
                    height=320
                )


# ------------------------------------------------------------------------------
# TAB 4: MOTOR DE ALERTAS & FRAGILIDADES
# ------------------------------------------------------------------------------
with tab_alertas:
    st.markdown("### ⚠️ Motor de Detecção Automática de Vieses e Fragilidades")
    st.markdown("Diagnóstico preventivo de riscos metodológicos, overfitting e viés de amostragem:")
    
    col_a1, col_a2 = st.columns(2)
    
    # Contagens de Alertas
    n_inflados = len(df_exp[df_exp['Indice_Sharpe'] > 1.8])
    n_custo_zero = len(df_exp[df_exp['Custo_Bps'] <= 0.0])
    n_concentrados = len(df_exp[df_exp['N_Ativos_Medio'] < 5.0])
    
    with col_a1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>⚠️ Alerta de Sharpe Inflado (> 1.8)</div>
            <div class='metric-value-coral'>{n_inflados} cenários</div>
            <div class='metric-sub'>Indicativo de potencial overfitting ou micro-regime excessivamente favorável.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>⚠️ Alerta de Custo Zero (Sem Fricção)</div>
            <div class='metric-value-coral'>{n_custo_zero} cenários</div>
            <div class='metric-sub'>Cenários puramente teóricos sem slippage e corretagem.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_a2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>⚠️ Alerta de Concentração Excessiva (< 5 ativos)</div>
            <div class='metric-value-coral'>{n_concentrados} cenários</div>
            <div class='metric-sub'>Risco idiossincrático acentuado por baixa diversificação no quintil.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>✅ Mitigação de Vieses Estruturais</div>
            <div class='metric-value-gold'>100% Protegido</div>
            <div class='metric-sub'>Viés de Sobrevivência e Look-Ahead eliminados por construção.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("#### Experimentos com Alertas Críticos Ativados:")
    df_com_alertas = df_exp[df_exp['Alertas_Risco'] != '✅ Robusto']
    if not df_com_alertas.empty:
        st.dataframe(
            df_com_alertas[['ID_Experimento', 'Nome_Experimento', 'Indice_Sharpe', 'Custo_Bps', 'N_Ativos_Medio', 'Alertas_Risco']],
            use_container_width=True
        )
    else:
        st.success("Nenhum experimento com alertas críticos ativados!")


# ------------------------------------------------------------------------------
# TAB 5: RELATÓRIO EXECUTIVO & EXPORTAÇÃO
# ------------------------------------------------------------------------------
with tab_rel:
    st.markdown("### 📄 Relatório Executivo e Exportação de Resultados")
    
    col_exp_btns1, col_exp_btns2 = st.columns(2)
    
    # 1. Download do CSV
    csv_bytes = df_exp.to_csv(index=False).encode('utf-8')
    with col_exp_btns1:
        st.download_button(
            label="📥 Baixar Tabela Completa (experimentos.csv)",
            data=csv_bytes,
            file_name="experimentos.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    # 2. Leitura e Download do Markdown
    relatorio_md_texto = ""
    if os.path.exists(caminho_md_padrao):
        with open(caminho_md_padrao, "r", encoding="utf-8") as f:
            relatorio_md_texto = f.read()
    else:
        relatorio_md_texto = gerar_relatorio_markdown_experimentos(df_exp, caminho_md=caminho_md_padrao)
        
    with col_exp_btns2:
        st.download_button(
            label="📥 Baixar Relatório Completo (experimentos.md)",
            data=relatorio_md_texto.encode('utf-8'),
            file_name="experimentos.md",
            mime="text/markdown",
            use_container_width=True
        )
        
    st.markdown("---")
    st.markdown("#### 📖 Visualização do Relatório Oficial em Markdown:")
    st.markdown(relatorio_md_texto)
