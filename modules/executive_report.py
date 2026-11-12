import re
import unicodedata


def normalize_text(text):
    """
    Normaliza textos para facilitar comparações,
    removendo acentos e padronizando letras minúsculas.
    """
    text = str(text).lower().strip()

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    return text


def classify_criticality(row):
    """
    Classifica a criticidade considerando primeiro
    o indicador, evitando interferência de palavras
    presentes em outras partes do insight.
    """

    indicator = normalize_text(row.get("Indicador", ""))
    insight = normalize_text(row.get("Insight", ""))
    evidence = normalize_text(row.get("Evidência", ""))

    # ESTOQUE

    if (
        "materiais abaixo do estoque minimo" in indicator
        or "abaixo do estoque minimo" in indicator
        or "abaixo do minimo" in indicator
    ):
        return "Alta"

    if "familia com maior quantidade" in indicator:
        return "Média"

    if (
        "necessidade de reposicao" in indicator
        or "quantidade para reposicao" in indicator
        or "reposicao" in indicator
    ):
        return "Média"

    if "valor estimado para reposicao" in indicator:
        return "Média"

    # MANUTENÇÃO

    if "ordens pendentes" in indicator:
        return "Média"

    if "ordens em execucao" in indicator:
        return "Média"

    if "ordens concluidas" in indicator:
        return "Baixa"

    if "prioridade mais frequente" in indicator:
        return "Baixa"

    if "tipo de manutencao com maior tempo medio" in indicator:
        return "Média"

    if "tempo medio de conclusao" in indicator:
        return "Baixa"

    # ANOMALIAS

    if (
        "anomalia" in indicator
        or "atipico" in indicator
        or "outlier" in indicator
        or "atipico" in insight
        or "outlier" in insight
    ):
        return "Alta"

    # TENDÊNCIAS

    if (
        "diminuiu" in insight
        or "aumentou" in insight
        or "variacao" in indicator
        or "tendencia" in indicator
    ):
        percentage_match = re.search(
            r"(\d+(?:[.,]\d+)?)\s*%",
            insight
        )

        if percentage_match:
            percentage = float(
                percentage_match.group(1).replace(",", ".")
            )

            if percentage >= 15:
                return "Alta"

            if percentage >= 5:
                return "Média"

            return "Baixa"

    # CLASSIFICAÇÕES GERAIS

    if "pendente" in insight or "atras" in insight:
        return "Média"

    if "reposicao" in insight or "repor" in insight:
        return "Média"

    return "Baixa"


def generate_quantitative_highlights(insights, anomaly_details=None):
    """
    Seleciona os principais indicadores quantitativos
    para o resumo executivo.
    """

    highlights = []

    priority_terms = [
        "materiais abaixo do estoque minimo",
        "necessidade de reposicao",
        "valor estimado para reposicao",
        "familia com maior quantidade",
        "ordens pendentes",
        "ordens em execucao",
        "ordens concluidas",
        "prioridade mais frequente",
        "tempo medio de conclusao",
        "tipo de manutencao com maior tempo medio",
        "preco_unitario",
        "valor_total"
    ]

    for _, row in insights.iterrows():

        indicator = normalize_text(
            row.get("Indicador", "")
        )

        insight = str(row.get("Insight", ""))

        if any(term in indicator for term in priority_terms):

            highlights.append(
                f"- **{row.get('Indicador', 'Indicador')}:** {insight}"
            )

    # Inclui os registros anômalos identificados,
    # sem alterar os cálculos estatísticos originais.

    if (
        anomaly_details is not None
        and not anomaly_details.empty
    ):

        for _, row in anomaly_details.iterrows():

            highlights.append(
                "- **Anomalia identificada:** "
                f"{row.get('Indicador', 'Não informado')} "
                f"com valor {row.get('Valor atípico', 'Não informado')} "
                f"na linha {row.get('Linha na base', 'Não informada')} "
                f"({row.get('Classificação', 'Classificação não informada')})."
            )

    if not highlights:
        return "Não foram identificados indicadores prioritários."

    return "\n".join(highlights)


