import os
import sys
import pandas as pd
from datetime import datetime

# Garante stdout não-bufferizado e utf-8
sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

import backtest

print("=" * 80)
print("🚀 MOTOR DE EXPERIMENTOS QUANTITATIVOS: GRADE MULTIVARIÁVEL (JONATHAN)")
print("=" * 80)

# Grade representativa e rápida (36 combinações abrangentes)
lista_lookbacks = [63, 126, 252]
lista_modos = ['long_only', 'long_short']
lista_fracoes = [0.10, 0.20, 0.30]
lista_frequencias = ['trimestral', 'mensal']
lista_custos = [0.0, 5.0, 15.0, 25.0]

def log_progresso(idx, total, nome):
    if idx % 10 == 0 or idx == total or idx == 1:
        print(f"[{idx:03d}/{total:03d}] {nome}")

df_exp, dict_curvas, dict_detalhes = backtest.executar_grade_experimentos(
    lista_lookbacks=lista_lookbacks,
    lista_modos=lista_modos,
    lista_fracoes=lista_fracoes,
    lista_frequencias=lista_frequencias,
    lista_custos=lista_custos,
    callback_progresso=log_progresso
)

caminho_csv = "experimentos.csv"
df_exp.to_csv(caminho_csv, index=False, encoding='utf-8')
print(f"✅ Grade concluída: {len(df_exp)} experimentos salvos em '{caminho_csv}'.")

caminho_md = "experimentos.md"
relatorio_md = backtest.gerar_relatorio_markdown_experimentos(df_exp, caminho_md=caminho_md)
print(f"✅ Relatório executivo gerado com sucesso em '{caminho_md}'.")
print("=" * 80)
