import pandas as pd
import unicodedata


OUTPUT_COLUMNS = [
    "Tipo",
    "Indicador",
    "Agregação",
    "Insight",
    "Evidência",
    "Atenção"
]


def normalize_text(value):
    text = str(value).lower().strip()

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    return text.replace(" ", "_")


def find_column(df, terms):

    normalized_columns = {
        normalize_text(column): column
        for column in df.columns
    }

    for term in terms:

        normalized_term = normalize_text(term)

        if normalized_term in normalized_columns:
            return normalized_columns[normalized_term]

    for column in df.columns:

        normalized_column = normalize_text(column)

        for term in terms:

            normalized_term = normalize_text(term)

            if normalized_term in normalized_column:
                return column

    return None


def add_insight(
    insights,
    indicator,
    aggregation,
    insight,
    evidence,
    attention
):

    insights.append({
        "Tipo": "Contextual",
        "Indicador": indicator,
        "Agregação": aggregation,
        "Insight": insight,
        "Evidência": evidence,
        "Atenção": attention
    })


# =====================================================
# ANÁLISE DE ESTOQUE
# =====================================================

def analyze_stock(df):

    insights = []

    current_column = find_column(
        df,
        [
            "estoque_atual",
            "quantidade_atual",
            "saldo_atual",
            "qtd_estoque",
            "quantidade_estoque"
        ]
    )

    minimum_column = find_column(
        df,
        [
            "estoque_minimo",
            "quantidade_minima",
            "saldo_minimo",
            "qtd_minima"
        ]
    )

    cost_column = find_column(
        df,
        [
            "custo_unitario",
            "preco_unitario",
            "valor_unitario"
        ]
    )

    family_column = find_column(
        df,
        [
            "familia",
            "categoria",
            "grupo",
            "tipo_material"
        ]
    )

    if current_column is None or minimum_column is None:
        return insights

    data = df.copy()

    data[current_column] = pd.to_numeric(
        data[current_column],
        errors="coerce"
    )

    data[minimum_column] = pd.to_numeric(
        data[minimum_column],
        errors="coerce"
    )

    valid_data = data.dropna(
        subset=[current_column, minimum_column]
    )

    if valid_data.empty:
        return insights

    below_minimum = valid_data[
        valid_data[current_column] < valid_data[minimum_column]
    ].copy()

    total_items = len(valid_data)

    affected_items = len(below_minimum)

    percentage = (
        affected_items / total_items
    ) * 100

    if affected_items > 0:

        add_insight(
            insights,
            "Materiais abaixo do estoque mínimo",
            "Contagem",
            (
                f"{affected_items} de {total_items} materiais "
                f"estão abaixo do estoque mínimo "
                f"({percentage:.1f}% do total)."
            ),
            (
                f"Materiais analisados: {total_items} | "
                f"Abaixo do mínimo: {affected_items} | "
                f"Percentual: {percentage:.1f}%"
            ),
            "Avaliar necessidade de reposição."
        )

        below_minimum["necessidade_reposicao"] = (
            below_minimum[minimum_column]
            - below_minimum[current_column]
        )

        total_replenishment = (
            below_minimum["necessidade_reposicao"].sum()
        )

        add_insight(
            insights,
            "Necessidade de reposição",
            "Soma",
            (
                f"São necessárias {total_replenishment:.0f} "
                f"unidades para que os materiais identificados "
                f"atinjam seus respectivos estoques mínimos."
            ),
            (
                f"Unidades necessárias: "
                f"{total_replenishment:.0f}"
            ),
            "Validar quantidades e disponibilidade de fornecimento."
        )

        if cost_column is not None:

            below_minimum[cost_column] = pd.to_numeric(
                below_minimum[cost_column],
                errors="coerce"
            )

            estimated_value = (
                below_minimum["necessidade_reposicao"]
                * below_minimum[cost_column]
            ).sum(min_count=1)

            if pd.notna(estimated_value):

                add_insight(
                    insights,
                    "Valor estimado para reposição",
                    "Soma",
                    (
                        f"O valor estimado para atingir o estoque "
                        f"mínimo é de {estimated_value:,.2f}."
                    ),
                    (
                        f"Valor estimado: "
                        f"{estimated_value:,.2f}"
                    ),
                    (
                        "Estimativa baseada no custo unitário "
                        "disponível. Não representa cotação ou "
                        "valor aprovado."
                    )
                )

        if family_column is not None:

            family_counts = (
                below_minimum[family_column]
                .value_counts()
            )

            if not family_counts.empty:

                main_family = family_counts.index[0]

                main_count = family_counts.iloc[0]

                add_insight(
                    insights,
                    "Família com maior quantidade de itens críticos",
                    "Contagem",
                    (
                        f"A família {main_family} concentra "
                        f"{main_count} materiais abaixo do "
                        f"estoque mínimo."
                    ),
                    (
                        f"Família: {main_family} | "
                        f"Materiais: {main_count}"
                    ),
                    "Avaliar concentração das necessidades de reposição."
                )

    return insights