def generate_maintenance_comparison(insights):
    """
    Compara o tempo médio geral de conclusão
    com o tipo de manutenção de maior duração.
    """

    general_average = None
    highest_average = None
    maintenance_type = None

    for _, row in insights.iterrows():

        indicator = normalize_text(
            row.get("Indicador", "")
        )

        insight = str(row.get("Insight", ""))
        evidence = str(row.get("Evidência", ""))

        if (
            "tempo medio de conclusao" in indicator
            and "tipo de manutencao" not in indicator
        ):

            values = re.findall(
                r"\d+(?:[.,]\d+)?",
                insight + " " + evidence
            )

            if values:
                general_average = float(
                    values[0].replace(",", ".")
                )

        elif (
            "tipo de manutencao" in indicator
            or "preventiva" in normalize_text(evidence)
        ):

            values = re.findall(
                r"\d+(?:[.,]\d+)?",
                insight + " " + evidence
            )

            if values:
                highest_average = float(
                    values[0].replace(",", ".")
                )

            if "preventiva" in normalize_text(insight):
                maintenance_type = "Preventiva"

            elif "corretiva" in normalize_text(insight):
                maintenance_type = "Corretiva"

    if (
        general_average is None
        or highest_average is None
        or general_average == 0
    ):
        return None

    difference = highest_average - general_average

    variation = (
        difference / general_average
    ) * 100

    type_description = (
        maintenance_type
        if maintenance_type
        else "tipo identificado"
    )

    return (
        f"O tempo médio de conclusão das ordens é de "
        f"**{general_average:.1f} dias**. "
        f"O tipo de manutenção com maior tempo médio é "
        f"**{type_description}**, com **{highest_average:.1f} dias**, "
        f"uma diferença de **{difference:.1f} dias "
        f"({variation:.1f}%)** em relação à média geral."
    )


def generate_anomaly_details_section(anomaly_details):
    """
    Formata os registros anômalos para o relatório executivo.
    """

    if (
        anomaly_details is None
        or anomaly_details.empty
    ):
        return None

    details = []

    for _, row in anomaly_details.iterrows():

        details.append(
            f"- **Linha na base:** {row.get('Linha na base', 'Não informada')}\n"
            f"  - **Indicador:** {row.get('Indicador', 'Não informado')}\n"
            f"  - **Valor atípico:** {row.get('Valor atípico', 'Não informado')}\n"
            f"  - **Classificação:** {row.get('Classificação', 'Não informada')}\n"
            f"  - **Limite inferior:** {row.get('Limite inferior', 'Não informado')}\n"
            f"  - **Limite superior:** {row.get('Limite superior', 'Não informado')}"
        )

        if "Grupo" in anomaly_details.columns:

            details.append(
                f"  - **Grupo:** {row.get('Grupo', 'Não informado')}"
            )

        contextual_fields = [
            ("data_lancamento", "Data de lançamento"),
            ("categoria_despesa", "Categoria"),
            ("centro_custo", "Centro de custo"),
            ("valor", "Valor"),
            ("status_pagamento", "Status do pagamento")
        ]

        for field, label in contextual_fields:

            if field in anomaly_details.columns:

                value = row.get(field)

                if value is not None:
                    details.append(
                        f"  - **{label}:** {value}"
                    )

        details.append("")

    return "\n".join(details)


