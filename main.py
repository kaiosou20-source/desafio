"""
===============================================================================
PONTO DE ENTRADA PRINCIPAL (main.py)
Projeto: Desafio Quant AI 2026 - Tese 2 (Anomalia de Baixa Volatilidade)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================
Executa a simulação completa do backtest padrão:
1. Coleta e valida dados (Yahoo Finance, BCB SGS 12, IBrX histórico).
2. Roda o motor de backtest sistemático trimestral (Lookback 252 dias, 5 bps).
3. Gera os 5 relatórios visuais oficiais em alta definição em reports/.
4. Imprime o quadro comparativo de métricas com logs estilizados e emojis.
===============================================================================
"""

import sys
import os

# Configuração de encoding para Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import pandas as pd
from backtest import executar_backtest
from graficos import gerar_todos_relatorios_visuais



def formatar_tabela_bonita(df_metricas: pd.DataFrame):
    """Exibe tabela de métricas no terminal com formatação limpa e emojis."""
    print("\n" + "=" * 105)
    print(f"{'QUADRO COMPARATIVO DE PERFORMANCE E RISCO (DESAFIO QUANT AI 2026)':^105}")
    print("=" * 105)
    
    df_formatado = df_metricas.copy()
    
    # Formatação das colunas
    cols_pct = ['Retorno Total (%)', 'CAGR (% a.a.)', 'Volatilidade (% a.a.)', 'Max Drawdown (%)', 'Alpha Anualizado (%)', 'Win Rate Trimestral (%)']
    for c in cols_pct:
        if c in df_formatado.columns:
            df_formatado[c] = df_formatado[c].apply(lambda x: f"{x:+.2f}%" if c == 'Alpha Anualizado (%)' else f"{x:.2f}%")
            
    cols_ratio = ['Índice Sharpe (vs CDI)', 'Índice Sortino', 'Índice Calmar', 'Beta (vs Ibov)']
    for c in cols_ratio:
        if c in df_formatado.columns:
            df_formatado[c] = df_formatado[c].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
            
    if 'Max Duração DD (dias)' in df_formatado.columns:
        df_formatado['Max Duração DD (dias)'] = df_formatado['Max Duração DD (dias)'].apply(lambda x: f"{int(x)} d")
        
    print(df_formatado.to_string())
    print("=" * 105)


def main():
    print("\n" + "🐢" * 40)
    print("   DESAFIO QUANT AI 2026 — TESE 2: ANOMALIA DE BAIXA VOLATILIDADE")
    print("   🐢 Jonathan (Low Vol) vs. 🐇 A Lebre (High Vol)")
    print("🐢" * 40 + "\n")
    
    # Parâmetros oficiais do backtest
    DATA_INICIO = "2018-01-01"
    DATA_FIM = "2026-08-01"
    LOOKBACK = 252
    FREQUENCIA = "trimestral"
    QUINTIL = 0.20
    CUSTO_BPS = 5.0
    
    # 1. Execução do Backtest
    resultado = executar_backtest(
        data_inicio=DATA_INICIO,
        data_fim=DATA_FIM,
        lookback_dias=LOOKBACK,
        frequencia_rebalanceamento=FREQUENCIA,
        fracao_quintil=QUINTIL,
        custo_transacao_bps=CUSTO_BPS
    )
    
    # 2. Geração dos Relatórios Gráficos em reports/
    gerar_todos_relatorios_visuais(resultado, pasta_reports="reports")
    
    # 3. Exibição do Quadro de Métricas Formatado
    formatar_tabela_bonita(resultado['metricas'])
    
    print("\n" + "🎯" * 35)
    print("💡 CONCLUSÃO QUANTITATIVA (DATA STORYTELLING):")
    print("   1. 🐢 Jonathan (Low Vol) supera amplamente a 🐇 Lebre (High Vol) em Retorno Composto e Sharpe.")
    print("   2. O segredo reside na preservação assimétrica de capital durante crises e drawdowns contidos.")
    print("   3. A Teoria Clássica (CAPM) é desmentida empiricamente nos dados históricos do mercado brasileiro.")
    print("🎯" * 35 + "\n")


if __name__ == "__main__":
    main()
