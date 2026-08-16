"""
===============================================================================
GERADOR DE RELATÓRIO FINAL EM PDF (gerar_pdf.py)
Projeto: Desafio Quant AI 2026 - Anomalia de Baixa Volatilidade (Low Vol)
Autoria: Candidato Anônimo — Equipe de Engenharia Quantitativa
Mascote: Robô Jonathan (Tartaruga Quant)
===============================================================================
Compila 'relatorio_final.pdf' a partir de 'relatorio.md' com padrão executivo:
- Anonimato absoluto (capa, cabeçalhos, rodapés e metadados).
- Lore completa da tartaruga Jonathan e fundamentação conceitual de Low Vol.
- Tipografia em Helvetica com hierarquia clara e espaçamentos equilibrados.
- Formatação matemática e renderização de equações em cartões destacados.
- Tabelas com colunas proporcionais, cabeçalhos destacados e linhas zebradas.
- Figuras em 300 DPI centralizadas e com quebra de página dedicada (sem órfãs).
- Cabeçalhos e rodapés anônimos com numeração dinâmica ('Página X de Y').
===============================================================================
"""

import os
import sys
import re
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_MD = os.path.join(BASE_DIR, "relatorio.md")
ARQUIVO_PDF = os.path.join(BASE_DIR, "relatorio_final.pdf")
PASTA_FIGURAS = os.path.join(BASE_DIR, "figuras")
MASCOTE_PATH = os.path.join(BASE_DIR, "robo.png") if os.path.exists(os.path.join(BASE_DIR, "robo.png")) else os.path.join(BASE_DIR, "assets", "jonathan.png")

# Paleta de Cores Institucional do Jonathan
C_PRIMARY = colors.HexColor("#11231A")       # Verde Noturno
C_SECONDARY = colors.HexColor("#1F3B2C")     # Verde Floresta
C_GOLD = colors.HexColor("#B08D4C")          # Dourado Jonathan
C_LIGHT_GOLD = colors.HexColor("#D4AF6A")    # Ouro Claro
C_CORAL = colors.HexColor("#E76F51")         # Coral Alerta
C_TEXT = colors.HexColor("#2B2D42")          # Grafite Escuro
C_BG_LIGHT = colors.HexColor("#F8F9FA")      # Fundo Claro
C_BORDER = colors.HexColor("#D1D5DB")        # Borda Cinza
C_MUTED = colors.HexColor("#6C757D")         # Cinza Médio


