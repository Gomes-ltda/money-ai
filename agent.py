from ai import analisar_oportunidade, analisar_pedido_cliente
from executor import Executor
from tasks import GerenciadorTarefas

from memory import (
    registrar_ciclo,
    registrar_resultado,
    registrar_aprendizado,
    obter_ultimos_aprendizados,
    obter_contexto_estrategico,
    avaliar_estrategias,
    obter_ultimo_ciclo,
    obter_estado_comercial,
    obter_leads,
    obter_leads_prioritarios,
    obter_pedido_cliente,
    atualizar_pedido_cliente,
    obter_reclamacoes
)

ACOES_PERMITIDAS = {
    "aguardar", "pesquisar", "analisar", "analisar_reclamacao", "resolver_reclamacao", "criar_oferta",
    "criar_proposta", "criar_conteudo", "executar_pedido", "pesquisar_alvo", "validar_alvo", "preparar_abordagem", "testar_estrategia", "acompanhar_lead", "processar_resposta", "preparar_followup", "medir_resultado"
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
        "reclamacao_id": detalhes.get("reclamacao_id"),
        "pedido_id": detalhes.get("pedido_id"),
        "alvo_validado": detalhes.get("alvo_validado", False),
        "evidencia_alvo_memoria": detalhes.get("evidencia_alvo_memoria", []),
        "preco_teste": detalhes.get("preco_teste"),
        "custo_teste": detalhes.get("custo_teste"),
        "acao_imediata": detalhes.get("acao_imediata"),
        "localizacao": localizacao,
        "precisa_permissao": False,
        "motivo": motivo,
        "acao_sobre_estrategia": detalhes.get("acao_sobre_estrategia", "testar_nova"),
        "estrategia_base": detalhes.get("estrategia_base"),
        "justificativa_evidencia": detalhes.get("justificativa_evidencia"),
        "proxima_acao_ciclo": detalhes.get("proxima_acao_ciclo")
    }


def executar_ciclo_pedido(pedido_id, localizacao="Brasil"):
    """Executa o ciclo da EVOLIA especificamente para uma solicitação recebida."""
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return {"status": "erro", "erro": "Pedido não encontrado.", "pedido_id": pedido_id}

    objetivo = (
        "Atender o pedido do cliente de forma sustentável, definindo escopo, preço, prazo "
        "e próximos passos com base nas informações fornecidas. Pedido: "
        + str(pedido.get("servico") or "serviço")
        + " — "
        + str(pedido.get("descricao") or "")
    )

    resultado = analisar_pedido_cliente(pedido, localizacao=localizacao)
    if resultado.get("status") != "sucesso":
        atualizar_pedido_cliente(
            pedido_id,
            status="em_analise",
            observacao="O ciclo foi iniciado, mas o Cérebro não conseguiu concluir a análise: "
            + str(resultado.get("erro") or "erro desconhecido")
        )
        ciclo = registrar_ciclo(
            objetivo=objetivo,
            localizacao=localizacao,
            pesquisa=resultado.get("fontes_utilizadas"),
            analise=resultado,
            decisao={"acao": "aguardar", "pedido_id": pedido_id, "motivo": "Análise indisponível."},
            execucao={"acao": "analisar_pedido_cliente", "status": "bloqueado", "pedido_id": pedido_id},
            medicao={"receita": 0, "custo": 0, "resultado": 0, "status": "aguardando_cerebro"},
            aprendizado="O pedido precisa ser reavaliado quando o Cérebro estiver disponível.",
            proxima_acao="Retomar a análise deste pedido.",
            tipo="pedido_cliente",
            pedido_id=pedido_id
        )
        return {
            "status": "aguardando_cerebro",
            "pedido_id": pedido_id,
            "pedido": obter_pedido_cliente(pedido_id),
            "ciclo_memoria": ciclo,
            "erro": resultado.get("erro")
        }

    analise = resultado.get("analise") or {}
    proposta = {
        "texto": analise.get("proposta_cliente") or analise.get("resumo") or "",
        "valor": analise.get("valor_sugerido"),
        "prazo": analise.get("prazo_sugerido"),
        "escopo": analise.get("escopo") or [],
        "nao_incluido": analise.get("nao_incluido") or [],
        "perguntas": analise.get("perguntas") or [],
        "justificativa_preco": analise.get("justificativa_preco"),
        "riscos": analise.get("riscos") or [],
        "confianca": analise.get("confianca"),
        "modelo_utilizado": resultado.get("modelo_utilizado"),
        "fontes_utilizadas": resultado.get("fontes_utilizadas") or []
    }
    atualizado = atualizar_pedido_cliente(
        pedido_id,
        status="proposta_preparada",
        proposta=proposta,
        observacao="Ciclo da EVOLIA concluído: proposta preparada e aguardando autorização para publicação ao cliente."
    )

    decisao = {
        "acao": "analisar_pedido_cliente",
        "pedido_id": pedido_id,
        "estrategia": "atendimento de pedidos recebidos",
        "cliente_alvo": pedido.get("nome"),
        "problema": pedido.get("descricao"),
        "oferta": pedido.get("servico"),
        "proxima_acao_ciclo": "Revisar e, se estiver adequada, autorizar a publicação da proposta ao cliente."
    }
    execucao = {
        "status": "executado",
        "acao": "analisar_pedido_cliente",
        "pedido_id": pedido_id,
        "execucoes": [{
            "status": "executado",
            "acao": "analisar_pedido_cliente",
            "pedido_id": pedido_id,
            "resultado": {"proposta_preparada": True, "valor": proposta.get("valor"), "prazo": proposta.get("prazo")}
        }]
    }
    ciclo = registrar_ciclo(
        objetivo=objetivo,
        localizacao=localizacao,
        pesquisa=resultado.get("fontes_utilizadas"),
        analise=resultado,
        decisao=decisao,
        execucao=execucao,
        medicao={"receita": 0, "custo": 0, "resultado": 0, "status": "proposta_preparada"},
        aprendizado="O pedido foi transformado em uma proposta estruturada sem executar comunicação externa.",
        proxima_acao="Revisar e autorizar a publicação da proposta ao cliente.",
        tipo="pedido_cliente",
        pedido_id=pedido_id
    )
    return {
        "status": "proposta_preparada",
        "pedido_id": pedido_id,
        "pedido": atualizado,
        "analise": analise,
        "ciclo_memoria": ciclo,
        "fontes_utilizadas": resultado.get("fontes_utilizadas") or []
    }


