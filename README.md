# Automated Insights Generator

Aplicação de portfólio em Python + Streamlit para carregar arquivos CSV/Excel e reconhecer automaticamente a estrutura dos dados.

## Versão 0.1
- Upload de CSV, XLSX e XLS.
- Seleção de aba em Excel.
- Perfil das colunas e inferência heurística de tipos.
- Contagem de registros, colunas, vazios e duplicidades.
- Prévia dos dados e identificação de período, quando possível.
- Exportação do perfil em CSV.

## Executar no Windows
1. `python -m venv .venv`
2. `.venv\\Scripts\\Activate.ps1`
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

## Estrutura
`app.py` é a interface; `modules/data_loader.py` lê arquivos; `modules/data_profiler.py` identifica os campos. Os demais módulos reservam espaço para métricas, gráficos, insights e relatório executivo.

## Próximas etapas
1. Indicadores automáticos adequados aos campos disponíveis.
2. Gráficos sugeridos conforme a estrutura.
3. Insights baseados em regras verificáveis.
4. Resumo executivo e exportação.
5. Camada opcional de IA generativa para redigir explicações a partir dos resultados calculados.

## Governança
Use apenas dados fictícios ou devidamente anonimizados no portfólio. Não carregue dados pessoais, sensíveis, confidenciais ou corporativos em ambientes públicos. O perfil não é auditoria formal nem certificação de qualidade. Inferências de tipo podem falhar e precisam de revisão.