class NumberedCanvas(canvas.Canvas):
    """Canvas de dois passos para contagem e renderização dinâmica do total de páginas com estrito anonimato."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # A capa (página 1) não recebe cabeçalho nem rodapé
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(C_MUTED)

        # Cabeçalho Superior Anônimo
        self.drawString(2.0 * cm, 28.5 * cm, "Desafio Quant AI 2026 — Robô Jonathan (Low Volatility Anomaly)")
        self.drawRightString(19.0 * cm, 28.5 * cm, "Relatório Técnico Final de Submissão")
        self.setStrokeColor(C_GOLD)
        self.setLineWidth(0.75)
        self.line(2.0 * cm, 28.3 * cm, 19.0 * cm, 28.3 * cm)

        # Rodapé Inferior Anônimo
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.5)
        self.line(2.0 * cm, 1.8 * cm, 19.0 * cm, 1.8 * cm)
        self.drawString(2.0 * cm, 1.4 * cm, "Autoria: Candidato Anônimo | Universo IBrX-100 (2018–2026)")
        self.drawRightString(19.0 * cm, 1.4 * cm, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def criar_estilos():
    """Define a hierarquia tipográfica do documento."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CapaTitulo',
        fontName='Helvetica-Bold',
        fontSize=18.0,
        leading=23.0,
        textColor=C_PRIMARY,
        alignment=1, # Centralizado
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='CapaSubtitulo',
        fontName='Helvetica',
        fontSize=11.0,
        leading=15.0,
        textColor=C_GOLD,
        alignment=1,
        spaceAfter=18
    ))

    styles.add(ParagraphStyle(
        name='CapaAutor',
        fontName='Helvetica-Bold',
        fontSize=10.0,
        leading=14.0,
        textColor=C_SECONDARY,
        alignment=1
    ))

    styles.add(ParagraphStyle(
        name='CapaData',
        fontName='Helvetica',
        fontSize=9.0,
        leading=13.0,
        textColor=C_MUTED,
        alignment=1
    ))

    styles.add(ParagraphStyle(
        name='SecaoTitulo',
        fontName='Helvetica-Bold',
        fontSize=12.0,
        leading=16.0,
        textColor=C_PRIMARY,
        spaceBefore=14,
        spaceAfter=5,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='SubSecaoTitulo',
        fontName='Helvetica-Bold',
        fontSize=10.0,
        leading=13.5,
        textColor=C_GOLD,
        spaceBefore=9,
        spaceAfter=3,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='TextoCorpo',
        fontName='Helvetica',
        fontSize=8.6,
        leading=12.4,
        textColor=C_TEXT,
        alignment=4, # Justificado
        spaceAfter=5.5
    ))

    styles.add(ParagraphStyle(
        name='TextoDestaque',
        fontName='Helvetica-Oblique',
        fontSize=8.4,
        leading=11.8,
        textColor=C_SECONDARY,
        spaceBefore=3,
        spaceAfter=4.5
    ))

    styles.add(ParagraphStyle(
        name='FormulaDisplay',
        fontName='Helvetica-Bold',
        fontSize=9.0,
        leading=13.0,
        textColor=C_PRIMARY,
        alignment=1, # Centralizado
        spaceBefore=2,
        spaceAfter=2
    ))

    styles.add(ParagraphStyle(
        name='LegendaFigura',
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=11.0,
        textColor=C_SECONDARY,
        alignment=1, # Centralizado
        spaceBefore=3,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name='AlertaTexto',
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.5,
        textColor=C_PRIMARY,
        spaceAfter=2
    ))

    styles.add(ParagraphStyle(
        name='TabelaCabecalho',
        fontName='Helvetica-Bold',
        fontSize=7.0,
        leading=8.8,
        textColor=colors.white,
        alignment=1
    ))

    styles.add(ParagraphStyle(
        name='TabelaCelula',
        fontName='Helvetica',
        fontSize=6.6,
        leading=8.4,
        textColor=C_TEXT,
        alignment=1
    ))

    styles.add(ParagraphStyle(
        name='TabelaCelulaBold',
        fontName='Helvetica-Bold',
        fontSize=6.6,
        leading=8.4,
        textColor=C_PRIMARY,
        alignment=1
    ))

    styles.add(ParagraphStyle(
        name='TabelaInstitucionalKey',
        fontName='Helvetica-Bold',
        fontSize=8.0,
        leading=10.2,
        textColor=C_SECONDARY,
        alignment=0 # Alinhado à esquerda
    ))

    styles.add(ParagraphStyle(
        name='TabelaInstitucionalVal',
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.2,
        textColor=C_TEXT,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        name='SumarioItem',
        fontName='Helvetica-Bold',
        fontSize=9.0,
        leading=13.0,
        textColor=C_PRIMARY,
        spaceAfter=3
    ))

    styles.add(ParagraphStyle(
        name='ReferenciaItem',
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.8,
        textColor=C_TEXT,
        spaceAfter=3.5
    ))

    return styles