def executar_ciclo(objetivo, localizacao="Brasil"):
    memoria = obter_ultimos_aprendizados(10)
    contexto_estrategico = obter_contexto_estrategico()
    ciclo_anterior = obter_ultimo_ciclo()
    estado_comercial = obter_estado_comercial()

    contexto_ciclo = {
        "tipo": "ciclo_anterior",
        "dados": ciclo_anterior or {},
        "instrucao": "Use este ciclo como estado de continuidade; não repita mecanicamente a última ação."
    }

    decisao_ia = analisar_oportunidade(
        objetivo,
        localizacao,
        contexto_memoria=memoria + [
            {"tipo": "desempenho_estrategico", "dados": contexto_estrategico},
            contexto_ciclo,
            {"tipo": "estado_comercial", "dados": estado_comercial}
        ]
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
            medicao={"receita": 0, "custo": 0, "resultado": 0, "status": "modo_degradado"},
            aprendizado=decisao_ia.get("aprendizado_esperado"),
            proxima_acao=decisao_ia.get("proximo_passo")
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

    detalhes = dict(decisao_ia.get("decisao", {}) or {})
    acao_inicial = detalhes.get("acao_executor", decisao_ia.get("acao_executor"))

    # Antes de prospectar novamente, prioriza leads já em andamento.
    # A EVOLIA deve avançar o funil existente antes de criar trabalho novo.
    pedidos_em_execucao = [p for p in __import__("memory").obter_pedidos_clientes(100) if p.get("status") == "em_execucao"]
    if pedidos_em_execucao:
        pedido = pedidos_em_execucao[0]
        detalhes["pedido_id"] = pedido.get("id")
        detalhes["cliente_alvo"] = pedido.get("nome")
        detalhes["oferta"] = pedido.get("servico")
        detalhes["problema"] = pedido.get("descricao")
        acao_inicial = "executar_pedido"
        detalhes["motivo_escolha"] = "Existe pedido pago em execução; produzir o resultado antes de iniciar novo trabalho comercial."

    reclamacoes_abertas = obter_reclamacoes(limite=50, status="aberta")
    reclamacoes_em_analise = obter_reclamacoes(limite=50, status="em_analise")
    if reclamacoes_abertas:
        reclamacao = reclamacoes_abertas[0]
        detalhes["reclamacao_id"] = reclamacao.get("id")
        detalhes["reclamacao_assunto"] = reclamacao.get("assunto")
        detalhes["reclamacao_descricao"] = reclamacao.get("descricao")
        acao_inicial = "analisar_reclamacao"
        detalhes["motivo_escolha"] = "Existe uma reclamação aberta; analisar o problema do cliente antes de iniciar nova prospecção."
    elif reclamacoes_em_analise:
        reclamacao = reclamacoes_em_analise[0]
        detalhes["reclamacao_id"] = reclamacao.get("id")
        detalhes["reclamacao_assunto"] = reclamacao.get("assunto")
        detalhes["reclamacao_descricao"] = reclamacao.get("descricao")
        acao_inicial = "resolver_reclamacao"
        detalhes["motivo_escolha"] = "Existe uma reclamação em análise; executar a providência possível antes de iniciar nova prospecção."

    leads_ativos = obter_leads_prioritarios(limite=20)
    if leads_ativos and acao_inicial in {
        "pesquisar_alvo", "validar_alvo", "preparar_abordagem"
    }:
        lead_prioritario = leads_ativos[0]
        status_lead = lead_prioritario.get("status")
        if status_lead == "abordagem_preparada":
            acao_inicial = "aguardar"
            detalhes["proxima_acao_ciclo"] = "Aguardar autorização para contato com o lead já preparado."
        elif status_lead == "autorizado":
            acao_inicial = "acompanhar_lead"
            detalhes["proxima_acao_ciclo"] = "Acompanhar a execução e o retorno do contato autorizado."
        elif status_lead == "contato_executado":
            acao_inicial = "acompanhar_lead"
            detalhes["proxima_acao_ciclo"] = "Aguardar ou processar resposta do lead antes de nova prospecção."
        elif status_lead in {"resposta", "interesse"}:
            acao_inicial = "processar_resposta"
            detalhes["proxima_acao_ciclo"] = "Processar a resposta/interesse existente e definir o próximo passo comercial antes de nova prospecção."

        detalhes["url_alvo"] = detalhes.get("url_alvo") or lead_prioritario.get("url")
        detalhes["canal"] = detalhes.get("canal") or lead_prioritario.get("canal")
        detalhes["cliente_alvo"] = detalhes.get("cliente_alvo") or lead_prioritario.get("nome")
        detalhes["alvo_validado"] = status_lead in {
            "abordagem_preparada", "autorizado", "contato_executado",
            "resposta", "interesse"
        }


    # Reaproveita alvos já validados pela memória antes de iniciar nova prospecção.
    if acao_inicial in {"preparar_abordagem", "validar_alvo"}:
        leads_validos = [
            lead for lead in obter_leads(status="validado", limite=100)
            if not detalhes.get("estrategia") or lead.get("estrategia") == detalhes.get("estrategia")
        ]
        url_atual = (detalhes.get("url_alvo") or "").strip()
        cliente_atual = (detalhes.get("cliente_alvo") or "").strip()
        lead = next(
            (x for x in reversed(leads_validos)
             if (url_atual and x.get("url") == url_atual)
             or (not url_atual and cliente_atual and x.get("nome") == cliente_atual)),
            None
        )
        if lead is None and not url_atual and leads_validos:
            lead = leads_validos[-1]
        if lead:
            detalhes["url_alvo"] = detalhes.get("url_alvo") or lead.get("url")
            detalhes["canal"] = detalhes.get("canal") or lead.get("canal")
            detalhes["cliente_alvo"] = detalhes.get("cliente_alvo") or lead.get("nome")
            detalhes["alvo_validado"] = True
            detalhes["evidencia_alvo_memoria"] = lead.get("evidencia_publica") or []

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

        # Mantém o último resultado útil do ciclo anterior quando a
        # estratégia é a mesma, permitindo continuidade real entre ciclos.
        resultado_anterior_ciclo = None
        estrategia = detalhes.get("estrategia")
        ciclo_execucao_anterior = (ciclo_anterior or {}).get("execucao", {}) if isinstance(ciclo_anterior, dict) else {}
        execucoes_anteriores = ciclo_execucao_anterior.get("execucoes", []) if isinstance(ciclo_execucao_anterior, dict) else []
        estrategia_anterior = ((ciclo_anterior or {}).get("decisao", {}) or {}).get("estrategia") if isinstance(ciclo_anterior, dict) else None
        if estrategia and estrategia_anterior == estrategia and execucoes_anteriores:
            resultado_anterior_ciclo = execucoes_anteriores[-1]

        contexto_execucao = {
            "objetivo": objetivo,
            "localizacao": localizacao,
            "resultado_anterior": resultado_anterior_ciclo,
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
        if item.get("acao") == "medir_resultado":
            continue
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

    proxima_acao = detalhes.get("proxima_acao_ciclo") or decisao_ia.get("proximo_passo")
    aprendizado_ciclo = decisao_ia.get("aprendizado_esperado") or (
        "Resultado do ciclo: R${:.2f}; ação executada: {}.".format(resultado, acao_inicial)
    )

    ciclo = registrar_ciclo(
        objetivo=objetivo, localizacao=localizacao,
        pesquisa=decisao_ia.get("fontes_utilizadas"),
        analise=decisao_ia, decisao=decisao,
        execucao=execucao, medicao=medicao,
        aprendizado=aprendizado_ciclo,
        proxima_acao=proxima_acao
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
