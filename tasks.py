import uuid

from memory import registrar_tarefa, atualizar_tarefa


ACOES_INTERNAS = {
    "aguardar",
    "pesquisar",
    "analisar",
    "criar_oferta",
    "criar_proposta",
    "criar_conteudo",
    "testar_estrategia"
}


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

    if acao == "pesquisar":
        adicionar("pesquisar", "Pesquisar dados para validar a oportunidade.")
        adicionar("analisar", "Estruturar os dados encontrados.")
    elif acao == "analisar":
        adicionar("analisar", "Estruturar a oportunidade e seus dados.")
        adicionar("criar_oferta", "Montar a oferta inicial a partir da análise.")
    elif acao == "criar_oferta":
        adicionar("criar_oferta", "Montar a oferta inicial.")
        adicionar("criar_proposta", "Preparar a proposta comercial a partir da oferta.")
    elif acao == "criar_proposta":
        adicionar("criar_proposta", "Preparar a proposta comercial.")
        adicionar("testar_estrategia", "Estruturar o teste da estratégia após preparar a proposta.")
    elif acao == "criar_conteudo":
        adicionar("criar_conteudo", "Produzir o material de teste.")
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
