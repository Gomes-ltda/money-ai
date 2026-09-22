import uuid

from memory import registrar_tarefa, atualizar_tarefa, obter_ultimo_ciclo


ACOES_INTERNAS = {
    "aguardar",
    "pesquisar",
    "analisar",
    "criar_oferta",
    "criar_proposta",
    "criar_conteudo",
    "pesquisar_alvo",
    "validar_alvo",
    "preparar_abordagem",
    "preparar_followup",
    "acompanhar_lead",
    "medir_resultado",
    "testar_estrategia"
}


CADEIA_PROCESSO = [
    ("pesquisar", "Pesquisar dados para validar a oportunidade."),
    ("analisar", "Estruturar os dados encontrados."),
    ("criar_oferta", "Montar a oferta inicial a partir da análise."),
    ("criar_proposta", "Preparar a proposta comercial a partir da oferta."),
    ("pesquisar_alvo", "Encontrar um alvo público concreto antes da abordagem."),
    ("validar_alvo", "Verificar evidências públicas do problema antes da abordagem."),
    ("preparar_abordagem", "Preparar a abordagem externa para autorização do usuário.")
]


def criar_tarefas(decisao):
    acao = decisao.get("acao")
    tarefas = []

    def adicionar(acao_tarefa, descricao):
        if acao_tarefa in ACOES_INTERNAS:
            tarefas.append({
                "id": str(uuid.uuid4()),
                "acao": acao_tarefa,
                "descricao": descricao,
                "status": "pendente"
            })

    if acao in {"pesquisar", "analisar", "criar_oferta", "criar_proposta"}:
        indice = next(
            indice for indice, (acao_tarefa, _) in enumerate(CADEIA_PROCESSO)
            if acao_tarefa == acao
        )

        # Se o último ciclo da mesma estratégia já concluiu etapas anteriores,
        # começa da próxima etapa útil em vez de reconstruir tudo.
        ultimo = obter_ultimo_ciclo() or {}
        decisao_anterior = ultimo.get("decisao") or {}
        mesma_estrategia = (
            decisao.get("estrategia")
            and decisao.get("estrategia") == decisao_anterior.get("estrategia")
        )
        concluidas = set()
        if mesma_estrategia:
            for execucao in (ultimo.get("execucao") or {}).get("execucoes", []) or []:
                if execucao.get("status") in {"executado", "concluida"}:
                    acao_concluida = execucao.get("acao")
                    if acao_concluida:
                        concluidas.add(acao_concluida)

        cadeia = CADEIA_PROCESSO[indice:]
        if concluidas:
            cadeia = [
                item for item in cadeia
                if item[0] not in concluidas
            ]
        if not cadeia:
            # Nada novo a executar nesta cadeia; deixa o agente decidir a
            # próxima ação comercial em vez de repetir tarefas.
            adicionar("acompanhar_lead", "Reavaliar o estado comercial após etapas já concluídas.")
        else:
            for acao_tarefa, descricao in cadeia:
                adicionar(acao_tarefa, descricao)
    elif acao == "criar_conteudo":
        adicionar("criar_conteudo", "Produzir o material de teste.")
    elif acao in {"pesquisar_alvo", "validar_alvo"}:
        indice = next(
            indice for indice, (acao_tarefa, _) in enumerate(CADEIA_PROCESSO)
            if acao_tarefa == acao
        )
        for acao_tarefa, descricao in CADEIA_PROCESSO[indice:]:
            adicionar(acao_tarefa, descricao)
    elif acao == "preparar_abordagem":
        if decisao.get("alvo_validado") and decisao.get("url_alvo"):
            adicionar("preparar_abordagem", "Preparar a abordagem do alvo já validado.")
        else:
            for acao_tarefa, descricao in CADEIA_PROCESSO[4:]:
                adicionar(acao_tarefa, descricao)
    elif acao == "preparar_followup":
        adicionar("preparar_followup", "Preparar acompanhamento de uma abordagem já executada.")
    elif acao == "acompanhar_lead":
        adicionar("acompanhar_lead", "Analisar o estado do lead e o próximo avanço comercial.")
    elif acao == "medir_resultado":
        adicionar("medir_resultado", "Medir receita, vendas e resultado da estratégia.")
    elif acao == "testar_estrategia":
        adicionar("testar_estrategia", "Registrar e estruturar o teste da estratégia.")
    else:
        adicionar("aguardar", "Aguardar uma próxima decisão segura.")

    return tarefas


class GerenciadorTarefas:

    def criar(self, decisao, ciclo=None):
        tarefas = criar_tarefas(decisao)

        for tarefa in tarefas:
            registrar_tarefa(
                tarefa_id=tarefa["id"],
                descricao=tarefa["descricao"],
                acao=tarefa["acao"],
                status="pendente",
                ciclo=ciclo
            )

        return tarefas

    def concluir(self, tarefa, resultado):
        return atualizar_tarefa(
            tarefa["id"],
            "concluida",
            resultado
        )

    def falhar(self, tarefa, erro):
        return atualizar_tarefa(
            tarefa["id"],
            "falhou",
            {"erro": erro}
        )
