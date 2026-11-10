import hashlib
import importlib

import streamlit as st
import pandas as pd

from modules.data_loader import load_uploaded_file
from modules.data_profiler import profile_dataframe
from modules.metrics_engine import generate_metrics
from modules.chart_engine import generate_charts

from modules.insights_engine import (
    generate_insights,
    generate_anomaly_details
)

from modules.context_engine import generate_context_insights

import modules.executive_report as executive_report_module
import modules.ai_analysis as ai_analysis_module

# =========================================================
# 1. CARREGAMENTO DOS MÓDULOS
# =========================================================

importlib.reload(executive_report_module)
importlib.reload(ai_analysis_module)

create_executive_summary = (
    executive_report_module.create_executive_summary
)

generate_ai_analysis = (
    ai_analysis_module.generate_ai_analysis
)


# =========================================================
# 2. CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="VÉRTICE | Data Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 3. IDENTIDADE VISUAL — PALETA RUBI / VINHO / AZUL-NAVY
# =========================================================

COLOR_PALETTE = {
    "red": "#E6223A",
    "burgundy": "#690722",
    "wine": "#621D43",
    "mauve": "#644765",
    "slate_blue": "#374365",
    "navy": "#062A48",
    "deep_navy": "#03213D"
}

CHART_COLORS = [
    COLOR_PALETTE["red"],
    COLOR_PALETTE["burgundy"],
    COLOR_PALETTE["wine"],
    COLOR_PALETTE["mauve"],
    COLOR_PALETTE["slate_blue"],
    COLOR_PALETTE["navy"],
    COLOR_PALETTE["deep_navy"]
]


# =========================================================
# 4. PERSONALIZAÇÃO DOS GRÁFICOS
# =========================================================

def apply_chart_palette(figure, chart_index):

    if figure is None:
        return

    figure.update_layout(
        colorway=CHART_COLORS,
        bargap=0.35,
        bargroupgap=0.15
    )

    figure.update_xaxes(
        gridcolor="rgba(100, 71, 101, 0.16)",
        linecolor="rgba(55, 67, 101, 0.42)",
        zerolinecolor="rgba(100, 71, 101, 0.30)"
    )

    figure.update_yaxes(
        gridcolor="rgba(100, 71, 101, 0.16)",
        linecolor="rgba(55, 67, 101, 0.42)",
        zerolinecolor="rgba(100, 71, 101, 0.30)"
    )

    bar_color_position = 0

    for trace_index, trace in enumerate(figure.data):

        trace_color = CHART_COLORS[
            trace_index % len(CHART_COLORS)
        ]

        if trace.type == "pie":

            trace.marker.colors = CHART_COLORS
            trace.marker.line.color = "rgba(255, 255, 255, 0.72)"
            trace.marker.line.width = 1

        elif trace.type == "bar":

            if trace.x is not None:
                bar_count = len(trace.x)
            elif trace.y is not None:
                bar_count = len(trace.y)
            else:
                bar_count = 0

            if bar_count:
                trace.marker.color = [
                    CHART_COLORS[
                        (bar_color_position + bar_index)
                        % len(CHART_COLORS)
                    ]
                    for bar_index in range(bar_count)
                ]
                bar_color_position += bar_count
            else:
                trace.marker.color = trace_color

            trace.marker.line.color = "rgba(255, 255, 255, 0.62)"
            trace.marker.line.width = 0.8

        elif trace.type in ("scatter", "scattergl"):

            if trace.mode and "lines" in trace.mode:
                trace.line.color = trace_color

            if trace.mode and "markers" in trace.mode:
                trace.marker.color = trace_color

        elif trace.type in ("box", "violin", "histogram"):

            trace.marker.color = trace_color


# =========================================================
# 5. IDENTIDADE VISUAL — CSS E MARCA TIPOGRÁFICA
# =========================================================

