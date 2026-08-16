"""
===============================================================================
DASHBOARD INTERATIVO QUANTITATIVO (dashboard.py)
Projeto: Desafio Quant AI 2026 - Anomalia de Baixa Volatilidade (Low Volatility Anomaly)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================

Aplicação Streamlit com tema escuro personalizado (#1F3B2C, #B08D4C, #D9D9D9):
- Header com o Mascote Oficial Jonathan e storytelling do Desafio Quant AI 2026.
- Controles interativos na barra lateral (lookback, rebalanceamento, custos, datas).
- Cards com KPIs comparativos de performance e risco.
- Gráficos interativos em Plotly (Curva de Capital, Drawdown, Quintis, Heatmap).
- Composição detalhada da carteira e botão de exportação em CSV.
===============================================================================
"""

import os
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from backtest import executar_backtest
from dados import carregar_composicao_ibrx

# Configuração da Página
st.set_page_config(
    page_title="Desafio Quant AI 2026 — Jonathan (Low Vol)",
    page_icon="🐢",
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
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin-bottom: 12px;
    }}
    .metric-title {{
        color: {C_MUTED};
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }}
    .metric-value-gold {{
        color: {C_LIGHT_GOLD};
        font-size: 1.6rem;
        font-weight: 800;
    }}
    .metric-value-coral {{
        color: {C_CORAL};
        font-size: 1.6rem;
        font-weight: 800;
    }}
    .metric-value-gray {{
        color: {C_GRAY};
        font-size: 1.6rem;
        font-weight: 800;
    }}
    .metric-sub {{
        font-size: 0.8rem;
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
# BARRA LATERAL (CONTROLES E PARÂMETROS)
# ==============================================================================
with st.sidebar:
    # Mascote na barra lateral se existir
    if os.path.exists("assets/jonathan.png"):
        st.image("assets/jonathan.png", use_container_width=True)
    elif os.path.exists("assets/jonathan_brand.png"):
        st.image("assets/jonathan_brand.png", use_container_width=True)
        
    st.markdown("<div class='badge-quant'>DESAFIO QUANT AI 2026</div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Parâmetros do Modelo")
    
    col_dt1, col_dt2 = st.columns(2)
    with col_dt1:
        data_ini_input = st.date_input("Início", value=pd.to_datetime("2018-01-01"))
    with col_dt2:
        data_fim_input = st.date_input("Fim", value=pd.to_datetime("2026-08-01"))
        
    lookback = st.slider("Lookback Volatilidade (Pregões)", min_value=63, max_value=504, value=252, step=21,
                         help="Janela móvel de cálculo do desvio-padrão (252 pregões = 12 meses).")
    
    freq = st.selectbox("Frequência de Rebalanceamento", options=["trimestral", "mensal", "semestral", "anual"], index=0,
                        help="Rebalanceamento sistemático com dados fechados no último pregão do ciclo.")
    
    fracao = st.slider("Tamanho do Quintil (%)", min_value=10, max_value=30, value=20, step=5,
                       help="Proporção de ações selecionadas em cada extremo (20% = Quintil clássico).") / 100.0
    
    custos = st.number_input("Custos de Transação (bps)", min_value=0.0, max_value=50.0, value=5.0, step=1.0,
                             help="Custo estimado de corretagem/slippage por turnover em pontos-base (5 bps = 0.05%).")
    
    btn_rodar = st.button("🚀 Executar Backtest", use_container_width=True, type="primary")
    
    st.markdown("---")
    st.markdown("""
    **Anomalia de Baixa Volatilidade (Low Volatility Anomaly)**
    *Betting Against Beta — Empiricamente, ativos de menor volatilidade entregam retornos superiores ajustados ao risco no longo prazo, desafiando a premissa clássica da relação risco-retorno do CAPM.*
    """)


# ==============================================================================
# EXECUÇÃO DO BACKTEST (COM CACHE STREAMLIT)
# ==============================================================================
@st.cache_data(show_spinner="Calculando simulação quantitativa...")
def rodar_backtest_cached(d_ini, d_fim, lk, fq, fr, cst):
    return executar_backtest(
        data_inicio=d_ini,
        data_fim=d_fim,
        lookback_dias=lk,
        frequencia_rebalanceamento=fq,
        fracao_quintil=fr,
        custo_transacao_bps=cst
    )

res = rodar_backtest_cached(
    str(data_ini_input),
    str(data_fim_input),
    lookback,
    freq,
    fracao,
    custos
)

curvas = res['curvas_capital']
metricas = res['metricas']
ret_diarios = res['retornos_diarios']
ret_mensais_j = res['retornos_mensais_jonathan']
ultimo_reb = res['ultimo_rebalanceamento']


# ==============================================================================
# CABEÇALHO PRINCIPAL E DATA STORYTELLING
# ==============================================================================
col_masc, col_title = st.columns([1.2, 4.5])

with col_masc:
    if os.path.exists("assets/jonathan_vs_lebre.png"):
        st.image("assets/jonathan_vs_lebre.png", use_container_width=True)
    elif os.path.exists("assets/jonathan.png"):
        st.image("assets/jonathan.png", use_container_width=True)

with col_title:
    st.markdown("<div class='badge-quant'>ANOMALIA DE BAIXA VOLATILIDADE (LOW VOLATILITY ANOMALY)</div>", unsafe_allow_html=True)
    st.title("🐢 Jonathan (Low Vol) vs. 🐇 A Lebre (High Vol)")
    st.markdown("""
    **Metáfora Central:** *Jonathan, a tartaruga de quase dois séculos, sobreviveu a guerras e crises não por ser veloz, mas por nunca correr riscos desnecessários.
    No mercado acionário brasileiro (IBrX-100), o controle estrito de drawdowns e a consistência superam a volatilidade e compõem capital superior no longo prazo.*
    """)


st.markdown("---")

# ==============================================================================
# CARDS DE KPIS COMPARATIVOS
# ==============================================================================
st.markdown("### 🏆 Confronto Direto de Performance e Risco")

c1, c2, c3, c4, c5, c6 = st.columns(6)

# Extrai métricas
m_j = metricas.loc['🐢 Q1 - Jonathan (Low Vol)']
m_l = metricas.loc['🐇 Q5 - A Lebre (High Vol)']
m_b = metricas.loc['📊 Benchmark (Ibovespa)']
m_cdi = metricas.loc['💵 Taxa Livre de Risco (CDI)']

with c1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>CAGR (Retorno Anual)</div>
        <div class='metric-value-gold'>{m_j['CAGR (% a.a.)']:.1f}%</div>
        <div class='metric-sub'>🐇 Lebre: {m_l['CAGR (% a.a.)']:.1f}% | 📊 Ibov: {m_b['CAGR (% a.a.)']:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Volatilidade Anualizada</div>
        <div class='metric-value-gold'>{m_j['Volatilidade (% a.a.)']:.1f}%</div>
        <div class='metric-sub'>🐇 Lebre: {m_l['Volatilidade (% a.a.)']:.1f}% | 📊 Ibov: {m_b['Volatilidade (% a.a.)']:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Índice Sharpe (vs CDI)</div>
        <div class='metric-value-gold'>{m_j['Índice Sharpe (vs CDI)']:.2f}</div>
        <div class='metric-sub'>🐇 Lebre: {m_l['Índice Sharpe (vs CDI)']:.2f} | 📊 Ibov: {m_b['Índice Sharpe (vs CDI)']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Max Drawdown</div>
        <div class='metric-value-gold'>{m_j['Max Drawdown (%)']:.1f}%</div>
        <div class='metric-sub'>🐇 Lebre: {m_l['Max Drawdown (%)']:.1f}% | 📊 Ibov: {m_b['Max Drawdown (%)']:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Índice Sortino</div>
        <div class='metric-value-gold'>{m_j['Índice Sortino']:.2f}</div>
        <div class='metric-sub'>🐇 Lebre: {m_l['Índice Sortino']:.2f} | 📊 Ibov: {m_b['Índice Sortino']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Alpha de Jensen</div>
        <div class='metric-value-gold'>{m_j['Alpha Anualizado (%)']:+.1f}%</div>
        <div class='metric-sub'>Beta: {m_j['Beta (vs Ibov)']:.2f} | Win Rate: {m_j['Win Rate Trimestral (%)']:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# ABAS INTERATIVAS DE VISUALIZAÇÃO
# ==============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Curva de Capital",
    "🌊 Drawdown Subaquático",
    "📊 Análise dos 5 Quintis",
    "🗓️ Heatmap Mensal",
    "🧩 Carteira Atual",
    "📜 Rebalanceamentos & Exportação"
])

# ------------------------------------------------------------------------------
# TAB 1: CURVA DE CAPITAL
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("#### Evolução do Patrimônio Acumulado (Base 100)")
    
    col_escala, _ = st.columns([2, 5])
    with col_escala:
        tipo_escala = st.radio("Escala do Eixo Y:", ["Linear", "Logarítmica"], horizontal=True)
        
    fig_curva = go.Figure()
    
    fig_curva.add_trace(go.Scatter(
        x=curvas.index, y=curvas['Q1_Jonathan'],
        name='🐢 Q1 - Jonathan (Low Vol)',
        line=dict(color=C_GOLD, width=3.2),
        hovertemplate='<b>🐢 Jonathan</b>: R$ %{y:,.2f}<extra></extra>'
    ))
    
    fig_curva.add_trace(go.Scatter(
        x=curvas.index, y=curvas['Benchmark'],
        name='📊 Benchmark (Ibovespa)',
        line=dict(color=C_GRAY, width=2.0, dash='dash'),
        hovertemplate='<b>📊 Ibovespa</b>: R$ %{y:,.2f}<extra></extra>'
    ))
    
    fig_curva.add_trace(go.Scatter(
        x=curvas.index, y=curvas['CDI'],
        name='💵 CDI (Taxa Livre de Risco)',
        line=dict(color="#FFFFFF", width=2.0, dash='dot'),
        hovertemplate='<b>💵 CDI</b>: R$ %{y:,.2f}<extra></extra>'
    ))
    
    fig_curva.add_trace(go.Scatter(
        x=curvas.index, y=curvas['Q5_Lebre'],
        name='🐇 Q5 - A Lebre (High Vol)',
        line=dict(color=C_CORAL, width=2.2),
        hovertemplate='<b>🐇 A Lebre</b>: R$ %{y:,.2f}<extra></extra>'
    ))
    
    fig_curva.update_layout(
        template="plotly_dark",
        paper_bgcolor=C_BG,
        plot_bgcolor=C_CARD,
        hovermode="x unified",
        margin=dict(l=40, r=40, t=20, b=40),
        height=550,
        yaxis_type="log" if tipo_escala == "Logarítmica" else "linear",
        yaxis=dict(gridcolor="#2A4E3B", title="Valor do Portfólio (R$)"),
        xaxis=dict(gridcolor="#2A4E3B", title="Data"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(31, 59, 44, 0.8)",
            bordercolor=C_GOLD,
            borderwidth=1
        )
    )
    st.plotly_chart(fig_curva, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: DRAWDOWN SUBAQUÁTICO
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("#### Rebaixamento a partir da Máxima Histórica (Drawdown Subaquático)")
    
    dd_j = (curvas['Q1_Jonathan'] / curvas['Q1_Jonathan'].cummax() - 1.0) * 100.0
    dd_l = (curvas['Q5_Lebre'] / curvas['Q5_Lebre'].cummax() - 1.0) * 100.0
    dd_b = (curvas['Benchmark'] / curvas['Benchmark'].cummax() - 1.0) * 100.0
    
    fig_dd = go.Figure()
    
    fig_dd.add_trace(go.Scatter(
        x=curvas.index, y=dd_l,
        name='🐇 A Lebre (High Vol)',
        fill='tozeroy',
        fillcolor='rgba(231, 111, 81, 0.25)',
        line=dict(color=C_CORAL, width=1.5),
        hovertemplate='<b>🐇 Lebre DD</b>: %{y:.2f}%<extra></extra>'
    ))
    
    fig_dd.add_trace(go.Scatter(
        x=curvas.index, y=dd_b,
        name='📊 Ibovespa',
        fill='tozeroy',
        fillcolor='rgba(217, 217, 217, 0.15)',
        line=dict(color=C_GRAY, width=1.5, dash='dash'),
        hovertemplate='<b>📊 Ibov DD</b>: %{y:.2f}%<extra></extra>'
    ))
    
    fig_dd.add_trace(go.Scatter(
        x=curvas.index, y=dd_j,
        name='🐢 Jonathan (Low Vol)',
        fill='tozeroy',
        fillcolor='rgba(176, 141, 76, 0.45)',
        line=dict(color=C_GOLD, width=2.5),
        hovertemplate='<b>🐢 Jonathan DD</b>: %{y:.2f}%<extra></extra>'
    ))
    
    fig_dd.update_layout(
        template="plotly_dark",
        paper_bgcolor=C_BG,
        plot_bgcolor=C_CARD,
        hovermode="x unified",
        margin=dict(l=40, r=40, t=20, b=40),
        height=500,
        yaxis=dict(gridcolor="#2A4E3B", title="Drawdown (%)", ticksuffix="%"),
        xaxis=dict(gridcolor="#2A4E3B", title="Data"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(31, 59, 44, 0.8)",
            bordercolor=C_GOLD,
            borderwidth=1
        )
    )
    st.plotly_chart(fig_dd, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: ANÁLISE DOS 5 QUINTIS
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("#### Quebra Empírica do CAPM: Risco vs. Retorno nos 5 Quintis")
    
    col_q_left, col_q_right = st.columns(2)
    
    colunas_q = ['Q1_Jonathan', 'Q2', 'Q3', 'Q4', 'Q5_Lebre']
    nomes_q = ['Q1 (Jonathan)', 'Q2', 'Q3', 'Q4', 'Q5 (Lebre)']
    cores_q = [C_GOLD, '#3A6B52', '#5B8C74', '#99855B', C_CORAL]
    
    n_preg = len(curvas)
    anos = n_preg / 252.0
    cagr_cdi = ((curvas['CDI'].iloc[-1] / curvas['CDI'].iloc[0]) ** (1.0 / anos) - 1.0) * 100.0
    
    vols_q, cagrs_q, sharpes_q, betas_q = [], [], [], []
    for q in colunas_q:
        cg = ((curvas[q].iloc[-1] / curvas[q].iloc[0]) ** (1.0 / anos) - 1.0) * 100.0
        ret_d = curvas[q].pct_change().dropna()
        vl = ret_d.std() * np.sqrt(252) * 100.0
        sh = (cg - cagr_cdi) / vl if vl > 0 else 0.0
        b_ret = curvas['Benchmark'].pct_change().dropna()
        bt = ret_d.cov(b_ret) / b_ret.var()
        
        vols_q.append(vl)
        cagrs_q.append(cg)
        sharpes_q.append(sh)
        betas_q.append(bt)
        
    df_plot_q = pd.DataFrame({
        'Quintil': nomes_q,
        'Volatilidade': vols_q,
        'CAGR': cagrs_q,
        'Sharpe': sharpes_q,
        'Beta': betas_q,
        'Cor': cores_q
    })
    
    with col_q_left:
        fig_disp = px.scatter(
            df_plot_q, x='Volatilidade', y='CAGR', text='Quintil', size=[25]*5,
            color='Quintil', color_discrete_sequence=cores_q,
            title="Dispersão Empírica: Volatilidade vs. CAGR"
        )
        fig_disp.update_traces(textposition='top center')
        fig_disp.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
            height=450, showlegend=False,
            xaxis=dict(title="Volatilidade Anualizada (%)", gridcolor="#2A4E3B", ticksuffix="%"),
            yaxis=dict(title="CAGR (%)", gridcolor="#2A4E3B", ticksuffix="%")
        )
        st.plotly_chart(fig_disp, use_container_width=True)
        
    with col_q_right:
        fig_bar_sh = px.bar(
            df_plot_q, x='Quintil', y='Sharpe', color='Quintil',
            color_discrete_sequence=cores_q,
            text=df_plot_q['Sharpe'].apply(lambda x: f"{x:.2f}"),
            title="Índice de Sharpe (vs. CDI) por Quintil"
        )
        fig_bar_sh.update_traces(textposition='outside')
        fig_bar_sh.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
            height=450, showlegend=False,
            xaxis=dict(title="", gridcolor="#2A4E3B"),
            yaxis=dict(title="Sharpe Ratio", gridcolor="#2A4E3B")
        )
        st.plotly_chart(fig_bar_sh, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 4: HEATMAP MENSAL
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("#### Matriz de Retornos Mensais e Anuais — 🐢 Jonathan (Low Vol)")
    
    st.dataframe(
        ret_mensais_j.style.background_gradient(
            cmap="RdYlGn",
            vmin=-10,
            vmax=10
        ).format("{:.2f}%"),
        use_container_width=True
    )

# ------------------------------------------------------------------------------
# TAB 5: CARTEIRA ATUAL
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("#### Ativos Selecionados no Último Rebalanceamento")
    if ultimo_reb:
        d_reb_str = pd.to_datetime(ultimo_reb['data_rebalanceamento']).strftime('%d/%m/%Y')
        st.info(f"📅 **Data de Rebalanceamento:** {d_reb_str} | **Lookback:** {lookback} pregões")
        
        df_q1_ativos = ultimo_reb['detalhes_quintis']['Q1_Jonathan']['df_ativos'].copy()
        df_q1_ativos['Volatilidade (%)'] = df_q1_ativos['Volatilidade_Anualizada'] * 100.0
        df_q1_ativos['Peso (%)'] = df_q1_ativos['Peso'] * 100.0
        
        col_t_left, col_t_right = st.columns([1.5, 1])
        
        with col_t_left:
            st.dataframe(
                df_q1_ativos[['Ticker', 'Volatilidade (%)', 'Beta', 'Peso (%)']].style.format({
                    'Volatilidade (%)': '{:.2f}%',
                    'Beta': '{:.2f}',
                    'Peso (%)': '{:.2f}%'
                }),
                use_container_width=True
            )
            
        with col_t_right:
            fig_bar_ativos = px.bar(
                df_q1_ativos.sort_values('Volatilidade (%)'),
                x='Volatilidade (%)', y='Ticker', orientation='h',
                color_discrete_sequence=[C_GOLD],
                title="Volatilidade Individual dos Ativos"
            )
            fig_bar_ativos.update_layout(
                template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_CARD,
                height=450,
                xaxis=dict(title="Vol Anual (%)", gridcolor="#2A4E3B", ticksuffix="%"),
                yaxis=dict(title="")
            )
            st.plotly_chart(fig_bar_ativos, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 6: HISTÓRICO DE REBALANCEAMENTOS & EXPORTAÇÃO CSV
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("#### Tabela Comparativa de Métricas & Exportação")
    
    st.dataframe(metricas.style.format({
        'Retorno Total (%)': '{:.2f}%',
        'CAGR (% a.a.)': '{:.2f}%',
        'Volatilidade (% a.a.)': '{:.2f}%',
        'Índice Sharpe (vs CDI)': '{:.2f}',
        'Índice Sortino': '{:.2f}',
        'Índice Calmar': '{:.2f}',
        'Max Drawdown (%)': '{:.2f}%',
        'Max Duração DD (dias)': '{:.0f}',
        'Beta (vs Ibov)': '{:.2f}',
        'Alpha Anualizado (%)': '{:+.2f}%',
        'Win Rate Trimestral (%)': '{:.1f}%'
    }), use_container_width=True)
    
    st.markdown("---")
    st.markdown("#### 📥 Exportar Resultados Diários do Backtest")
    
    # Prepara CSV combinado para download
    df_export = pd.concat([
        curvas.add_prefix("Curva_Capital_"),
        ret_diarios.add_prefix("Retorno_Diario_")
    ], axis=1)
    
    csv_bytes = df_export.to_csv().encode('utf-8')
    
    st.download_button(
        label="📥 Baixar Série Temporal Completa em CSV",
        data=csv_bytes,
        file_name="desafio_quant_2026_jonathan_backtest.csv",
        mime="text/csv",
        use_container_width=True
    )
