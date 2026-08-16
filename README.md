# 🐢 Desafio Quant AI 2026 — Tese 2: Anomalia de Baixa Volatilidade (Betting Against Beta)

> **"Não corro riscos desnecessários. Acumulo tempo a favor. Consistência hoje, liberdade sempre."**  
> — *Jonathan, o Robô-Tartaruga Quant*

---

## 📌 1. Visão Geral e Storytelling (Jonathan vs. A Lebre)

Este repositório contém a implementação quantitativa completa, modular e reproduzível da **Tese 2: Anomalia de Baixa Volatilidade (*Betting Against Beta* / Low Volatility)** para o **Desafio Quant AI 2026**.

### A Metáfora Central
- **🐢 Jonathan (Quintil 1 - Low Volatility):** Inspirado em Jonathan, a tartaruga-gigante-de-seychelles reconhecida pelo *Guinness World Records* como o animal terrestre vivo mais antigo do mundo (>190 anos). Jonathan atravessou guerras mundiais, crises financeiras e choques de mercado não por ser o mais rápido, mas por sua robustez e por evitar drawdowns fatais.
- **🐇 A Lebre (Quintil 5 - High Volatility):** Representa ativos altamente voláteis e especulativos que apresentam picos efêmeros em fases de euforia, mas sofrem rebaixamentos severos (-60% a -80%) durante choques de mercado, destruindo a composição de juros compostos de longo prazo.

---

## 🏛️ 2. Fundamentação Teórica da Estratégia

O modelo clássico de precificação de ativos (*Capital Asset Pricing Model - CAPM*, Sharpe, 1964) postula uma relação linear positiva e direta entre risco sistemático ($\beta$) e retorno esperado:

$$\mathbb{E}[R_i] = R_f + \beta_i (\mathbb{E}[R_m] - R_f)$$

Entretanto, evidências empíricas históricas seminais globais e no mercado brasileiro (**Haugen & Heins, 1972**; **Baker, Bradley & Wurgler, 2011**; **Frazzini & Pedersen, 2014**) revelam que **portfólios de ações com menor volatilidade histórica entregam retornos absolutos e retornos ajustados ao risco (Índice de Sharpe) substancialmente superiores aos de portfólios de alta volatilidade**.

### Por que a anomalia persiste? (Limites de Arbitragem)
1. **Restrições de Alavancagem Institucional:** Gestores de fundos e investidores institucionais que buscam superar benchmarks muitas vezes enfrentam restrições regulatórias para se alavancar. Como resultado, concentram capital em ações de alto beta/risco para obter retornos maiores, inflando artificialmente seus preços.
2. **Viés Comportamental de Loteria (*Preference for Skewness*):** Investidores pessoas físicas e especuladores superavaliam ações com potencial remoto de valorização explosiva (*growth/techs*) e negligenciam empresas maduras, previsíveis e geradoras de caixa (*utilities, telecom, seguros*).

---

## 🛠️ 3. Arquitetura Modular do Código

O projeto foi concebido seguindo princípios rigorosos de engenharia de software e finanças quantitativas:

```
desafio_quant/
├── .venv/                              # Ambiente virtual Python isolado
├── requirements.txt                    # Dependências fixadas do projeto
├── data/
│   ├── ibrx_composicao_historica.csv   # Universo IBrX-100 histórico ponto-a-ponto (sem viés de sobrevivência)
│   ├── cotacoes_cache.parquet          # Cache local de preços ajustados (Yahoo Finance)
│   └── cdi_cache.csv                   # Cache local do CDI diário (BCB SGS 12)
├── assets/
│   ├── jonathan.png                    # Mascote Jonathan Robô-Tartaruga
│   └── jonathan_vs_lebre.png           # Jonathan cruzando a linha de chegada vs Lebre
├── reports/                            # Gráficos em alta resolução (300 DPI) com tema escuro do Jonathan
│   ├── curva_capital.png
│   ├── drawdown_subaquatico.png
│   ├── dispersao_quintis.png
│   ├── heatmap_retornos.png
│   └── composicao_ultimo_rebalanceamento.png
├── dados.py                            # Ingestão, cache, CDI BCB, IBrX histórico e calendário B3
├── estrategia.py                       # Volatilidade móvel 252d, Beta, ranking e formação de quintis (Q1 a Q5)
├── backtest.py                         # Motor de simulação temporal trimestral, custos de 5 bps e KPIs
├── graficos.py                         # Gerador de relatórios estáticos em alta definição
├── dashboard.py                        # Painel interativo completo em Streamlit
├── main.py                             # Script de execução rápida no terminal
└── README.md                           # Documentação completa e disclaimers
```

