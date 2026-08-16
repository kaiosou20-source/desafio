"""
===============================================================================
MÓDULO DE DADOS QUANTITATIVOS (dados.py)
Projeto: Desafio Quant AI 2026 - Tese 2 (Anomalia de Baixa Volatilidade)
Mascote: Jonathan, o Robô-Tartaruga Quant (Q1) vs. A Lebre (Q5)
===============================================================================
Este módulo é responsável pela ingestão, higienização, validação e cache dos dados:
1. Séries históricas de preços diários ajustados via Yahoo Finance (yfinance).
2. Taxa livre de risco diária (CDI) via API oficial do Banco Central do Brasil (SGS 12).
3. Benchmark de mercado (Ibovespa / IBrX via ticker ^BVSP).
4. Universo histórico reconstituído do IBrX-100 para eliminação do viés de sobrevivência.
5. Calendário de dias úteis da B3 e datas pontuais de rebalanceamento sistemático.
===============================================================================
"""

import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import requests
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import List, Tuple, Optional



def formatar_ticker_b3(ticker: str) -> str:
    """
    Padroniza o ticker para a convenção do Yahoo Finance adicionando o sufixo '.SA'.
    Exemplo: 'PETR4' -> 'PETR4.SA', 'VALE3.SA' -> 'VALE3.SA'
    """
    ticker_limpo = ticker.strip().upper()
    if not ticker_limpo.endswith('.SA') and not ticker_limpo.startswith('^'):
        return f"{ticker_limpo}.SA"
    return ticker_limpo


def carregar_composicao_ibrx(caminho_csv: str = "data/ibrx_composicao_historica.csv") -> pd.DataFrame:
    """
    Carrega o arquivo histórico de composição do IBrX-100 por data de corte.
    
    Garante que em cada momento do tempo (rebalanceamento) utilizemos APENAS os ativos
    que de fato compunham o índice naquele trimestre, mitigando viés de sobrevivência
    (survivorship bias).
    """
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(
            f"❌ Arquivo de composição histórica não encontrado em '{caminho_csv}'. "
            "Certifique-se de que a base histórica do IBrX-100 esteja presente."
        )
    
    df = pd.read_csv(caminho_csv)
    df['data_rebalanceamento'] = pd.to_datetime(df['data_rebalanceamento'])
    df['ticker'] = df['ticker'].apply(formatar_ticker_b3)
    return df


def obter_universo_valido(data_corte: pd.Timestamp, df_composicao: pd.DataFrame) -> List[str]:
    """
    Retorna a lista de tickers elegíveis do IBrX-100 disponíveis na data de corte mais
    recente anterior ou igual à data de rebalanceamento.
    """
    datas_disponiveis = df_composicao[df_composicao['data_rebalanceamento'] <= data_corte]['data_rebalanceamento']
    if datas_disponiveis.empty:
        # Se for anterior à primeira data registrada, pega a primeira disponível
        data_referencia = df_composicao['data_rebalanceamento'].min()
    else:
        data_referencia = datas_disponiveis.max()
        
    filtro = df_composicao['data_rebalanceamento'] == data_referencia
    tickers = df_composicao.loc[filtro, 'ticker'].unique().tolist()
    return tickers