def formatar_formula_html(raw_latex: str) -> str:
    """Converte comandos LaTeX matemáticos em notação HTML limpa."""
    txt = raw_latex.strip()
    
    # Substituições de frações e raízes
    txt = txt.replace(r"\frac{252}{N - 1}", "( 252 / (N - 1) )")
    txt = txt.replace(r"\frac{252}{N-1}", "( 252 / (N - 1) )")
    txt = txt.replace(r"\frac{1}{N}", "( 1 / N )")
    txt = txt.replace(r"\frac{1}{M_q}", "1 / M<sub>q</sub>")
    txt = txt.replace(r"\frac{1}{T_d - 1}", "( 1 / (T<sub>d</sub> - 1) )")
    txt = txt.replace(r"\frac{V_T}{V_0}", "( V<sub>T</sub> / V<sub>0</sub> )")
    txt = txt.replace(r"\frac{252}{T_d}", "( 252 / T<sub>d</sub> )")
    txt = txt.replace(r"\frac{\sigma_{i,t}}{\sigma_{m,t}}", "(&sigma;<sub>i,t</sub> / &sigma;<sub>m,t</sub>)")
    txt = txt.replace(r"\frac{\text{CAGR} - \text{CDI}_{\text{anual}}}{\sigma_{\text{anual}}}", "( CAGR - CDI<sub>anual</sub> ) / &sigma;<sub>anual</sub>")
    txt = txt.replace(r"\frac{\text{CAGR} - \text{CDI}_{\text{ann}}}{\sigma_{\text{ann}}}", "( CAGR - CDI<sub>anual</sub> ) / &sigma;<sub>anual</sub>")
    txt = txt.replace(r"\frac{\max_{\tau \le t} V_\tau - V_t}{\max_{\tau \le t} V_\tau}", "[ max<sub>&tau; &le; t</sub> V<sub>&tau;</sub> - V<sub>t</sub> ] / max<sub>&tau; &le; t</sub> V<sub>&tau;</sub>")
    
    # Símbolos Gregos e Variáveis
    txt = txt.replace(r"\sigma_{i,t}", "&sigma;<sub>i,t</sub>")
    txt = txt.replace(r"\sigma_{\text{anual}}", "&sigma;<sub>anual</sub>")
    txt = txt.replace(r"\sigma_{\text{ann}}", "&sigma;<sub>anual</sub>")
    txt = txt.replace(r"\sigma_{m,t}", "&sigma;<sub>m,t</sub>")
    txt = txt.replace(r"\sigma", "&sigma;")
    txt = txt.replace(r"\beta_{i,t}", "&beta;<sub>i,t</sub>")
    txt = txt.replace(r"\beta_i", "&beta;<sub>i</sub>")
    txt = txt.replace(r"\beta_m", "&beta;<sub>m</sub>")
    txt = txt.replace(r"\beta", "&beta;")
    txt = txt.replace(r"\hat{\rho}_{i,m}", "&rho;&#770;<sub>i,m</sub>")
    txt = txt.replace(r"\alpha_{\text{anual}}", "&alpha;<sub>anual</sub>")
    txt = txt.replace(r"\alpha_{\text{ann}}", "&alpha;<sub>anual</sub>")
    txt = txt.replace(r"\alpha", "&alpha;")
    txt = txt.replace(r"\epsilon_t", "&epsilon;<sub>t</sub>")
    txt = txt.replace(r"\tau", "&tau;")
    
    # Somatórios e Raízes
    txt = txt.replace(r"\sum_{i \in Q_1}", "&Sigma;<sub>i &isin; Q1</sub>")
    txt = txt.replace(r"\sum_{k=0}^{N-1}", "&Sigma;<sub>k=0..N-1</sub>")
    txt = txt.replace(r"\sum_{t=1}^{T_d}", "&Sigma;<sub>t=1..T</sub>")
    txt = txt.replace(r"\sum_i", "&Sigma;<sub>i</sub>")
    txt = txt.replace(r"\sqrt{", "&radic;[ ")
    
    # Notações de Retorno e Pesos
    txt = txt.replace(r"E[R_i]", "<b>E[R<sub>i</sub>]</b>")
    txt = txt.replace(r"R_f", "R<sub>f</sub>")
    txt = txt.replace(r"E[R_m]", "E[R<sub>m</sub>]")
    txt = txt.replace(r"R_{i, t-k}", "R<sub>i, t-k</sub>")
    txt = txt.replace(r"\bar{R}_{i,t}", "R&#773;<sub>i,t</sub>")
    txt = txt.replace(r"\bar{R}_p", "R&#773;<sub>p</sub>")
    txt = txt.replace(r"R_{p,t}", "R<sub>p,t</sub>")
    txt = txt.replace(r"R_{\text{CDI},t}", "R<sub>CDI,t</sub>")
    txt = txt.replace(r"R_{CDI,t}", "R<sub>CDI,t</sub>")
    txt = txt.replace(r"R_{m,t}", "R<sub>m,t</sub>")
    txt = txt.replace(r"R_{\text{LO},t}", "R<sub>LO,t</sub>")
    txt = txt.replace(r"R_{\text{LS},t}", "R<sub>LS,t</sub>")
    txt = txt.replace(r"R_{Q_1,t}", "R<sub>Q1,t</sub>")
    txt = txt.replace(r"R_{Q_5,t}", "R<sub>Q5,t</sub>")
    txt = txt.replace(r"w_{i,t^+}", "w<sub>i,t<sup>+</sup></sub>")
    txt = txt.replace(r"w_{i,t^-}", "w<sub>i,t<sup>-</sup></sub>")
    txt = txt.replace(r"w_{i,t}", "w<sub>i,t</sub>")
    txt = txt.replace(r"w_i", "w<sub>i</sub>")
    txt = txt.replace(r"M_{Q_1}", "M<sub>Q1</sub>")
    txt = txt.replace(r"M_q", "M<sub>q</sub>")
    
    # Limpeza de Operadores
    txt = txt.replace(r"\ln(", "ln(")
    txt = txt.replace(r"\ln\left(", "ln(")
    txt = txt.replace(r"\left(", "(").replace(r"\right)", ")")
    txt = txt.replace(r"\left[", "[").replace(r"\right]", "]")
    txt = txt.replace(r"\text{Custo}_t", "Custo<sub>t</sub>")
    txt = txt.replace(r"\text{CAGR}", "CAGR")
    txt = txt.replace(r"\text{Sharpe}", "Índice de Sharpe")
    txt = txt.replace(r"\text{Max DD}", "Max Drawdown")
    txt = txt.replace(r"\text{CDI}", "CDI")
    txt = txt.replace(r"\max_{t \in [0,T]}", "max<sub>t &isin; [0,T]</sub>")
    txt = txt.replace(r"\max_{\tau \le t}", "max<sub>&tau; &le; t</sub>")
    txt = txt.replace(r"\times", "&times;")
    txt = txt.replace(r"\le", "&le;").replace(r"\approx", "&asymp;")
    txt = txt.replace(r"^2", "<sup>2</sup>")
    txt = txt.replace(r"}", "]") if "&radic;[" in txt else txt.replace("}", "")
    txt = txt.replace("{", "")
    
    return txt


