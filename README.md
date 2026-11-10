# VÉRTICE | Data Intelligence Platform

**From Data to Decisions.**

Plataforma de inteligência de dados desenvolvida em Python e Streamlit para transformar arquivos estruturados em indicadores, visualizações, descobertas analíticas e informações que apoiam a tomada de decisão.

O VÉRTICE automatiza etapas da análise exploratória, identifica padrões e comportamentos relevantes, detecta possíveis anomalias e consolida resultados em relatórios executivos. Também conta com uma camada opcional de inteligência artificial generativa para apoiar a interpretação dos insights.

---

## Sobre o projeto

O VÉRTICE é uma aplicação de análise automatizada de dados desenvolvida para aproximar a análise técnica da visão executiva.

A plataforma combina processamento de dados, métodos estatísticos, visualizações interativas e inteligência artificial para facilitar a exploração de diferentes bases de dados, reduzindo o esforço operacional necessário para identificar informações relevantes.

Foi desenvolvido com uma arquitetura modular, permitindo organizar as responsabilidades de carregamento, processamento, análise e apresentação dos dados.

## Funcionalidades

### 1. Carregamento e exploração de dados
- Upload de arquivos CSV, XLSX e XLS.
- Seleção de abas em arquivos Excel.
- Leitura e pré-visualização das bases.
- Identificação da estrutura e dos tipos de dados.
- Perfil das colunas e identificação de valores ausentes.
- Verificação de registros duplicados.

### 2. Indicadores automáticos
- Contagem de registros e colunas.
- Identificação de métricas aplicáveis aos campos numéricos.
- Cálculo de soma, média, mediana, mínimo, máximo e desvio-padrão.
- Identificação de categorias distintas e categorias mais frequentes.
- Identificação de períodos e informações temporais, quando disponíveis.

### 3. Visualizações interativas
- Geração automática de gráficos conforme a estrutura dos dados.
- Visualizações construídas com Plotly.
- Representação de distribuições, comparações e comportamentos.
- Apoio à exploração visual dos indicadores.

### 4. Insights analíticos
- Identificação de tendências.
- Análise de concentração por categorias.
- Comparação de indicadores ao longo do tempo, quando aplicável.
- Geração de evidências quantitativas para apoiar a interpretação dos resultados.

### 5. Detecção de anomalias
- Identificação de possíveis valores atípicos.
- Aplicação do método estatístico IQR (Intervalo Interquartil).
- Cálculo de limites inferiores e superiores.
- Identificação e classificação dos registros sinalizados.
- Disponibilização do detalhamento para investigação.

Valores atípicos não representam necessariamente erros. Sua interpretação depende do contexto dos dados.

### 6. Relatório executivo
- Consolidação dos principais resultados da análise.
- Organização de indicadores e descobertas.
- Geração de resumo executivo em Markdown.
- Exportação dos resultados para utilização externa.

### 7. Inteligência artificial
- Integração com a API Google Gemini.
- Interpretação textual dos insights consolidados.
- Apoio à contextualização dos resultados.
- Geração de explicações em linguagem natural.

A inteligência artificial atua como camada complementar de interpretação. Os indicadores e resultados estatísticos são calculados pela própria aplicação.

### 8. Exportação
- Exportação de indicadores e resultados em CSV.
- Download do relatório executivo em Markdown.

## Arquitetura do projeto

O VÉRTICE utiliza uma estrutura modular para separar as responsabilidades e facilitar a manutenção e evolução da aplicação.

```text
automated-insights-generator/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── modules/
│   ├── data_loader.py
│   ├── data_profiler.py
│   ├── metrics_engine.py
│   ├── chart_engine.py
│   ├── insights_engine.py
│   ├── context_engine.py
│   ├── executive_report.py
│   └── ai_analysis.py
│
└── .streamlit/
    └── secrets.toml
```

**Responsabilidades dos principais componentes:**

| Componente | Responsabilidade |
|---|---|
| `app.py` | Interface, navegação e integração dos módulos |
| `data_loader.py` | Carregamento de arquivos |
| `data_profiler.py` | Perfil e caracterização dos dados |
| `metrics_engine.py` | Cálculo dos indicadores |
| `chart_engine.py` | Geração das visualizações |
| `insights_engine.py` | Tendências, concentrações e anomalias |
| `context_engine.py` | Insights contextuais |
| `executive_report.py` | Consolidação do relatório executivo |
| `ai_analysis.py` | Integração com a inteligência artificial |

## Tecnologias utilizadas

- **Python:** linguagem principal de desenvolvimento.
- **Streamlit:** construção da interface interativa.
- **Pandas:** processamento e manipulação de dados.
- **Plotly:** visualizações interativas.
- **Google Gemini API:** interpretação dos insights por inteligência artificial.
- **NumPy:** operações e suporte a cálculos numéricos.

## Instalação e execução

### Requisitos

- Python instalado.
- Git (opcional para clonagem do repositório).
- Chave da API Google Gemini para utilizar a funcionalidade de inteligência artificial.

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
```

Entre na pasta do projeto:

```bash
cd automated-insights-generator
```

### 2. Criar o ambiente virtual

```powershell
python -m venv .venv
```

### 3. Ativar o ambiente virtual

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 5. Configurar a API Gemini

Crie a pasta `.streamlit` na raiz do projeto e, dentro dela, o arquivo `secrets.toml`.

Configure a chave:

```toml
GEMINI_API_KEY = "SUA_CHAVE_DA_API"
```

**Importante:** o arquivo `secrets.toml` contém credenciais privadas e não deve ser enviado ao GitHub.

### 6. Executar a aplicação

```bash
streamlit run app.py
```

A aplicação será disponibilizada localmente pelo Streamlit.

## Organização da interface

A plataforma está organizada em oito áreas de análise:

1. **Visão geral:** apresentação consolidada dos resultados.
2. **Dados:** exploração da estrutura e do perfil da base.
3. **Indicadores:** métricas calculadas automaticamente.
4. **Insights:** descobertas analíticas e contextuais.
5. **Anomalias:** identificação e detalhamento de valores atípicos.
6. **Relatório executivo:** consolidação dos resultados.
7. **IA:** interpretação dos insights com apoio do Gemini.
8. **Sobre o projeto:** apresentação, objetivo, tecnologias e características da plataforma.

## Privacidade e governança

O VÉRTICE foi desenvolvido considerando a necessidade de controle sobre os dados utilizados nas análises.

- A integração com o Gemini utiliza insights consolidados, não a base original nem o detalhamento dos registros atípicos.
- A chave da API deve permanecer em configuração privada.
- Arquivos utilizados em ambientes públicos devem conter dados fictícios ou devidamente anonimizados.
- Dados pessoais, sensíveis, confidenciais ou corporativos não devem ser publicados em repositórios ou ambientes públicos.
- Os resultados dependem da estrutura, qualidade e características da base analisada.

A plataforma oferece apoio à análise exploratória e à tomada de decisão. Não constitui auditoria formal, certificação de qualidade de dados ou substituição da validação profissional.

## Limitações analíticas

A identificação de tipos de dados e a seleção de métricas são realizadas por regras automatizadas e inferências sobre as colunas disponíveis.

Os resultados devem ser interpretados considerando o contexto do negócio. Uma variação estatística, concentração ou anomalia pode representar um comportamento legítimo, e não necessariamente um problema.

A IA generativa também pode produzir interpretações imprecisas. Portanto, seus resultados devem ser revisados antes de serem utilizados em decisões.

## Objetivo

Transformar dados em perspectivas, análises em conhecimento e conhecimento em decisões.

**VÉRTICE — From Data to Decisions.**
