from ai import analisar_oportunidade
from executor import Executor
from tasks import GerenciadorTarefas

from memory import (
    registrar_ciclo,
    registrar_resultado,
    registrar_aprendizado,
    obter_ultimos_aprendizados,
    obter_contexto_estrategico,
    avaliar_estrategias
)

ACOES_PERMITIDAS = {
    "aguardar", "pesquisar", "analisar", "criar_oferta",
    "criar_proposta", "criar_conteudo", "pesquisar_alvo", "preparar_abordagem", "testar_estrategia"
}

MAX_TAREFAS_POR_CICLO = 6


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
        "url_alvo": detalhes.get("url_alvo"),
        "preco_teste": detalhes.get("preco_teste"),
        "custo_teste": detalhes.get("custo_teste"),
        "acao_imediata": detalhes.get("acao_imediata"),
        "localizacao": localizacao,
        "precisa_permissao": False,
        "motivo": motivo,
        "acao_sobre_estrategia": detalhes.get("acao_sobre_estrategia", "testar_nova"),
        "estrategia_base": detalhes.get("estrategia_base"),
        "justificativa_evidencia": detalhes.get("justificativa_evidencia")
    }


def executar_ciclo(objetivo, localizacao="Brasil"):
    memoria = obter_ultimos_aprendizados(10)
    contexto_estrategico = obter_contexto_estrategico()

    decisao_ia = analisar_oportunidade(
        objetivo, localizacao, contexto_memoria=memoria + [{"tipo": "desempenho_estrategico", "dados": contexto_estrategico}]
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

    # Em modo degradado, o Cérebro não decide uma estratégia nova.
    # Ainda assim, a EVOLIA pode executar pesquisa factual de prospecção
    # usando o TinyFish, sem enviar mensagens ou assumir que encontrou um
    # problema real sem validação pública.
    if decisao_ia.get("status") == "modo_degradado":
        detalhes_degradados = decisao_ia.get("decisao", {}) or {}
        fallback = {
            **detalhes_degradados,
            "estrategia": "prospecção incremental de clientes",
            "nicho": "prestadores de serviços B2B",
            "cliente_alvo": "prestadores de serviços B2B",
            "problema": "dificuldade na captação de clientes B2B e abordagens comerciais genéricas",
            "oferta": "diagnóstico e melhoria de abordagem comercial com IA",
            "canal": None,
            "url_alvo": None,
            "acao_executor": "pesquisar_alvo",
            "precisa_permissao": False
        }
        decisao_degradada = _montar_decisao(
            fallback,
            "pesquisar_alvo",
            objetivo,
            localizacao,
            "Modo degradado: provedores de IA indisponíveis; executar somente prospecção factual e validação pública."
        )

        executor_degradado = Executor()
        execucoes_degradadas = []
        resultado_anterior = None

        for acao in ("pesquisar_alvo", "validar_alvo"):
            tarefa_decisao = dict(decisao_degradada)
            tarefa_decisao["acao"] = acao
            tarefa_decisao["resultado_anterior"] = resultado_anterior
            try:
                resultado_tarefa = executor_degradado.executar(tarefa_decisao)
            except Exception as erro:
                resultado_tarefa = {"status": "erro", "acao": acao, "erro": str(erro)}

            execucoes_degradadas.append(resultado_tarefa)
            if resultado_tarefa.get("status") in {"erro", "bloqueado"}:
                break
            resultado_anterior = resultado_tarefa

        ultimo_resultado = execucoes_degradadas[-1] if execucoes_degradadas else {}
        resultado_publico = ultimo_resultado.get("resultado", {}) if isinstance(ultimo_resultado, dict) else {}
        execucao_degradada = {
            "status": "modo_degradado",
            "acao": "pesquisar_alvo",
            "tarefas_planejadas": [
                {"acao": "pesquisar_alvo", "descricao": "Encontrar alvos públicos específicos."},
                {"acao": "validar_alvo", "descricao": "Verificar evidências públicas antes de qualquer abordagem."}
            ],
            "tarefas_executadas": len(execucoes_degradadas),
            "execucoes": execucoes_degradadas
        }
        ciclo = registrar_ciclo(
            objetivo=objetivo,
            localizacao=localizacao,
            pesquisa=resultado_publico.get("candidatos") or resultado_publico.get("evidencia"),
            analise=decisao_ia,
            decisao=decisao_degradada,
            execucao=execucao_degradada,
            medicao={"receita": 0, "custo": 0, "resultado": 0, "status": "modo_degradado"}
        )
        return {
            "status": "modo_degradado",
            "objetivo": objetivo,
            "localizacao": localizacao,
            "decisao_ia": decisao_ia,
            "decisao": decisao_degradada,
            "tarefas": execucao_degradada["tarefas_planejadas"],
            "execucao": execucao_degradada,
            "medicao": {"receita": 0, "custo": 0, "resultado": 0, "status": "modo_degradado"},
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

        contexto_execucao = {
            "objetivo": objetivo,
            "localizacao": localizacao,
            "resultado_anterior": None,
            "historico": []
        }

        for tarefa in tarefas[:MAX_TAREFAS_POR_CICLO]:
            tarefa_decisao = dict(decisao)
            tarefa_decisao["acao"] = tarefa["acao"]
            tarefa_decisao["resultado_anterior"] = contexto_execucao["resultado_anterior"]
            tarefa_decisao["contexto_execucao"] = contexto_execucao

            try:
                resultado_tarefa = executor.executar(tarefa_decisao)
                if resultado_tarefa.get("status") in {"erro", "bloqueado"}:
                    gerenciador.falhar(tarefa, resultado_tarefa)
                    execucoes.append(resultado_tarefa)
                    contexto_execucao["historico"].append({
                        "tarefa_id": tarefa["id"],
                        "acao": tarefa["acao"],
                        "resultado": resultado_tarefa
                    })
                    break

                gerenciador.concluir(tarefa, resultado_tarefa)
                execucoes.append(resultado_tarefa)
                contexto_execucao["resultado_anterior"] = resultado_tarefa
                contexto_execucao["historico"].append({
                    "tarefa_id": tarefa["id"],
                    "acao": tarefa["acao"],
                    "resultado": resultado_tarefa
                })
            except Exception as erro:
                erro_resultado = {"status": "erro", "acao": tarefa["acao"], "erro": str(erro)}
                gerenciador.falhar(tarefa, erro_resultado)
                execucoes.append(erro_resultado)
                contexto_execucao["historico"].append({
                    "tarefa_id": tarefa["id"],
                    "acao": tarefa["acao"],
                    "resultado": erro_resultado
                })
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
    acao_sobre_estrategia = detalhes.get("acao_sobre_estrategia", "testar_nova")
    if acao_sobre_estrategia not in {"continuar", "modificar", "testar_nova", "aguardar"}:
        acao_sobre_estrategia = "testar_nova"

    avaliacao_atual = avaliar_estrategias()

    if estrategia and acao_sobre_estrategia == "aguardar":
        registrar_aprendizado(
            aprendizado=f"A estratégia '{estrategia}' foi colocada em espera pela decisão estratégica.",
            estrategia=estrategia,
            evidencias=[avaliacao_atual.get(estrategia, {})],
            impacto=0,
            acao="aguardar",
            recomendacao="aguardar"
        )

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