def formatar_inline_latex(texto: str) -> str:
    """Substitui expressões matemáticas inline por entidades limpas."""
    t = texto
    t = t.replace("$Q_1$", "<i>Q</i><sub>1</sub>")
    t = t.replace("$Q_5$", "<i>Q</i><sub>5</sub>")
    t = t.replace("$Q_2$", "<i>Q</i><sub>2</sub>")
    t = t.replace("$Q_3$", "<i>Q</i><sub>3</sub>")
    t = t.replace("$Q_4$", "<i>Q</i><sub>4</sub>")
    t = t.replace("Q1", "<i>Q</i><sub>1</sub>")
    t = t.replace("Q5", "<i>Q</i><sub>5</sub>")
    t = t.replace(r"$\beta$", "&beta;")
    t = t.replace(r"$\beta_i$", "&beta;<sub>i</sub>")
    t = t.replace(r"$\beta_m$", "&beta;<sub>m</sub>")
    t = t.replace(r"$\alpha$", "&alpha;")
    t = t.replace(r"$\alpha_{\text{anual}}$", "&alpha;<sub>anual</sub>")
    t = t.replace(r"$\sigma_{i,t}$", "&sigma;<sub>i,t</sub>")
    t = t.replace(r"$\sigma_{\text{ann}}$", "&sigma;<sub>anual</sub>")
    t = t.replace(r"$\sigma_{\text{anual}}$", "&sigma;<sub>anual</sub>")
    t = t.replace(r"$\sigma_{m,t}$", "&sigma;<sub>m,t</sub>")
    t = t.replace(r"$T \in \{63, 126, 252\}$", "<i>T</i> &isin; {63, 126, 252}")
    t = t.replace(r"$N \in \{63, 126, 252\}$", "<i>N</i> &isin; {63, 126, 252}")
    t = t.replace(r"$c = 0\text{ bps}$", "<i>c</i> = 0 bps")
    t = t.replace(r"$c = 5\text{ bps}$", "<i>c</i> = 5 bps")
    t = t.replace(r"$c = 15\text{ bps}$", "<i>c</i> = 15 bps")
    t = t.replace(r"$0$", "0").replace(r"$5$", "5").replace(r"$15$", "15")
    t = t.replace(r"$Q_1 - Q_5 + \text{CDI}$", "<i>Q</i><sub>1</sub> - <i>Q</i><sub>5</sub> + CDI")
    t = t.replace(r"$R_{CDI,t}$", "<i>R</i><sub>CDI,t</sub>")
    t = t.replace(r"$R_m$", "<i>R</i><sub>m</sub>")
    t = t.replace(r"$R_f$", "<i>R</i><sub>f</sub>")
    t = t.replace(r"$\beta = 0,67$", "&beta; = 0,67")
    t = t.replace(r"$\beta \approx -0,66$", "&beta; &asymp; -0,66")
    t = t.replace(r"$\beta=1$", "&beta; = 1")
    t = t.replace(r"$\beta \le 1$", "&beta; &le; 1")
    t = t.replace(r"$\text{SR}$", "SR")
    t = t.replace(r"$w_i = 1/M_{Q_1} \approx 5,0\%$", "<i>w</i><sub>i</sub> = 1/<i>M</i><sub>Q1</sub> &asymp; 5,0%")
    t = t.replace(r"$0\% \le w_i \le 8\%$", "0% &le; <i>w</i><sub>i</sub> &le; 8%")
    t = t.replace(r"$t$", "<i>t</i>").replace(r"$t+1$", "<i>t</i>+1")
    t = t.replace(r"$i$", "<i>i</i>").replace(r"$q$", "<i>q</i>")
    t = t.replace(r"$M_q \approx 20$", "<i>M</i><sub>q</sub> &asymp; 20")
    t = t.replace(r"$M_q$", "<i>M</i><sub>q</sub>")
    t = t.replace(r"$T$", "<i>T</i>").replace(r"$c$", "<i>c</i>").replace(r"$N$", "<i>N</i>")
    t = t.replace("(β)", "(&beta;)").replace("(α)", "(&alpha;)")
    t = t.replace("β = 0,67", "&beta; = 0,67").replace("β ≈ -0,66", "&beta; &asymp; -0,66")
    t = t.replace("σ_anual", "&sigma;<sub>anual</sub>")
    t = t.replace("w_i", "<i>w</i><sub>i</sub>")
    return t


