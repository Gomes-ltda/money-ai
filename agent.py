from ai import analisar_oportunidade
from executor import Executor
from tasks import GerenciadorTarefas

from memory import (
    registrar_ciclo,
    registrar_resultado,
    registrar_aprendizado,
    obter_ultimos_aprendizados
)

ACOES_PERMITIDAS = {
    "aguardar", "pesquisar", "analisar", "criar_oferta",
    "criar_proposta", "criar_conteudo", "testar_estrategia"
}

MAX_TAREFAS_POR_CICLO = 3


def _montar_decisao(detalhes, acao, objetivo, localizacao, motivo):
    return {
        "acao": acao,
        "estrategia": detalhes.get("estrategia"),
        "objetivo": objetivo,
        "nicho": detalhes.get("nicho"),
        "cliente_alvo": detalhes.get("cliente_alvo"),
        "problema": detalhes.get("problema"),
        "oferta": detalhes.get("oferta"),
        "canal": detalhes.get("canal"),
        "preco_teste": detalhes.get("preco_teste"),
        "custo_teste": detalhes.get("custo_teste"),
        "acao_imediata": detalhes.get("acao_imediata"),
        "localizacao": localizacao,
        "precisa_permissao": False,
        "motivo": motivo
    }


def executar_ciclo(objetivo, localizacao="Brasil"):
    memoria = obter_ultimos_aprendizados(10)

    decisao_ia = analisar_oportunidade(
        objetivo, localizacao, contexto_memoria=memoria
    )

    if decisao_ia.get("status") in {"erro_cota", "erro", "erro_configuracao"}:
        ciclo = registrar_ciclo(
            objetivo=objetivo, localizacao=localizacao, pesquisa=None,
            analise=decisao_ia,
            decisao={"acao": "aguardar", "motivo": "O Cérebro não está disponível no momento."},
            execucao={"acao": "aguardar", "status": "bloqueado"},
            medicao={"receita": 0, "custo": 0, "resultado": 0, "status": "aguardando_cerebro"}
        )
        return {
            "status": "aguardando_cerebro",
            "motivo": decisao_ia.get("erro", "Cérebro indisponível."),
            "decisao_ia": decisao_ia,
            "decisao": {"acao": "aguardar"},
            "execucao": {"acao": "aguardar", "status": "bloqueado"},
            "medicao": {"receita": 0, "custo": 0, "resultado": 0, "status": "aguardando_cerebro"},
            "ciclo_memoria": ciclo
        }

    detalhes = decisao_ia.get("decisao", {})
    acao_inicial = detalhes.get("acao_executor", decisao_ia.get("acao_executor"))

    if acao_inicial not in ACOES_PERMITIDAS:
        acao_inicial = "aguardar"
        motivo = "A IA retornou uma ação inexistente ou não autorizada."
    else:
        motivo = "Ação escolhida pelo Cérebro com base na análise e memória."

    if detalhes.get("precisa_permissao", False):
        decisao = {
            "acao": "aguardar",
            "acao_solicitada": acao_inicial,
            "estrategia": detalhes.get("estrategia"),
            "precisa_permissao": True,
            "motivo": "A próxima ação exige autorização do usuário."
        }
        execucao = Executor().executar(decisao)
        tarefas = []
    else:
        decisao = _montar_decisao(detalhes, acao_inicial, objetivo, localizacao, motivo)
        gerenciador = GerenciadorTarefas()
        tarefas = gerenciador.criar(decisao)
        executor = Executor()
        execucoes = []

        for tarefa in tarefas[:MAX_TAREFAS_POR_CICLO]:
            tarefa_decisao = dict(decisao)
            tarefa_decisao["acao"] = tarefa["acao"]

            try:
                resultado_tarefa = executor.executar(tarefa_decisao)
                if resultado_tarefa.get("status") in {"erro", "bloqueado"}:
                    gerenciador.falhar(tarefa, resultado_tarefa)
                    execucoes.append(resultado_tarefa)
                    break

                gerenciador.concluir(tarefa, resultado_tarefa)
                execucoes.append(resultado_tarefa)
            except Exception as erro:
                gerenciador.falhar(tarefa, {"erro": str(erro)})
                execucoes.append({"status": "erro", "acao": tarefa["acao"], "erro": str(erro)})
                break

        execucao = {
            "status": "executado" if execucoes else "sem_execucao",
            "acao": acao_inicial,
            "tarefas_planejadas": tarefas,
            "tarefas_executadas": len(execucoes),
            "execucoes": execucoes
        }

    receita = 0
    custo = 0
    for item in execucao.get("execucoes", [execucao]):
        resultado_item = item.get("resultado", {})
        receita += resultado_item.get("receita", 0) or 0
        custo += resultado_item.get("custo", 0) or 0

    resultado = receita - custo
    medicao = {
        "receita": receita, "custo": custo, "resultado": resultado,
        "status": execucao.get("status", "executado")
    }

    estrategia = detalhes.get("estrategia")
    if estrategia:
        registrar_resultado(
            estrategia=estrategia, receita=receita, custo=custo,
            resultado=resultado, acao=acao_inicial,
            evidencias=execucao.get("execucoes", [])
        )
        registrar_aprendizado(
            aprendizado=(
                "A estratégia '{}' executou {} tarefa(s). "
                "Resultado financeiro: R$" + "{:.2f}."
            ).format(estrategia, execucao.get("tarefas_executadas", 0), resultado),
            estrategia=estrategia,
            evidencias=execucao.get("execucoes", []),
            impacto=resultado,
            acao=acao_inicial
        )

    ciclo = registrar_ciclo(
        objetivo=objetivo, localizacao=localizacao,
        pesquisa=decisao_ia.get("fontes_utilizadas"),
        analise=decisao_ia, decisao=decisao,
        execucao=execucao, medicao=medicao
    )

    return {
        "status": "sucesso",
        "objetivo": objetivo,
        "localizacao": localizacao,
        "memoria_utilizada": memoria,
        "decisao_ia": decisao_ia,
        "decisao": decisao,
        "tarefas": tarefas,
        "execucao": execucao,
        "medicao": medicao,
        "ciclo_memoria": ciclo
    }


class MoneyAgent:
    def executar_ciclo(self, objetivo, localizacao="Brasil"):
        return executar_ciclo(objetivo, localizacao)