st.markdown(
    """
    <style>

    html[data-theme="light"] {
        --app-background: #F8F7F8;
        --app-surface: #FFFFFF;
        --app-card: #FFFFFF;
        --app-font: #03213D;
        --app-secondary: #644765;
        --app-muted: #644765;
        --app-border: #E8E1E6;
        --app-accent: #E6223A;
        --app-accent-hover: #690722;
        --app-accent-text: #FFFFFF;
        --app-accent-soft: rgba(230, 34, 58, 0.08);
    }

    html[data-theme="dark"] {
        --app-background: #03213D;
        --app-surface: #062A48;
        --app-card: #062A48;
        --app-font: #FFFFFF;
        --app-secondary: #FFFFFF;
        --app-muted: rgba(255, 255, 255, 0.72);
        --app-border: #374365;
        --app-accent: #E6223A;
        --app-accent-hover: #690722;
        --app-accent-text: #FFFFFF;
        --app-accent-soft: rgba(230, 34, 58, 0.14);
    }

    :root {
        --app-background: var(--background-color, #F8F7F8);
        --app-surface: var(--secondary-background-color, #FFFFFF);
        --app-card: var(--secondary-background-color, #FFFFFF);
        --app-font: var(--text-color, #03213D);
        --app-secondary: #644765;
        --app-muted: #644765;
        --app-border: #E8E1E6;
        --app-accent: var(--primary-color, #E6223A);
        --app-accent-hover: #690722;
        --app-accent-text: #FFFFFF;
        --app-accent-soft: rgba(230, 34, 58, 0.08);
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"],
    div[data-testid="stMetric"] {
        transition:
            background-color 0.2s ease,
            border-color 0.2s ease,
            color 0.2s ease;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    .main {
        background-color: var(--app-background);
        color: var(--app-font);
    }

    .main .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    .main h1,
    .main h2,
    .main h3,
    .main h4,
    .main h5 {
        color: var(--app-font);
        font-weight: 650;
        letter-spacing: -0.02em;
    }

    .main p,
    .main li,
    .main label,
    .main [data-testid="stCaptionContainer"] {
        color: var(--app-font);
    }

    .main [data-testid="stMarkdownContainer"] p {
        color: var(--app-font);
    }

    .main [data-testid="stCaptionContainer"],
    .main .stCaption {
        color: var(--app-muted);
    }

    [data-testid="stSidebar"] {
        background-color: var(
            --secondary-background-color,
            var(--app-background)
        );
        border-right: 1px solid var(--app-border);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: var(--app-font);
        font-weight: 650;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] label {
        color: var(--app-font);
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--app-muted);
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--app-border);
        opacity: 0.8;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: var(--app-surface);
        border: 1px solid var(--app-border);
        border-radius: 9px;
        padding: 10px;
    }

    /* MARCA */

    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 11px;
        margin-top: 4px;
    }

    .brand-symbol {
        width: 39px;
        height: 39px;
        flex: 0 0 39px;
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 3px;
        padding: 9px 8px;
        box-sizing: border-box;
        border: 1px solid var(--app-border);
        border-radius: 9px;
        background: var(--app-surface);
    }

    .brand-symbol span {
        display: block;
        width: 4px;
        border-radius: 3px 3px 1px 1px;
    }

    .brand-symbol span:nth-child(1) {
        height: 9px;
        background: #644765;
    }

    .brand-symbol span:nth-child(2) {
        height: 15px;
        background: #374365;
    }

    .brand-symbol span:nth-child(3) {
        height: 21px;
        background: #E6223A;
    }

    .brand-name {
        color: var(--app-font);
        font-size: 15px;
        font-weight: 750;
        line-height: 1.15;
        letter-spacing: -0.45px;
    }

    .brand-product {
        color: var(--app-secondary);
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1.8px;
        line-height: 1.5;
        margin-top: 4px;
    }

    .brand-subtitle {
        color: var(--app-muted);
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 1.45px;
        margin-top: 10px;
    }

    /* CABEÇALHO */

    .workspace-kicker {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--app-muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.45px;
        margin-bottom: 5px;
    }

    .workspace-kicker::before {
        content: "";
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--app-accent);
    }

    /* CARDS KPI */

    div[data-testid="stMetric"] {
        background-color: var(--app-card);
        border: 1px solid var(--app-border);
        border-top: 2px solid var(--app-accent);
        padding: 18px;
        border-radius: 9px;
        min-height: 105px;
        box-shadow: 0 1px 3px rgba(3, 33, 61, 0.06);
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetricLabel"] {
        color: var(--app-secondary) !important;
        font-size: 13px;
        font-weight: 600;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--app-font) !important;
        font-size: 27px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 12px;
    }

    /* BOTÕES */

    .stButton > button {
        background-color: var(--app-surface);
        color: var(--app-font);
        border: 1px solid var(--app-border);
        border-radius: 7px;
        min-height: 40px;
        font-weight: 600;
        transition: all 0.18s ease;
    }

    .stButton > button:hover {
        color: var(--app-accent);
        border-color: var(--app-accent);
        background-color: var(--app-surface);
    }

    .stButton > button:focus {
        border-color: var(--app-accent);
        color: var(--app-accent);
        box-shadow: 0 0 0 2px rgba(230, 34, 58, 0.18);
    }

    .stButton > button[kind="primary"],
    .stButton [data-testid="stBaseButton-primary"] {
        background-color: var(--app-accent);
        color: var(--app-accent-text);
        border: 1px solid var(--app-accent);
        font-weight: 600;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton [data-testid="stBaseButton-primary"]:hover {
        background-color: var(--app-accent-hover);
        color: #FFFFFF;
        border-color: var(--app-accent-hover);
    }

    /* DOWNLOADS */

    .stDownloadButton > button {
        background-color: var(--app-surface);
        color: var(--app-font);
        border: 1px solid var(--app-border);
        border-radius: 7px;
        font-weight: 600;
        transition: all 0.18s ease;
    }

    .stDownloadButton > button:hover {
        background-color: var(--app-surface);
        color: var(--app-accent);
        border-color: var(--app-accent);
    }

    /* ABAS */

    div[data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid var(--app-border);
    }

    button[data-baseweb="tab"] {
        background-color: transparent;
        color: var(--app-secondary) !important;
        font-size: 13px;
        font-weight: 600;
        border-radius: 5px 5px 0 0;
        padding: 10px 13px;
        border-bottom: 2px solid transparent;
        transition: all 0.18s ease;
    }

    button[data-baseweb="tab"]:hover {
        color: var(--app-accent) !important;
        background-color: transparent;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: transparent !important;
        color: var(--app-accent) !important;
        border-bottom: 2px solid var(--app-accent) !important;
    }

    div[data-baseweb="tab-highlight"] {
        background-color: var(--app-accent) !important;
    }

    /* TELA INICIAL */

    .welcome-card {
        position: relative;
        background-color: var(--app-surface);
        border: 1px solid var(--app-border);
        border-left: 4px solid var(--app-accent);
        border-radius: 10px;
        padding: 34px;
        margin-top: 28px;
        margin-bottom: 25px;
    }

    .welcome-eyebrow {
        color: var(--app-accent);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
    }

    .welcome-title {
        font-size: 30px;
        font-weight: 700;
        color: var(--app-font);
        letter-spacing: -0.8px;
        margin-bottom: 12px;
    }

    .welcome-text {
        color: var(--app-secondary);
        font-size: 15px;
        line-height: 1.75;
        max-width: 720px;
    }

    /* SOBRE O PROJETO */

    .about-hero {
        background-color: var(--app-surface);
        border: 1px solid var(--app-border);
        border-left: 4px solid var(--app-accent);
        border-radius: 10px;
        padding: 28px;
        margin-bottom: 24px;
    }

    .about-eyebrow {
        color: var(--app-accent);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.6px;
        margin-bottom: 10px;
    }

    .about-title {
        color: var(--app-font);
        font-size: 30px;
        font-weight: 750;
        letter-spacing: -0.8px;
        margin-bottom: 8px;
    }

    .about-subtitle {
        color: var(--app-muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
    }

    .about-description {
        color: var(--app-secondary);
        font-size: 15px;
        line-height: 1.8;
        max-width: 850px;
        margin-top: 20px;
    }

    .about-section {
        margin-top: 28px;
        margin-bottom: 12px;
    }

    .about-footer {
        border-top: 1px solid var(--app-border);
        margin-top: 30px;
        padding-top: 20px;
        color: var(--app-muted);
        font-size: 13px;
        line-height: 1.7;
    }

    /* ALERTAS */

    [data-testid="stAlert"] {
        background-color: var(--app-surface);
        border: 1px solid var(--app-border);
        border-left: 3px solid var(--app-accent);
        border-radius: 8px;
    }

    [data-testid="stAlert"] p {
        color: var(--app-font);
    }

    /* DIVISÓRIAS E TABELAS */

    hr {
        border-color: var(--app-border);
        opacity: 0.8;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--app-border);
        border-radius: 8px;
        overflow: hidden;
    }

    /* CAMPOS DE ENTRADA */

    [data-testid="stFileUploader"] {
        border-radius: 8px;
    }

    [data-testid="stSelectbox"] label,
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label {
        color: var(--app-font);
        font-weight: 600;
    }

    [data-baseweb="input"],
    [data-baseweb="textarea"] {
        border-color: var(--app-border);
        border-radius: 7px;
    }

    [data-baseweb="select"] > div {
        border-color: var(--app-border);
        border-radius: 7px;
    }

    /* EXPANDERS — DESTAQUE VÉRTICE */

    [data-testid="stExpander"] {
        border: 1px solid rgba(230, 34, 58, 0.35);
        border-left: 3px solid #E6223A;
        border-radius: 8px;
        background-color: var(--app-accent-soft);
        transition:
            border-color 0.2s ease,
            background-color 0.2s ease;
    }

    [data-testid="stExpander"] summary {
        color: #E6223A !important;
        font-weight: 650;
        transition:
            background-color 0.2s ease,
            color 0.2s ease;
    }

    [data-testid="stExpander"] summary:hover {
        background-color: rgba(230, 34, 58, 0.06);
    }

    [data-testid="stExpander"] summary svg {
        color: #E6223A !important;
        fill: #E6223A !important;
    }

    [data-testid="stExpander"] summary:focus-visible {
        outline: 2px solid #E6223A;
        outline-offset: 2px;
    }

    /* GRÁFICOS */

    [data-testid="stPlotlyChart"] {
        border: 1px solid var(--app-border);
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 18px;
    }

    /* CHAT */

    [data-testid="stChatMessage"] {
        border: 1px solid var(--app-border);
        border-radius: 9px;
    }

    /* LINKS */

    .main a {
        color: var(--app-accent);
        text-decoration: none;
    }

    .main a:hover {
        color: var(--app-accent-hover);
        text-decoration: underline;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 6. FUNÇÃO — SOBRE O PROJETO
# =========================================================

def render_about_project():

    st.html(
    """
    <div class="about-hero">

        <div class="about-eyebrow">
            DATA INTELLIGENCE PLATFORM
        </div>

        <div class="about-title">
            VÉRTICE
        </div>

        <div class="about-subtitle">
            FROM DATA TO DECISIONS.
        </div>

        <div class="about-description">
            Uma plataforma de inteligência de dados desenvolvida
            para transformar bases estruturadas em indicadores,
            descobertas analíticas e informações que apoiam
            a tomada de decisão.
        </div>

    </div>
    """
)

    st.markdown("### Sobre a plataforma")

    st.write(
        """
        O VÉRTICE é uma solução de análise automatizada de dados
        desenvolvida em Python e Streamlit.

        A plataforma combina análise exploratória, métodos
        estatísticos, visualizações interativas e inteligência
        artificial generativa para facilitar a interpretação
        de bases de dados.

        Seu propósito é reduzir o esforço operacional envolvido
        na análise de informações, identificar comportamentos
        relevantes e transformar resultados técnicos em
        conhecimento acessível.
        """
    )

    st.divider()

    st.markdown("### Objetivo")

    st.write(
        """
        Simplificar o processo de análise de dados, automatizando
        etapas de exploração, identificação de indicadores,
        detecção de padrões e consolidação de resultados.

        O VÉRTICE busca aproximar a análise técnica da visão
        executiva, contribuindo para decisões mais estruturadas
        e orientadas por evidências.
        """
    )

    st.divider()

    st.markdown("### Funcionalidades")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("#### Análise e exploração")

        st.markdown(
            """
            - Perfil e qualidade dos dados.
            - Identificação de tipos de informações.
            - Métricas e indicadores automáticos.
            - Visualizações interativas.
            """
        )

        st.markdown("#### Inteligência analítica")

        st.markdown(
            """
            - Identificação de tendências.
            - Análise de concentrações.
            - Insights estatísticos e contextuais.
            - Detecção de anomalias.
            """
        )

    with col2:

        st.markdown("#### Consolidação")

        st.markdown(
            """
            - Relatórios executivos.
            - Exportação de indicadores.
            - Download de insights.
            - Consolidação dos resultados.
            """
        )

        st.markdown("#### Inteligência artificial")

        st.markdown(
            """
            - Interpretação dos insights.
            - Análise textual dos resultados.
            - Apoio à compreensão dos indicadores.
            - Geração de interpretações executivas.
            """
        )

    st.divider()

    st.markdown("### Tecnologias")

    tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)

    with tech_col1:
        st.markdown("**Python**")
        st.caption("Linguagem de desenvolvimento.")

    with tech_col2:
        st.markdown("**Streamlit**")
        st.caption("Interface e aplicação interativa.")

    with tech_col3:
        st.markdown("**Pandas / Plotly**")
        st.caption("Manipulação e visualização de dados.")

    with tech_col4:
        st.markdown("**Gemini API**")
        st.caption("Interpretação com IA generativa.")

    st.divider()

    st.markdown("### Privacidade e responsabilidade")

    st.write(
        """
        A integração com inteligência artificial utiliza
        os insights consolidados para gerar interpretações.

        A base original e o detalhamento de anomalias não são
        enviados para a API Gemini pela funcionalidade de IA
        desta aplicação.

        Os resultados estatísticos e as interpretações geradas
        devem ser avaliados dentro do contexto de cada base.
        A inteligência artificial funciona como apoio analítico
        e não substitui a validação dos dados ou o julgamento
        profissional.
        """
    )

    st.markdown(
        """
        <div class="about-footer">
            <strong>VÉRTICE</strong><br>
            Transformando dados em perspectivas,
            análises em conhecimento e conhecimento em decisões.
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 7. BARRA LATERAL
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-symbol">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <div class="brand-copy">
                <div class="brand-name">Vértice Insights</div>
                <div class="brand-product">DATA INTELLIGENCE</div>
            </div>
        </div>

        <div class="brand-subtitle">
            DATA INTELLIGENCE PLATFORM
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### Nova análise")

    file = st.file_uploader(
        "Carregar base de dados",
        type=["csv", "xlsx", "xls"],
        help="Envie uma planilha CSV ou Excel."
    )

    st.divider()

    st.markdown("### Sobre o projeto")

    st.caption(
        "Plataforma de análise automatizada de dados "
        "com estatística, inteligência de negócios "
        "e IA generativa."
    )

    st.divider()

    st.markdown("### Recursos")

    st.markdown(
        """
        - Perfil de dados
        - Métricas automáticas
        - Gráficos interativos
        - Insights estatísticos
        - Análises contextuais
        - Detecção de anomalias
        - Relatórios executivos
        - Inteligência artificial
        """
    )

    st.divider()

    st.caption("VÉRTICE · v1.5")


# =========================================================
# 8. TELA INICIAL
# =========================================================

if not file:

    st.markdown(
        """
        <div class="workspace-kicker">
            DATA INTELLIGENCE PLATFORM
        </div>
        """,
        unsafe_allow_html=True
    )

    st.html(
        """
        <div class="welcome-card">

            <div class="welcome-eyebrow">
                VÉRTICE · DATA INTELLIGENCE
            </div>

            <div class="welcome-title">
                Sua análise começa aqui.
            </div>

            <div class="welcome-text">
                Transforme planilhas em indicadores,
                descobertas e recomendações executivas.

                <br><br>

                Carregue uma base de dados para iniciar
                uma análise automatizada com inteligência
                estatística e IA generativa.
            </div>

        </div>
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("#### Métricas")

        st.caption(
            "Identificação automática de indicadores "
            "e comportamento dos dados."
        )

    with col2:

        st.markdown("#### Descobertas")

        st.caption(
            "Tendências, concentrações e "
            "anomalias estatísticas."
        )

    with col3:

        st.markdown("#### Inteligência")

        st.caption(
            "Interpretação executiva com "
            "inteligência artificial."
        )

    st.info(
        "Para começar, utilize o campo de upload "
        "na barra lateral. Você também pode testar "
        "os arquivos fictícios da pasta samples."
    )

    st.caption(
        "Privacidade: não carregue dados pessoais, "
        "sensíveis, confidenciais ou corporativos."
    )

    st.divider()

    with st.expander("Conheça o VÉRTICE"):

        render_about_project()

    st.stop()


# =========================================================
# 9. PROCESSAMENTO DO ARQUIVO
# =========================================================

try:

    file_hash = hashlib.sha256(
        file.getvalue()
    ).hexdigest()

    sheet = None

    if file.name.lower().endswith((".xlsx", ".xls")):

        xls = pd.ExcelFile(file)

        sheet = st.selectbox(
            "Selecione a aba da planilha",
            xls.sheet_names
        )

        file.seek(0)

    analysis_identity = f"{file_hash}_{sheet}"

    if st.session_state.get("analysis_identity") != analysis_identity:

        st.session_state["analysis_identity"] = analysis_identity

        st.session_state["ai_analysis_result"] = None

    df = load_uploaded_file(
        file,
        sheet_name=sheet
    )

    if df.empty:

        st.warning(
            "O arquivo não contém registros para análise."
        )

        st.stop()

    # =====================================================
    # 10. CABEÇALHO DA ANÁLISE
    # =====================================================

    st.markdown(
        """
        <div class="workspace-kicker">
            DATA INTELLIGENCE PLATFORM / WORKSPACE
        </div>
        """,
        unsafe_allow_html=True
    )

    st.title("Análise de dados")

    st.caption(
        f"Arquivo: {file.name} · "
        f"{len(df):,} registros · "
        f"{len(df.columns)} colunas"
    )

    st.success("Base carregada e pronta para análise.")

    # =====================================================
    # 11. PROCESSAMENTO ANALÍTICO
    # =====================================================

    profile = profile_dataframe(df)

    metrics = generate_metrics(df)

    charts = generate_charts(
        df,
        limit=5
    )

    for chart_index, chart in enumerate(charts):

        apply_chart_palette(
            chart.get("figura"),
            chart_index
        )

    statistical_insights = generate_insights(df)

    contextual_insights = generate_context_insights(df)

    insights = pd.concat(
        [
            statistical_insights,
            contextual_insights
        ],
        ignore_index=True
    )

    anomaly_details = generate_anomaly_details(df)

    executive_report = create_executive_summary(
        metrics,
        insights,
        anomaly_details
    )

    # =====================================================
    # 12. VISÃO GERAL
    # =====================================================

    st.subheader("Visão geral")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Registros",
        f"{len(df):,}".replace(",", ".")
    )

    col2.metric(
        "Colunas",
        len(df.columns)
    )

    col3.metric(
        "Células vazias",
        f"{int(df.isna().sum().sum()):,}".replace(",", ".")
    )

    col4.metric(
        "Duplicidades",
        f"{int(df.duplicated().sum()):,}".replace(",", ".")
    )

    # =====================================================
    # 13. ORGANIZAÇÃO EM ABAS
    # =====================================================

    tabs = st.tabs(
        [
            "Visão geral",
            "Dados",
            "Indicadores",
            "Insights",
            "Anomalias",
            "Relatório executivo",
            "IA",
            "Sobre o projeto"
        ]
    )

    # =====================================================
    # ABA 1 — VISÃO GERAL
    # =====================================================

    with tabs[0]:

        st.subheader("Resumo da análise")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Métricas",
            len(metrics)
        )

        col2.metric(
            "Insights",
            len(insights)
        )

        col3.metric(
            "Anomalias",
            len(anomaly_details)
        )

        st.divider()

        st.markdown("### Visualizações automáticas")

        if charts:

            for chart in charts:

                st.markdown(
                    f"#### {chart['titulo']}"
                )

                st.plotly_chart(
                    chart["figura"],
                    use_container_width=True,
                    theme="streamlit"
                )

        else:

            st.info(
                "Não foram identificadas combinações "
                "adequadas para geração de gráficos."
            )

    # =====================================================
    # ABA 2 — DADOS
    # =====================================================

    with tabs[1]:

        st.subheader("Perfil das colunas")

        st.dataframe(
            profile,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Baixar perfil da base",
            profile.to_csv(
                index=False
            ).encode("utf-8-sig"),
            "perfil_da_base.csv",
            "text/csv"
        )

        st.divider()

        st.subheader("Prévia dos dados")

        st.dataframe(
            df.head(20),
            use_container_width=True
        )

        st.divider()

        st.subheader("Cobertura temporal")

        dates = profile.loc[
            profile["Tipo identificado"] == "Data",
            "Coluna"
        ].tolist()

        if dates:

            selected_date = st.selectbox(
                "Campo de data",
                dates
            )

            parsed = pd.to_datetime(
                df[selected_date],
                errors="coerce",
                dayfirst=True
            ).dropna()

            if not parsed.empty:

                st.write(
                    f"Período: **{parsed.min().date()} "
                    f"até {parsed.max().date()}**"
                )

            else:

                st.info(
                    "Não foi possível determinar o período."
                )

        else:

            st.info(
                "Nenhuma coluna de data foi identificada "
                "com confiança suficiente."
            )

    # =====================================================
    # ABA 3 — INDICADORES
    # =====================================================

    with tabs[2]:

        st.subheader("Métricas automáticas")

        if not metrics.empty:

            st.success(
                f"{len(metrics)} métricas identificadas."
            )

            st.dataframe(
                metrics,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Baixar métricas (CSV)",
                metrics.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                "metricas_automaticas.csv",
                "text/csv"
            )

        else:

            st.info(
                "Não foram identificadas métricas compatíveis."
            )

    # =====================================================
    # ABA 4 — INSIGHTS
    # =====================================================

    with tabs[3]:

        st.subheader("Insights automáticos")

        if not insights.empty:

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Tendências",
                int((insights["Tipo"] == "Tendência").sum())
            )

            col2.metric(
                "Concentrações",
                int((insights["Tipo"] == "Concentração").sum())
            )

            col3.metric(
                "Anomalias",
                int((insights["Tipo"] == "Anomalia").sum())
            )

            col4.metric(
                "Contextuais",
                int((insights["Tipo"] == "Contextual").sum())
            )

            st.divider()

            st.dataframe(
                insights,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Baixar insights consolidados",
                insights.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                "insights_consolidados.csv",
                "text/csv"
            )

        else:

            st.info(
                "Nenhum insight relevante foi identificado."
            )

    # =====================================================
    # ABA 5 — ANOMALIAS
    # =====================================================

    with tabs[4]:

        st.subheader("Detalhamento de anomalias")

        if not anomaly_details.empty:

            st.warning(
                f"{len(anomaly_details)} registros atípicos identificados."
            )

            st.caption(
                "A linha na base corresponde à posição do "
                "registro no arquivo original, começando em 1. "
                "A identificação estatística não significa "
                "necessariamente que exista um erro."
            )

            st.dataframe(
                anomaly_details,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Baixar registros atípicos",
                anomaly_details.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                "registros_atipicos.csv",
                "text/csv"
            )

            st.metric(
                "Indicadores com anomalias",
                anomaly_details["Indicador"].nunique()
            )

        else:

            st.success(
                "Nenhum registro atípico foi identificado."
            )

    # =====================================================
    # ABA 6 — RELATÓRIO EXECUTIVO
    # =====================================================

    with tabs[5]:

        st.markdown(executive_report)

        st.download_button(
            "Baixar relatório executivo",
            executive_report.encode("utf-8"),
            "relatorio_executivo.md",
            "text/markdown"
        )

    # =====================================================
    # ABA 7 — INTELIGÊNCIA ARTIFICIAL
    # =====================================================

    with tabs[6]:

        st.subheader("Assistente de inteligência")

        st.caption(
            "Interpretação executiva dos insights "
            "calculados pelo sistema."
        )

        st.info(
            "O Gemini recebe somente os insights consolidados. "
            "A base original e o detalhamento de anomalias "
            "não são enviados para a API."
        )

        if insights.empty:

            st.warning(
                "Não existem insights disponíveis "
                "para interpretação com IA."
            )

        else:

            if st.button(
                "Gerar análise com Gemini",
                type="primary"
            ):

                try:

                    api_key = st.secrets.get(
                        "GEMINI_API_KEY"
                    )

                    if not api_key:

                        st.error(
                            "Chave da API Gemini não configurada."
                        )

                    else:

                        with st.spinner(
                            "Analisando os indicadores..."
                        ):

                            ai_result = generate_ai_analysis(
                                insights,
                                api_key
                            )

                        st.session_state[
                            "ai_analysis_result"
                        ] = ai_result

                except Exception as e:

                    st.error(
                        f"Não foi possível gerar a análise: {e}"
                    )

            ai_result = st.session_state.get(
                "ai_analysis_result"
            )

            if ai_result:

                st.divider()

                st.chat_message("assistant").markdown(
                    ai_result
                )

                st.download_button(
                    "Baixar análise com IA",
                    ai_result.encode("utf-8"),
                    "analise_inteligente_ia.md",
                    "text/markdown"
                )

                st.caption(
                    "A análise gerada por IA é interpretativa. "
                    "Valide as conclusões antes de utilizá-las "
                    "em decisões."
                )

    # =====================================================
    # ABA 8 — SOBRE O PROJETO
    # =====================================================

    with tabs[7]:

        render_about_project()

    # =====================================================
    # 14. CRITÉRIOS DE CLASSIFICAÇÃO
    # =====================================================

    with st.expander("Critérios de classificação"):

        st.markdown(
            """
            **Perfil dos dados**

            - Numérico: números e indicadores estatísticos.
            - Data: valores interpretáveis como datas.
            - Categoria: grupos e classificações.
            - Texto: campos descritivos.
            - Booleano: verdadeiro/falso.

            **Métricas e visualizações**

            As agregações são sugestões automáticas
            baseadas na estrutura e nos nomes dos campos.

            **Insights estatísticos**

            - Tendências: comparação entre duas metades
              do período analisado.
            - Concentração: categorias com participação
              igual ou superior a 40%.
            - Anomalias: identificação estatística pelo
              método IQR.

            **Insights contextuais**

            - Estoque: materiais abaixo do estoque mínimo,
              necessidade de reposição e estimativa financeira.
            - Manutenção: distribuição por status,
              prioridades e tempo de conclusão.

            **Inteligência artificial**

            Interpretação dos insights consolidados por
            um modelo generativo. A IA não substitui
            a validação dos dados nem a análise técnica.

            Os resultados são exploratórios e não
            representam, isoladamente, conclusões
            definitivas sobre o negócio.
            """
        )


# =========================================================
# 15. TRATAMENTO GLOBAL DE ERROS
# =========================================================

except Exception as e:

    st.error(
        "Ocorreu um erro durante o processamento da análise."
    )

    with st.expander("Detalhes técnicos do erro"):

        st.exception(e)