def gerar_elementos_capa(styles):
    """Monta a capa institucional com imagem do mascote e estrito anonimato."""
    elementos = []
    elementos.append(Spacer(1, 1.2 * cm))

    elementos.append(Paragraph(
        "A Anomalia de Baixa Volatilidade e a Estratégia <i>Betting Against Beta</i> (BAB) no Mercado Acionário Brasileiro",
        styles['CapaTitulo']
    ))
    elementos.append(Paragraph(
        "Uma Análise Técnica e Empírica no Universo IBrX-100 (2018–2026)",
        styles['CapaSubtitulo']
    ))

    elementos.append(HRFlowable(width="75%", thickness=1.5, color=C_GOLD, spaceAfter=18, spaceBefore=4))

    # Imagem do Mascote
    if os.path.exists(MASCOTE_PATH):
        img_mascote = Image(MASCOTE_PATH, width=6.8 * cm, height=6.8 * cm)
        img_mascote.hAlign = 'CENTER'
        elementos.append(img_mascote)
        elementos.append(Spacer(1, 0.6 * cm))
    else:
        elementos.append(Spacer(1, 5.0 * cm))

    elementos.append(Paragraph("<b>DESAFIO QUANT AI 2026</b>", styles['CapaAutor']))
    elementos.append(Spacer(1, 0.15 * cm))
    elementos.append(Paragraph("<b>Estratégia:</b> Robô Jonathan (<i>Low Volatility Quant Strategy</i>)", styles['CapaAutor']))
    elementos.append(Spacer(1, 0.15 * cm))
    elementos.append(Paragraph("<b>Autoria:</b> Candidato Anônimo (Equipe de Engenharia Quantitativa)", styles['CapaAutor']))
    elementos.append(Spacer(1, 0.15 * cm))
    elementos.append(Paragraph("Agosto de 2026", styles['CapaData']))

    elementos.append(PageBreak())
    return elementos


def gerar_elementos_sumario(styles):
    """Monta o sumário executivo com a estrutura do relatório."""
    elementos = []
    elementos.append(Paragraph("SUMÁRIO EXECUTIVO", styles['SecaoTitulo']))
    elementos.append(HRFlowable(width="100%", thickness=1.0, color=C_GOLD, spaceAfter=14, spaceBefore=2))

    itens_sumario = [
        ("🏛️ Apresentação Institucional do Robô Jonathan", "Lore da tartaruga, mandato quantitativo e capacidade de alocação"),
        ("1. Resumo Executivo", "Fundamentos da anomalia e síntese de resultados empíricos"),
        ("2. Hipótese e Fundamentação Teórica", "Falha do CAPM, restrições de alavancagem e efeito da Selic/CDI"),
        ("3. Metodologia de Pesquisa", "Reconstituição corte a corte, sinais de volatilidade e regimes Long-Only/Long-Short"),
        ("4. Vieses Metodológicos e Cuidados Operacionais", "Mitigação de survivorship bias, look-ahead bias e atritos de mercado"),
        ("5. Interpretação Técnica das Métricas", "CAGR, Volatilidade, Sharpe vs. CDI, Max Drawdown e Alpha de Jensen"),
        ("6. Resultados Empíricos do Backtest", "Tabela comparativa dos 18 experimentos e diagnósticos visuais 300 DPI"),
        ("7. Limitações Práticas e Próximos Passos", "Impacto de BTC, risco de duration em Utilities e esteira prioritária"),
        ("8. Uso de IA Generativa no Projeto", "Documentação do edital: Deep Research, Coding Assistant e Refinamento"),
        ("9. Referências Bibliográficas", "Literatura internacional seminal e estudos empíricos brasileiros"),
    ]

    for titulo, desc in itens_sumario:
        elementos.append(Paragraph(f"<b>{titulo}</b> — <font color='#6C757D'>{desc}</font>", styles['TextoCorpo']))
        elementos.append(Spacer(1, 0.12 * cm))

    elementos.append(Spacer(1, 0.6 * cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=12, spaceBefore=4))
    elementos.append(PageBreak())
    return elementos