def generate_recommendations(insights, anomaly_details=None):
    """
    Gera recomendações direcionadas conforme
    os indicadores encontrados na base.
    """

    recommendations = []

    for _, row in insights.iterrows():

        indicator = normalize_text(
            row.get("Indicador", "")
        )

        insight = normalize_text(
            row.get("Insight", "")
        )

        # ESTOQUE

        if (
            "materiais abaixo do estoque minimo" in indicator
            or "abaixo do estoque minimo" in indicator
            or "abaixo do minimo" in indicator
        ):

            recommendations.append(
                "Priorizar a análise dos materiais abaixo do estoque "
                "mínimo e avaliar a necessidade de reposição."
            )

        elif (
            "necessidade de reposicao" in indicator
            or "quantidade para reposicao" in indicator
        ):

            recommendations.append(
                "Planejar a reposição das quantidades identificadas, "
                "considerando a disponibilidade e a prioridade dos materiais."
            )

        elif "valor estimado para reposicao" in indicator:

            recommendations.append(
                "Avaliar o impacto financeiro estimado da reposição "
                "e considerar o valor no planejamento orçamentário."
            )

        elif "familia com maior quantidade" in indicator:

            recommendations.append(
                "Analisar os materiais críticos da família identificada "
                "e verificar oportunidades de ajuste nos níveis de estoque."
            )

        # MANUTENÇÃO

        elif "ordens pendentes" in indicator:

            recommendations.append(
                "Avaliar as ordens pendentes, priorizando aquelas com "
                "maior impacto operacional e maior tempo de espera."
            )

        elif "ordens em execucao" in indicator:

            recommendations.append(
                "Acompanhar as ordens em execução para identificar "
                "possíveis impedimentos e evitar prolongamento dos atendimentos."
            )

        elif "ordens concluidas" in indicator:

            recommendations.append(
                "Acompanhar a evolução das ordens concluídas em relação "
                "ao volume total de solicitações."
            )

        elif "prioridade mais frequente" in indicator:

            recommendations.append(
                "Avaliar a distribuição das prioridades para verificar "
                "se os critérios de classificação estão adequados."
            )

        elif "tipo de manutencao com maior tempo medio" in indicator:

            recommendations.append(
                "Investigar os fatores que contribuem para o maior tempo "
                "médio de conclusão do tipo de manutenção identificado."
            )

        elif "tempo medio de conclusao" in indicator:

            recommendations.append(
                "Monitorar o tempo médio de conclusão das ordens "
                "para acompanhar a eficiência dos atendimentos."
            )

        # VENDAS

        elif "preco_unitario" in indicator:

            recommendations.append(
                "Investigar os fatores que explicam a variação do preço "
                "unitário e avaliar seus impactos nos resultados comerciais."
            )

        elif "valor_total" in indicator:

            recommendations.append(
                "Analisar os fatores associados à variação do valor total "
                "e acompanhar sua evolução nos próximos períodos."
            )

        # ANOMALIAS

        elif (
            "anomalia" in indicator
            or "atipico" in indicator
            or "outlier" in indicator
            or "atipico" in insight
            or "outlier" in insight
        ):

            # Quando há detalhes disponíveis, a recomendação
            # contextual será gerada abaixo.
            if (
                anomaly_details is None
                or anomaly_details.empty
            ):

                recommendations.append(
                    "Validar os registros identificados como atípicos "
                    "para verificar se representam situações legítimas "
                    "ou inconsistências nos dados."
                )

    # RECOMENDAÇÕES CONTEXTUAIS PARA ANOMALIAS

    if (
        anomaly_details is not None
        and not anomaly_details.empty
    ):

        for _, row in anomaly_details.iterrows():

            category = row.get("categoria_despesa")
            cost_center = row.get("centro_custo")
            payment_status = row.get("status_pagamento")

            context_parts = []

            if category is not None:
                context_parts.append(
                    f"categoria {category}"
                )

            if cost_center is not None:
                context_parts.append(
                    f"centro de custo {cost_center}"
                )

            if payment_status is not None:
                context_parts.append(
                    f"status de pagamento {payment_status}"
                )

            if context_parts:

                context = ", ".join(context_parts)

                recommendations.append(
                    "Validar o registro atípico considerando "
                    f"{context}, verificando sua origem e documentação "
                    "antes de qualquer ajuste."
                )

            else:

                recommendations.append(
                    "Validar a origem e a documentação do registro "
                    "atípico antes de qualquer ajuste."
                )

    # Remove recomendações repetidas, preservando a ordem.

    unique_recommendations = []

    for recommendation in recommendations:

        if recommendation not in unique_recommendations:
            unique_recommendations.append(recommendation)

    if not unique_recommendations:

        return [
            "Manter o acompanhamento periódico dos indicadores "
            "e revisar os resultados conforme a evolução da base."
        ]

    return unique_recommendations