---

## 🚀 4. Como Configurar e Executar

### Passo 1: Clonar o Repositório e Criar o Ambiente Virtual

No terminal (PowerShell ou Prompt de Comando do Windows):

```powershell
# Criação do ambiente virtual .venv
py -3.13 -m venv .venv

# Ativação do ambiente virtual
# No Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# No Windows Prompt de Comando (CMD):
.\.venv\Scripts\activate.bat
```

### Passo 2: Instalar as Dependências

```powershell
pip install -r requirements.txt
```

### Passo 3: Executar o Backtest e Gerar os Relatórios Gráficos

Para rodar a simulação padrão e exportar todos os gráficos em `reports/`:

```powershell
python main.py
```

### Passo 4: Gerar Figuras de Publicação em 300 DPI (`figuras/`)

Para gerar as 5 figuras em altíssima definição (300 DPI) para o relatório institucional:

```powershell
python figuras.py
```

### Passo 5: Gerar o Relatório Final em PDF de Submissão (`relatorio_final.pdf`)

Para compilar e gerar o PDF final de submissão do desafio com capa, sumário executivo, figuras e tabelas formatadas:

```powershell
python gerar_pdf.py
```

### Passo 6: Iniciar o Dashboard Interativo Multi-páginas (Streamlit)

Para abrir a interface visual no seu navegador (incluindo a página principal e o laboratório de experimentos):

```powershell
streamlit run dashboard.py
```


---

## 📊 5. Parâmetros Metodológicos e Disciplina Quantitativa

- **Universo de Investimento:** Universo histórico do **IBrX-100** reconstruído periodicamente (`data/ibrx_composicao_historica.csv`), eliminando o viés de sobrevivência.
- **Janela de Cálculo (Lookback):** **252 pregões** (12 meses úteis) para cálculo da volatilidade anualizada ($\sigma = \text{std} \times \sqrt{252}$) e Beta contra o Ibovespa.
- **Frequência de Rebalanceamento:** Sistemática **Trimestral** (último pregão útil de Março, Junho, Setembro e Dezembro).
- **Sem Viés de Antecipação (*No Look-ahead Bias*):** Os pesos de cada trimestre são fixados estritamente com base nos dados fechados no dia de rebalanceamento.
- **Custos de Transação:** **5 bps (0,05%)** aplicados diretamente sobre o giro/turnover de rebalanceamento da carteira.
- **Taxa Livre de Risco:** Série diária oficial do **CDI (Banco Central do Brasil - SGS 12)** com acumulação composta em dias úteis.

---

## 🤖 6. Documentação do Uso de IA Generativa (GenAI)

Em conformidade com as diretrizes do **Guia de Primeiros Passos — Desafio Quant AI 2026**:

1. **Criação do Mascote e Identidade Visual:**  
   Utilizou-se IA Generativa multimodal de imagem para concepção e geração do personagem **Jonathan, o Robô-Tartaruga Quant**, incorporando a paleta de cores corporativa:
   - Verde-petróleo escuro (`#1F3B2C`) — Solidez, estabilidade e proteção de capital (casco hexagonal).
   - Dourado envelhecido (`#B08D4C`) — Longevidade, tradição e consistência.
   - Coral / Alerta (`#E76F51`) — Risco elevado da Lebre.
   - Cinza claro (`#D9D9D9`) e Branco — Clareza e precisão analítica.

2. **Engenharia de Software e Data Storytelling:**  
   A IA generativa atuou como assistente sênior na estruturação modular do código em Python, documentação técnica, design de interface no Streamlit e narrativa pedagógica de dados.

---

## ⚠️ 7. Aviso Legal (Disclaimer)

Este projeto foi desenvolvido estritamente para fins acadêmicos, educacionais e de pesquisa quantitativa no âmbito do **Desafio Quant AI 2026**.  
**Não constitui, sob nenhuma circunstância, recomendação de investimento, aconselhamento financeiro, oferta ou solicitação de compra e venda de quaisquer ativos ou valores mobiliários.**  
Retornos históricos passados não são garantia de rendimentos futuros.