def baixar_cdi_bcb(
    data_inicio: str = "2015-01-01",
    data_fim: str = "2026-08-01",
    caminho_cache: str = "data/cdi_cache.csv"
) -> pd.Series:
    """
    Baixa a série histórica da taxa CDI diária diretamente da API do SGS (Sistema Gerenciador de Séries Temporais)
    do Banco Central do Brasil (Série 12: Taxa de juros - CDI diária em % ao dia).
    
    Implementa cache local e download em blocos temporais para máxima robustez e performance.
    Retorna uma pd.Series de retornos decimais diários (ex.: 0.04% a.d. -> 0.0004).
    """
    os.makedirs(os.path.dirname(caminho_cache), exist_ok=True)
    
    # 1. Verifica cache local
    if os.path.exists(caminho_cache):
        try:
            df_cache = pd.read_csv(caminho_cache, parse_dates=['data'])
            df_cache.set_index('data', inplace=True)
            serie_cdi = df_cache['retorno_cdi_diario']
            
            dt_inicio_req = pd.to_datetime(data_inicio)
            dt_fim_req = pd.to_datetime(data_fim)
            if serie_cdi.index.min() <= dt_inicio_req and serie_cdi.index.max() >= (dt_fim_req - pd.Timedelta(days=7)):
                print(f"💵 [Cache CDI] Carregada série do CDI do cache local ({len(serie_cdi)} pregões).")
                return serie_cdi
        except Exception as e:
            print(f"⚠️ Erro ao ler cache do CDI ({e}). Atualizando via API do BCB...")

    print(f"🌐 Baixando taxa livre de risco (CDI diário - SGS 12) da API do Banco Central ({data_inicio} a {data_fim})...")
    
    ano_ini = pd.to_datetime(data_inicio).year
    ano_fim = pd.to_datetime(data_fim).year
    
    # Divide em lotes de até 3 anos para evitar timeout na API do BCB
    lotes_anos = []
    curr = ano_ini
    while curr <= ano_fim:
        fim_bloco = min(curr + 2, ano_fim)
        lotes_anos.append((curr, fim_bloco))
        curr = fim_bloco + 1
        
    todos_dados = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DesafioQuantAI/2026"}
    
    for a_ini, a_fim in lotes_anos:
        d_i_str = f"01/01/{a_ini}"
        d_f_str = f"31/12/{a_fim}"
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={d_i_str}&dataFinal={d_f_str}"
        
        sucesso = False
        for tentativa in range(3):
            try:
                resp = requests.get(url, headers=headers, timeout=45)
                if resp.status_code == 200:
                    dados_lote = resp.json()
                    todos_dados.extend(dados_lote)
                    sucesso = True
                    break
            except Exception:
                pass
                
        if not sucesso:
            print(f"   ⚠️ Falha ao obter bloco do CDI {a_ini}-{a_fim}.")

    if not todos_dados:
        if os.path.exists(caminho_cache):
            print("🔄 Utilizando versão prévia do cache local do CDI.")
            df_cache = pd.read_csv(caminho_cache, parse_dates=['data'])
            df_cache.set_index('data', inplace=True)
            return df_cache['retorno_cdi_diario']
        else:
            raise RuntimeError("❌ Impossível obter a série do CDI da API do BCB e não há cache local disponível.")
            
    df_cdi = pd.DataFrame(todos_dados)
    df_cdi.drop_duplicates(subset=['data'], inplace=True)
    df_cdi['data'] = pd.to_datetime(df_cdi['data'], format='%d/%m/%Y')
    df_cdi['taxa_pct'] = pd.to_numeric(df_cdi['valor'], errors='coerce')
    df_cdi['retorno_cdi_diario'] = df_cdi['taxa_pct'] / 100.0
    
    df_cdi.dropna(subset=['retorno_cdi_diario'], inplace=True)
    df_cdi.sort_values('data', inplace=True)
    df_cdi.set_index('data', inplace=True)
    
    # Salva no cache local
    df_cdi[['retorno_cdi_diario']].to_csv(caminho_cache)
    print(f"✅ [CDI BCB] Ingestão concluída com sucesso: {len(df_cdi)} registros salvos em '{caminho_cache}'.")
    return df_cdi['retorno_cdi_diario']



def baixar_cotacoes_ativos(
    tickers: List[str],
    data_inicio: str = "2015-01-01",
    data_fim: str = "2026-08-01",
    caminho_cache: str = "data/cotacoes_cache.parquet",
    forcar_download: bool = False
) -> pd.DataFrame:
    """
    Baixa os preços históricos de fechamento ajustados (auto_adjust=True) para o universo
    de ações via Yahoo Finance.
    
    Implementa:
    - Armazenamento em formato Parquet para alta performance.
    - Suporte a cache incremental / completo.
    - Tratamento de colunas MultiIndex e limpeza de dados nulos.
    """
    os.makedirs(os.path.dirname(caminho_cache), exist_ok=True)
    tickers_formatados = sorted(list(set([formatar_ticker_b3(t) for t in tickers])))
    
    # Checa existência de cache
    if os.path.exists(caminho_cache) and not forcar_download:
        try:
            df_cached = pd.read_parquet(caminho_cache)
            colunas_presentes = set(df_cached.columns)
            tickers_faltantes = [t for t in tickers_formatados if t not in colunas_presentes]
            
            # Se faltam poucos tickers, podemos usar o que temos ou baixar apenas os faltantes
            if len(tickers_faltantes) == 0:
                print(f"📦 [Cache Preços] Carregados {df_cached.shape[1]} ativos ({df_cached.shape[0]} pregões) do cache local.")
                return df_cached
            else:
                print(f"ℹ️ Cache contém {len(colunas_presentes)} ativos. Baixando {len(tickers_faltantes)} ativos complementares...")
                df_novos = _download_yfinance_batch(tickers_faltantes, data_inicio, data_fim)
                df_combinado = pd.concat([df_cached, df_novos], axis=1)
                df_combinado = df_combinado.loc[:, ~df_combinado.columns.duplicated()]
                df_combinado.sort_index(inplace=True)
                df_combinado.to_parquet(caminho_cache)
                return df_combinado
        except Exception as e:
            print(f"⚠️ Erro ao ler cache Parquet ({e}). Baixando base completa do Yahoo Finance...")

    print(f"🚀 Baixando cotações ajustadas de {len(tickers_formatados)} ativos do Yahoo Finance ({data_inicio} até {data_fim})...")
    df_precos = _download_yfinance_batch(tickers_formatados, data_inicio, data_fim)
    
    # Salva no cache
    df_precos.to_parquet(caminho_cache)
    print(f"✅ Preços salvos em '{caminho_cache}'. Dimensão: {df_precos.shape}")
    return df_precos


