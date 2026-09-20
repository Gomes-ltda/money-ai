import uuid

from memory import registrar_tarefa, atualizar_tarefa


ACOES_INTERNAS = {
    "aguardar",
    "pesquisar",
    "analisar",
    "criar_oferta",
    "criar_proposta",
    "criar_conteudo",
    "pesquisar_alvo",
    "preparar_abordagem",
    "testar_estrategia"
}


CADEIA_PROCESSO = [
    ("pesquisar", "Pesquisar dados para validar a oportunidade."),
    ("analisar", "Estruturar os dados encontrados."),
    ("criar_oferta", "Montar a oferta inicial a partir da análise."),
    ("criar_proposta", "Preparar a proposta comercial a partir da oferta."),
    ("pesquisar_alvo", "Encontrar um alvo público concreto antes da abordagem."),
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
        for acao_tarefa, descricao in CADEIA_PROCESSO[indice:]:
            adicionar(acao_tarefa, descricao)
    elif acao == "criar_conteudo":
        adicionar("criar_conteudo", "Produzir o material de teste.")
    elif acao == "preparar_abordagem":
        adicionar("preparar_abordagem", "Preparar uma abordagem comercial sem enviá-la.")
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