def create_executive_summary(
    metrics,
    insights,
    anomaly_details=None
):
    """
    Monta o relatório executivo em Markdown.
    """

    report = []

    report.append("# Relatório Executivo")
    report.append("")

    report.append("## Resumo da análise")
    report.append("")

    report.append(
        f"- Métricas calculadas: **{len(metrics)}**"
    )

    report.append(
        f"- Insights identificados: **{len(insights)}**"
    )

    report.append("")

    # DESTAQUES QUANTITATIVOS

    report.append("## Principais indicadores")
    report.append("")

    report.append(
        generate_quantitative_highlights(
            insights,
            anomaly_details
        )
    )

    report.append("")

    # CLASSIFICAÇÃO DE CRITICIDADE

    criticality_counts = {
        "Alta": 0,
        "Média": 0,
        "Baixa": 0
    }

    for _, row in insights.iterrows():

        criticality = classify_criticality(row)

        criticality_counts[criticality] += 1

    report.append("## Classificação por criticidade")
    report.append("")

    report.append(
        f"- **Alta:** {criticality_counts['Alta']}"
    )

    report.append(
        f"- **Média:** {criticality_counts['Média']}"
    )

    report.append(
        f"- **Baixa:** {criticality_counts['Baixa']}"
    )

    report.append("")

    # PRINCIPAIS DESCOBERTAS

    report.append("## Principais descobertas")
    report.append("")

    if insights.empty:

        report.append(
            "Nenhum insight relevante foi identificado."
        )

    else:

        for _, row in insights.iterrows():

            criticality = classify_criticality(row)

            report.append(
                f"- **{row.get('Indicador', 'Indicador')} "
                f"({criticality}):** "
                f"{row.get('Insight', '')}"
            )

            evidence = row.get("Evidência")

            if evidence:
                report.append(
                    f"  - Evidência: {evidence}"
                )

    report.append("")

    # COMPARAÇÃO DE MANUTENÇÃO

    maintenance_comparison = generate_maintenance_comparison(
        insights
    )

    if maintenance_comparison:

        report.append(
            "## Análise comparativa de manutenção"
        )

        report.append("")

        report.append(
            maintenance_comparison
        )

        report.append("")

    # ANOMALIAS

    anomaly_section = generate_anomaly_details_section(
        anomaly_details
    )

    if anomaly_section:

        report.append(
            "## Detalhamento dos registros anômalos"
        )

        report.append("")

        report.append(anomaly_section)

        report.append("")

        report.append(
            "**Observação:** registros atípicos são pontos "
            "que se diferenciam do comportamento estatístico "
            "da base. Isso não significa necessariamente erro, "
            "fraude ou perda financeira. A validação deve considerar "
            "o contexto operacional."
        )

        report.append("")

    # PONTOS DE ATENÇÃO

    attention_points = []
    seen_attention = set()

    for _, row in insights.iterrows():

        attention = row.get("Atenção")

        if attention and str(attention).strip():

            attention_text = str(attention).strip()

            # Normaliza apenas para identificar duplicidades.
            # O texto original é preservado no relatório.

            attention_key = normalize_text(
                " ".join(attention_text.split())
            )

            if attention_key not in seen_attention:

                seen_attention.add(attention_key)

                attention_points.append(
                    f"- {attention_text}"
                )

    report.append("## Pontos de atenção")
    report.append("")

    if attention_points:

        report.extend(attention_points)

    else:

        report.append(
            "Não foram identificados pontos adicionais de atenção."
        )

    report.append("")

    # RECOMENDAÇÕES

    recommendations = generate_recommendations(
        insights,
        anomaly_details
    )

    report.append("## Recomendações")
    report.append("")

    for recommendation in recommendations:

        report.append(
            f"- {recommendation}"
        )

    report.append("")

    report.append("---")
    report.append(
        "*Relatório gerado automaticamente pelo "
        "Automated Insights Generator.*"
    )

    return "\n".join(report)