def _download_yfinance_batch(
    tickers: List[str],
    data_inicio: str,
    data_fim: str,
    batch_size: int = 40
) -> pd.DataFrame:
    """
    Função auxiliar que baixa tickers em lotes para evitar sobrecarga ou bloqueio da API.
    """
    dfs = []
    for i in range(0, len(tickers), batch_size):
        lote = tickers[i:i + batch_size]
        print(f"   📥 Baixando lote {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1} ({len(lote)} ativos)...")
        try:
            dados = yf.download(
                lote,
                start=data_inicio,
                end=data_fim,
                auto_adjust=True,
                progress=False,
                threads=False
            )
            
            if isinstance(dados.columns, pd.MultiIndex):
                if 'Close' in dados.columns.levels[0]:
                    df_close = dados['Close'].copy()
                else:
                    df_close = dados.xs('Close', axis=1, level=0).copy()
            else:
                df_close = dados[['Close']].copy()
                if len(lote) == 1:
                    df_close.columns = [lote[0]]
            
            dfs.append(df_close)
        except Exception as err:
            print(f"   ⚠️ Erro ao baixar lote: {err}. Tentando download individual...")
            for ticker in lote:
                try:
                    t_data = yf.download(ticker, start=data_inicio, end=data_fim, auto_adjust=True, progress=False, threads=False)
                    if not t_data.empty:
                        close_col = t_data['Close']
                        if isinstance(close_col, pd.DataFrame):
                            close_col = close_col.iloc[:, 0]
                        close_col.name = ticker
                        dfs.append(close_col.to_frame())
                except Exception:
                    pass

    if not dfs:
        raise RuntimeError("❌ Nenhum dado pôde ser baixado do Yahoo Finance. Verifique a conexão com a internet.")
        
    resultado = pd.concat(dfs, axis=1)
    resultado = resultado.loc[:, ~resultado.columns.duplicated()]
    resultado.sort_index(inplace=True)
    return resultado


def baixar_benchmark(
    ticker: str = "^BVSP",
    data_inicio: str = "2015-01-01",
    data_fim: str = "2026-08-01",
    caminho_cache: str = "data/benchmark_cache.csv"
) -> pd.Series:
    """
    Baixa a série de preços do benchmark de mercado (Ibovespa / IBrX proxy).
    """
    os.makedirs(os.path.dirname(caminho_cache), exist_ok=True)
    
    if os.path.exists(caminho_cache):
        try:
            df_bench = pd.read_csv(caminho_cache, parse_dates=['Date'])
            df_bench.set_index('Date', inplace=True)
            print(f"📊 [Cache Benchmark] Carregado {ticker} do cache ({len(df_bench)} pregões).")
            return df_bench['Benchmark']
        except Exception:
            pass

    print(f"📊 Baixando série histórica do Benchmark ({ticker}) do Yahoo Finance...")
    dados = yf.download(ticker, start=data_inicio, end=data_fim, auto_adjust=True, progress=False, threads=False)
    if isinstance(dados.columns, pd.MultiIndex):
        serie = dados['Close'].iloc[:, 0]
    else:
        serie = dados['Close']
        
    serie.name = "Benchmark"
    df_save = serie.to_frame()
    df_save.to_csv(caminho_cache)
    return serie


def calcular_retornos_diarios(precos_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula os retornos aritméticos diários: R_t = (P_t / P_{t-1}) - 1.
    """
    retornos = precos_df.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    return retornos


def obter_datas_rebalanceamento(
    datas_disponiveis: pd.DatetimeIndex,
    frequencia: str = "trimestral"
) -> List[pd.Timestamp]:
    """
    Gera a lista de datas de rebalanceamento a partir do calendário real de negociação da B3.
    
    Para rebalanceamento trimestral:
    Identifica o último dia de negociação dos meses de Março (Q1), Junho (Q2), Setembro (Q3) e Dezembro (Q4).
    Isso assegura estrita execução pontual (point-in-time), eliminando viés de antecipação (look-ahead bias).
    """
    df_datas = pd.DataFrame(index=datas_disponiveis)
    df_datas['Ano'] = df_datas.index.year
    df_datas['Mes'] = df_datas.index.month
    df_datas['Trimestre'] = df_datas.index.quarter
    
    if frequencia.lower() == "trimestral":
        # Pega o último pregão disponível de cada trimestre
        datas_reb = df_datas.groupby(['Ano', 'Trimestre']).apply(lambda g: g.index.max(), include_groups=False).tolist()
    elif frequencia.lower() == "mensal":
        datas_reb = df_datas.groupby(['Ano', 'Mes']).apply(lambda g: g.index.max(), include_groups=False).tolist()
    elif frequencia.lower() == "semestral":
        df_datas['Semestre'] = (df_datas['Mes'] - 1) // 6 + 1
        datas_reb = df_datas.groupby(['Ano', 'Semestre']).apply(lambda g: g.index.max(), include_groups=False).tolist()
    elif frequencia.lower() == "anual":
        datas_reb = df_datas.groupby(['Ano']).apply(lambda g: g.index.max(), include_groups=False).tolist()
    else:
        raise ValueError(f"Frequência '{frequencia}' não suportada. Use 'trimestral', 'mensal', 'semestral' ou 'anual'.")

    return sorted(datas_reb)