# =====================================================
# ANÁLISE DE MANUTENÇÃO
# =====================================================

def analyze_maintenance(df):

    insights = []

    status_column = find_column(
        df,
        [
            "status_ordem",
            "status",
            "situacao_ordem",
            "situacao"
        ]
    )

    priority_column = find_column(
        df,
        [
            "prioridade",
            "nivel_prioridade"
        ]
    )

    response_column = find_column(
        df,
        [
            "tempo_resposta_dias",
            "tempo_atendimento_dias",
            "dias_resposta",
            "tempo_resposta"
        ]
    )

    maintenance_type_column = find_column(
        df,
        [
            "tipo_manutencao",
            "tipo_de_manutencao",
            "categoria_manutencao"
        ]
    )

    total_orders = len(df)

    if total_orders == 0:
        return insights

    # ---------------------------------------------
    # DISTRIBUIÇÃO POR STATUS
    # ---------------------------------------------

    if status_column is not None:

        statuses = (
            df[status_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        normalized_statuses = statuses.map(normalize_text)

        pending_mask = normalized_statuses.isin([
            "pendente",
            "aberta",
            "aberto",
            "aguardando",
            "aguardando_execucao"
        ])

        execution_mask = normalized_statuses.isin([
            "em_execucao",
            "em_andamento",
            "em_progresso",
            "em_atendimento"
        ])

        completed_mask = normalized_statuses.isin([
            "concluida",
            "concluido",
            "finalizada",
            "finalizado",
            "encerrada",
            "encerrado"
        ])

        pending = int(pending_mask.sum())
        execution = int(execution_mask.sum())
        completed = int(completed_mask.sum())

        if pending > 0:

            add_insight(
                insights,
                "Ordens pendentes",
                "Contagem",
                (
                    f"Existem {pending} ordens pendentes, "
                    f"representando "
                    f"{pending / total_orders * 100:.1f}% "
                    f"do total."
                ),
                (
                    f"Ordens pendentes: {pending} | "
                    f"Total de ordens: {total_orders}"
                ),
                "Avaliar o volume de ordens aguardando execução."
            )

        if execution > 0:

            add_insight(
                insights,
                "Ordens em execução",
                "Contagem",
                (
                    f"Existem {execution} ordens em execução, "
                    f"representando "
                    f"{execution / total_orders * 100:.1f}% "
                    f"do total."
                ),
                (
                    f"Ordens em execução: {execution} | "
                    f"Total de ordens: {total_orders}"
                ),
                "Acompanhar a evolução das ordens em andamento."
            )

        if completed > 0:

            add_insight(
                insights,
                "Ordens concluídas",
                "Contagem",
                (
                    f"{completed} ordens foram concluídas, "
                    f"representando "
                    f"{completed / total_orders * 100:.1f}% "
                    f"do total."
                ),
                (
                    f"Ordens concluídas: {completed} | "
                    f"Total de ordens: {total_orders}"
                ),
                "Acompanhar a proporção de ordens concluídas."
            )

    else:
        completed_mask = None

    # ---------------------------------------------
    # DISTRIBUIÇÃO POR PRIORIDADE
    # ---------------------------------------------

    if priority_column is not None:

        priorities = (
            df[priority_column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        priority_counts = priorities.value_counts()

        if not priority_counts.empty:

            main_priority = priority_counts.index[0]

            main_count = priority_counts.iloc[0]

            add_insight(
                insights,
                "Prioridade mais frequente",
                "Contagem",
                (
                    f"A prioridade {main_priority} "
                    f"é a mais frequente, com "
                    f"{main_count} ordens."
                ),
                (
                    f"Prioridade: {main_priority} | "
                    f"Quantidade: {main_count}"
                ),
                "Verificar se a distribuição está alinhada à criticidade."
            )

    # ---------------------------------------------
    # TEMPO DE CONCLUSÃO
    # SOMENTE ORDENS CONCLUÍDAS
    # ---------------------------------------------

    if (
        response_column is not None
        and status_column is not None
    ):

        completed_data = df.loc[completed_mask].copy()

        completed_data[response_column] = pd.to_numeric(
            completed_data[response_column],
            errors="coerce"
        )

        response_values = (
            completed_data[response_column]
            .dropna()
        )

        if not response_values.empty:

            average_response = response_values.mean()

            median_response = response_values.median()

            add_insight(
                insights,
                "Tempo médio de conclusão",
                "Média",
                (
                    f"O tempo médio entre a criação e a "
                    f"conclusão das ordens é de "
                    f"{average_response:.1f} dias."
                ),
                (
                    f"Média: {average_response:.1f} dias | "
                    f"Mediana: {median_response:.1f} dias | "
                    f"Ordens concluídas analisadas: "
                    f"{len(response_values)}"
                ),
                (
                    "Comparar com a meta de conclusão, "
                    "caso exista uma meta definida."
                )
            )

            # Comparação por tipo de manutenção

            if maintenance_type_column is not None:

                grouped = (
                    completed_data
                    .groupby(maintenance_type_column)[response_column]
                    .mean()
                    .dropna()
                    .sort_values(ascending=False)
                )

                if not grouped.empty:

                    main_type = grouped.index[0]

                    main_average = grouped.iloc[0]

                    add_insight(
                        insights,
                        "Tipo de manutenção com maior tempo médio de conclusão",
                        "Média",
                        (
                            f"A manutenção do tipo {main_type} "
                            f"apresenta o maior tempo médio de "
                            f"conclusão: {main_average:.1f} dias."
                        ),
                        (
                            f"Tipo: {main_type} | "
                            f"Média: {main_average:.1f} dias"
                        ),
                        (
                            "Comparação considera somente ordens "
                            "concluídas. Investigar possíveis "
                            "diferenças de complexidade."
                        )
                    )

    return insights


# =====================================================
# MOTOR PRINCIPAL
# =====================================================

def generate_context_insights(df):

    insights = []

    # Identificação de estoque:
    # exige quantidade atual e quantidade mínima.

    current_stock = find_column(
        df,
        ["estoque_atual", "quantidade_atual",
         "saldo_atual", "qtd_estoque",
         "quantidade_estoque"]
    )

    minimum_stock = find_column(
        df,
        ["estoque_minimo", "quantidade_minima",
         "saldo_minimo", "qtd_minima"]
    )

    if current_stock and minimum_stock:
        insights.extend(analyze_stock(df))

    # Identificação de manutenção:
    # exige status da ordem e algum identificador
    # ou atributo característico de manutenção.

    status_column = find_column(
        df,
        ["status_ordem", "situacao_ordem"]
    )

    maintenance_column = find_column(
        df,
        ["tipo_manutencao", "tipo_de_manutencao",
         "categoria_manutencao"]
    )

    order_column = find_column(
        df,
        ["ordem", "numero_ordem", "ordem_manutencao"]
    )

    if status_column and (maintenance_column or order_column):
        insights.extend(analyze_maintenance(df))

    return pd.DataFrame(
        insights,
        columns=OUTPUT_COLUMNS
    )