def converter_markdown_para_pdf(styles):
    """Processa relatorio.md e constrói a sequência de Flowables com diagramação elegante."""
    elementos = []

    if not os.path.exists(ARQUIVO_MD):
        print(f"Erro: {ARQUIVO_MD} nao encontrado.")
        return elementos

    with open(ARQUIVO_MD, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    # 1. Capa e Sumário
    elementos.extend(gerar_elementos_capa(styles))
    elementos.extend(gerar_elementos_sumario(styles))

    i = 0
    total_linhas = len(linhas)

    while i < total_linhas:
        linha = linhas[i].strip()

        # Linhas vazias
        if not linha:
            i += 1
            continue

        # Ignora cabeçalhos duplicados da capa
        if linha.startswith("# A Anomalia de Baixa Volatilidade") or linha.startswith("**Desafio Quant AI 2026**") or linha.startswith("**Autoria:**") or linha.startswith("**Data de Conclusão:**") or linha.startswith("**Estratégia Quantitativa:**"):
            i += 1
            continue

        # Título de Seção H2 (ex: ## 1) Resumo Executivo)
        if linha.startswith("## "):
            texto_h2 = linha.replace("## ", "").strip()
            elementos.append(Spacer(1, 0.25 * cm))
            elementos.append(Paragraph(formatar_inline_latex(texto_h2), styles['SecaoTitulo']))
            elementos.append(HRFlowable(width="100%", thickness=0.8, color=C_GOLD, spaceAfter=6, spaceBefore=2))
            i += 1
            continue

        # Título de Subseção H3 (ex: ### 3.1. Universo de Ativos)
        if linha.startswith("### "):
            texto_h3 = linha.replace("### ", "").strip()
            elementos.append(Spacer(1, 0.18 * cm))
            elementos.append(Paragraph(formatar_inline_latex(texto_h3), styles['SubSecaoTitulo']))
            i += 1
            continue

        # Título H4 (ex: #### Figura 1: ...)
        if linha.startswith("#### Figura ") or linha.startswith("#### "):
            texto_h4 = linha.replace("#### ", "").strip()
            # Se for uma figura na Seção 6, vamos agrupar com a imagem subsequente
            if "Figura " in texto_h4:
                # Procura a imagem correspondente nas próximas linhas
                i_img = i + 1
                img_path = None
                img_caption = texto_h4
                while i_img < total_linhas and not linhas[i_img].strip().startswith("####") and not linhas[i_img].strip().startswith("##"):
                    if linhas[i_img].strip().startswith("!["):
                        match_img = re.search(r'!\[(.*?)\]\((.*?)\)', linhas[i_img].strip())
                        if match_img:
                            img_path = match_img.group(2)
                            img_caption = match_img.group(1)
                            break
                    i_img += 1

                if img_path:
                    caminho_abs = os.path.join(BASE_DIR, img_path.replace("/", os.sep))
                    if os.path.exists(caminho_abs):
                        elementos.append(PageBreak()) # Quebra de página limpa para cada figura
                        elementos.append(Paragraph(formatar_inline_latex(texto_h4), styles['SubSecaoTitulo']))
                        elementos.append(Spacer(1, 0.15 * cm))
                        img_flow = Image(caminho_abs, width=16.5 * cm, height=8.25 * cm)
                        img_flow.hAlign = 'CENTER'
                        elementos.append(img_flow)
                        elementos.append(Spacer(1, 0.1 * cm))
                        elementos.append(Paragraph(f"<b>{img_caption}</b>", styles['LegendaFigura']))
                        elementos.append(Spacer(1, 0.2 * cm))
                        i = i_img + 1
                        continue

            elementos.append(Spacer(1, 0.12 * cm))
            elementos.append(Paragraph(formatar_inline_latex(texto_h4), styles['SubSecaoTitulo']))
            i += 1
            continue

        # Linha Horizontal (---)
        if linha == "---":
            elementos.append(Spacer(1, 0.1 * cm))
            elementos.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=6, spaceBefore=3))
            i += 1
            continue

        # Callouts / Alerts (> [!IMPORTANT] ou > [!WARNING])
        if linha.startswith("> [!IMPORTANT]") or linha.startswith("> [!WARNING]") or linha.startswith(">"):
            linhas_callout = []
            while i < total_linhas and (linhas[i].strip().startswith(">") or (linhas_callout and linhas[i].strip() and not linhas[i].strip().startswith("#") and not linhas[i].strip().startswith("|") and not linhas[i].strip().startswith("$$"))):
                l_raw = linhas[i].strip()
                if l_raw.startswith(">"):
                    l_limpa = l_raw.replace(">", "").strip()
                    if not l_limpa.startswith("[!"):
                        linhas_callout.append(l_limpa)
                else:
                    break
                i += 1
                
            texto_callout = " ".join(linhas_callout)
            texto_callout = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto_callout)
            texto_callout = re.sub(r'\*(.*?)\*', r'<i>\1</i>', texto_callout)
            texto_callout = formatar_inline_latex(texto_callout)

            p_alerta = Paragraph(f"<b>DIRETRIZ DE GOVERNANÇA / ALERTA METODOLÓGICO:</b><br/>{texto_callout}", styles['AlertaTexto'])
            t_alerta = Table([[p_alerta]], colWidths=[17.0 * cm])
            t_alerta.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FDF8E2")),
                ('BOX', (0, 0), (-1, -1), 1.0, C_GOLD),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elementos.append(Spacer(1, 0.15 * cm))
            elementos.append(KeepTogether([t_alerta]))
            elementos.append(Spacer(1, 0.15 * cm))
            continue

        # Inserção de Imagens avulsas (![Legenda](caminho))
        if linha.startswith("!["):
            match_img = re.search(r'!\[(.*?)\]\((.*?)\)', linha)
            if match_img:
                legenda = match_img.group(1)
                caminho_rel = match_img.group(2)
                caminho_abs = os.path.join(BASE_DIR, caminho_rel.replace("/", os.sep))

                if os.path.exists(caminho_abs):
                    elementos.append(Spacer(1, 0.15 * cm))
                    img_flow = Image(caminho_abs, width=16.5 * cm, height=8.25 * cm)
                    img_flow.hAlign = 'CENTER'
                    elementos.append(KeepTogether([
                        img_flow,
                        Spacer(1, 0.1 * cm),
                        Paragraph(f"<b>{legenda}</b>", styles['LegendaFigura'])
                    ]))
                    elementos.append(Spacer(1, 0.15 * cm))
            i += 1
            continue

        # Fórmulas LaTeX em bloco ($$ ... $$)
        if linha.startswith("$$"):
            if linha.endswith("$$") and len(linha) > 4:
                formula_raw = linha[2:-2].strip()
                i += 1
            else:
                linhas_formula = [linha.replace("$$", "")]
                i += 1
                while i < total_linhas and not (linhas[i].strip().endswith("$$") or "$$" in linhas[i]):
                    linhas_formula.append(linhas[i].strip())
                    i += 1
                if i < total_linhas:
                    linhas_formula.append(linhas[i].strip().replace("$$", ""))
                    i += 1
                formula_raw = " ".join(linhas_formula).strip()

            formula_html = formatar_formula_html(formula_raw)

            # Cartão centralizado para equações
            p_form = Paragraph(f"<b>{formula_html}</b>", styles['FormulaDisplay'])
            t_form = Table([[p_form]], colWidths=[17.0 * cm])
            t_form.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
                ('BOX', (0, 0), (-1, -1), 0.6, C_BORDER),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elementos.append(Spacer(1, 0.1 * cm))
            elementos.append(KeepTogether([t_form]))
            elementos.append(Spacer(1, 0.1 * cm))
            continue

        # Tabelas Markdown (| col1 | col2 | ...)
        if linha.startswith("|"):
            linhas_tabela = []
            while i < total_linhas and linhas[i].strip().startswith("|"):
                l_tab = linhas[i].strip()
                if not re.match(r'^\|[\s:-|-]+\|$', l_tab):
                    cols = [c.strip() for c in l_tab.strip('|').split('|')]
                    linhas_tabela.append(cols)
                i += 1

            if linhas_tabela:
                num_cols = len(linhas_tabela[0])
                largura_disp = 17.0 * cm

                # Tabela institucional de 2 colunas vs Tabela quantitativa de 12 colunas
                if num_cols == 2:
                    col_widths = [4.8 * cm, 12.2 * cm]
                    dados_celulas = []
                    for r_idx, row in enumerate(linhas_tabela):
                        c0_txt = formatar_inline_latex(re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', row[0]))
                        c1_txt = formatar_inline_latex(re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', re.sub(r'\*(.*?)\*', r'<i>\1</i>', row[1])))
                        if r_idx == 0:
                            dados_celulas.append([Paragraph(f"<b>{c0_txt}</b>", styles['TabelaCabecalho']), Paragraph(f"<b>{c1_txt}</b>", styles['TabelaCabecalho'])])
                        else:
                            dados_celulas.append([Paragraph(c0_txt, styles['TabelaInstitucionalKey']), Paragraph(c1_txt, styles['TabelaInstitucionalVal'])])
                    
                    t_rep = Table(dados_celulas, colWidths=col_widths)
                    estilo = [
                        ('BACKGROUND', (0, 0), (-1, 0), C_SECONDARY),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
                        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5.0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5.0),
                    ]
                    for r_i in range(1, len(dados_celulas)):
                        if r_i % 2 == 0:
                            estilo.append(('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor("#F8F9FA")))
                    t_rep.setStyle(TableStyle(estilo))

                else:
                    # Tabela de 12 colunas otimizada para página A4
                    col_widths = [1.25 * cm, 2.35 * cm, 1.15 * cm, 1.10 * cm, 1.45 * cm, 1.35 * cm, 1.45 * cm, 1.15 * cm, 1.35 * cm, 1.45 * cm, 1.55 * cm, 1.15 * cm]
                    if len(col_widths) != num_cols:
                        col_widths = [largura_disp / num_cols] * num_cols

                    dados_celulas = []
                    for r_idx, row in enumerate(linhas_tabela):
                        linha_c = []
                        for c_idx, val in enumerate(row):
                            val_limpo = formatar_inline_latex(val)
                            val_limpo = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', val_limpo)
                            val_limpo = re.sub(r'\*(.*?)\*', r'<i>\1</i>', val_limpo)
                            val_limpo = val_limpo.replace("`", "")
                            
                            if r_idx == 0:
                                p_c = Paragraph(f"<b>{val_limpo}</b>", styles['TabelaCabecalho'])
                            else:
                                if "EXP-" in val or "BENCH-" in val or "Long-Only" in val or "<b>" in val_limpo:
                                    p_c = Paragraph(val_limpo, styles['TabelaCelulaBold'])
                                else:
                                    p_c = Paragraph(val_limpo, styles['TabelaCelula'])
                            linha_c.append(p_c)
                        dados_celulas.append(linha_c)

                    t_rep = Table(dados_celulas, colWidths=col_widths, repeatRows=1)
                    estilo = [
                        ('BACKGROUND', (0, 0), (-1, 0), C_SECONDARY),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 0.35, C_BORDER),
                        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                        ('LEFTPADDING', (0, 0), (-1, -1), 1.5),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 1.5),
                    ]
                    for r_i in range(1, len(dados_celulas)):
                        if r_i % 2 == 0:
                            estilo.append(('BACKGROUND', (0, r_i), (-1, r_i), colors.HexColor("#F8F9FA")))
                    t_rep.setStyle(TableStyle(estilo))

                elementos.append(Spacer(1, 0.15 * cm))
                elementos.append(KeepTogether([t_rep]))
                elementos.append(Spacer(1, 0.2 * cm))
            continue

        # Lista com marcadores (- ou *)
        if linha.startswith("- ") or linha.startswith("* "):
            texto_item = linha[2:].strip()
            texto_item = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto_item)
            texto_item = re.sub(r'\*(.*?)\*', r'<i>\1</i>', texto_item)
            texto_item = re.sub(r'`(.*?)`', r'<b>\1</b>', texto_item)
            texto_item = formatar_inline_latex(texto_item)
            elementos.append(Paragraph(f"• {texto_item}", styles['TextoCorpo']))
            i += 1
            continue

        # Lista numerada (1. , 2. )
        match_num = re.match(r'^(\d+)\.\s+(.*)', linha)
        if match_num:
            num_item = match_num.group(1)
            texto_item = match_num.group(2)
            texto_item = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto_item)
            texto_item = re.sub(r'\*(.*?)\*', r'<i>\1</i>', texto_item)
            texto_item = re.sub(r'`(.*?)`', r'<b>\1</b>', texto_item)
            texto_item = formatar_inline_latex(texto_item)
            elementos.append(Paragraph(f"<b>{num_item}.</b> {texto_item}", styles['TextoCorpo']))
            i += 1
            continue

        # Parágrafo de texto corrido
        texto_p = linha
        texto_p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto_p)
        texto_p = re.sub(r'\*(.*?)\*', r'<i>\1</i>', texto_p)
        texto_p = re.sub(r'`(.*?)`', r'<b>\1</b>', texto_p)
        texto_p = formatar_inline_latex(texto_p)
        
        # Estilo de Referência Bibliográfica na seção 9
        if linha.startswith("- **") and ("Journal" in linha or "Revista" in linha or "Finance" in linha or "Press" in linha or "Praeger" in linha):
            elementos.append(Paragraph(texto_p.replace("- ", ""), styles['ReferenciaItem']))
        else:
            elementos.append(Paragraph(texto_p, styles['TextoCorpo']))
        i += 1

    return elementos


def compilar_pdf():
    """Gera o documento PDF executivo final."""
    print("=" * 80)
    print("INICIANDO COMPILACAO DO RELATORIO FINAL ANONIMO (relatorio_final.pdf)...")
    print("=" * 80)

    doc = SimpleDocTemplate(
        ARQUIVO_PDF,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm
    )

    styles = criar_estilos()
    elementos = converter_markdown_para_pdf(styles)

    print(f"Total de elementos tipograficos estruturados: {len(elementos)}")
    
    doc.build(elementos, canvasmaker=NumberedCanvas)
    
    print("=" * 80)
    print(f"RELATORIO FINAL COMPILADO COM SUCESSO: {ARQUIVO_PDF}")
    print("=" * 80)


if __name__ == "__main__":
    compilar_pdf()
