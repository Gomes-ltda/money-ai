from datetime import datetime, timezone
import uuid

from Permissões import solicitar_permissao
from pesquisa import pesquisar
from memory import registrar_evento, registrar_teste, registrar_acao_externa, obter_acoes_externas, registrar_lead, obter_leads, atualizar_lead

ACOES_INTERNAS = {
    "aguardar", "pesquisar", "analisar", "analisar_reclamacao", "resolver_reclamacao", "analisar_pedido_cliente", "criar_oferta",
    "criar_proposta", "criar_conteudo", "executar_pedido", "validar_resultado", "preparar_abordagem", "preparar_followup", "acompanhar_lead", "processar_resposta", "medir_resultado", "pesquisar_alvo", "validar_alvo", "testar_estrategia"
}

def agora():
    return datetime.now(timezone.utc).isoformat()

class Executor:
    def executar(self, decisao):
        acao = decisao.get("acao")
        if not acao:
            return {"status": "erro", "acao": None, "erro": "Nenhuma ação foi definida."}
        if acao not in ACOES_INTERNAS:
            return {"status": "bloqueado", "acao": acao, "motivo": "Ação não reconhecida pelo Executor."}

        permissao = solicitar_permissao(acao)
        if not permissao.get("permitido"):
            return {"status": "bloqueado", "acao": acao, "motivo": permissao.get("motivo", "Ação não autorizada.")}

        inicio = agora()
        execucao_id = str(uuid.uuid4())
        try:
            if acao == "aguardar":
                resultado = self.executar_aguardar(decisao)
            elif acao == "pesquisar":
                resultado = self.executar_pesquisa(decisao)
            elif acao == "analisar":
                resultado = self.executar_analise(decisao)
            elif acao == "analisar_reclamacao":
                resultado = self.analisar_reclamacao(decisao)
            elif acao == "resolver_reclamacao":
                resultado = self.resolver_reclamacao(decisao)
            elif acao == "analisar_pedido_cliente":
                from agent import executar_ciclo_pedido
                resultado = executar_ciclo_pedido(decisao.get("pedido_id"), decisao.get("localizacao", "Brasil"))
            elif acao == "criar_oferta":
                resultado = self.criar_oferta(decisao)
            elif acao == "criar_proposta":
                resultado = self.criar_proposta(decisao)
            elif acao == "criar_conteudo":
                resultado = self.criar_conteudo(decisao)
            elif acao == "executar_pedido":
                resultado = self.executar_pedido(decisao)
            elif acao == "validar_resultado":
                resultado = self.validar_resultado(decisao)
            elif acao == "pesquisar_alvo":
                resultado = self.pesquisar_alvo(decisao)
            elif acao == "validar_alvo":
                resultado = self.validar_alvo(decisao)
            elif acao == "preparar_abordagem":
                resultado = self.preparar_abordagem(decisao)
            elif acao == "preparar_followup":
                resultado = self.preparar_followup(decisao)
            elif acao == "acompanhar_lead":
                resultado = self.acompanhar_lead(decisao)
            elif acao == "processar_resposta":
                resultado = self.processar_resposta(decisao)
            elif acao == "medir_resultado":
                resultado = self.medir_resultado(decisao)
            elif acao == "testar_estrategia":
                resultado = self.testar_estrategia(decisao)
            else:
                resultado = {"status": "erro", "acao": acao, "erro": "Ação não implementada."}

            resultado["execucao_id"] = execucao_id
            resultado["iniciada_em"] = inicio
            resultado["finalizada_em"] = agora()
            return resultado
        except Exception as erro:
            return {"status": "erro", "acao": acao, "execucao_id": execucao_id, "erro": str(erro)}

    def executar_aguardar(self, decisao):
        registrar_evento("executor", f"Ação aguardar registrada: {decisao.get('motivo', 'sem motivo informado')}")
        return {
            "status": "aguardando", "acao": "aguardar",
            "resultado": {"receita": 0, "custo": 0},
            "motivo": decisao.get("motivo", "Nenhuma ação será executada agora.")
        }

    def executar_pesquisa(self, decisao):
        consulta = decisao.get("consulta") or decisao.get("acao_imediata") or decisao.get("objetivo") or "Encontrar oportunidades de mercado"
        resultado = pesquisar(consulta, decisao.get("localizacao", "Brasil"))
        registrar_evento("pesquisa", f"Pesquisa executada: {consulta}")
        return {"status": "executado", "acao": "pesquisar", "consulta": consulta, "resultado": resultado}

    def executar_analise(self, decisao):
        anterior = decisao.get("resultado_anterior") or {}
        pesquisa_anterior = anterior.get("resultado", {}) if isinstance(anterior, dict) else {}
        analise = {
            "estrategia": decisao.get("estrategia"),
            "nicho": decisao.get("nicho"),
            "cliente_alvo": decisao.get("cliente_alvo"),
            "problema": decisao.get("problema"),
            "oferta": decisao.get("oferta"),
            "canal": decisao.get("canal"),
            "pesquisa_anterior": pesquisa_anterior
        }
        registrar_evento("analise", f"Análise estruturada para a estratégia: {decisao.get('estrategia')}")
        return {"status": "executado", "acao": "analisar", "resultado": {"receita": 0, "custo": 0, "analise": analise}}

    def analisar_reclamacao(self, decisao):
        from memory import obter_reclamacoes, atualizar_reclamacao, obter_pedido_cliente

        reclamacao_id = str(decisao.get("reclamacao_id") or "").strip()
        reclamacao = next((r for r in obter_reclamacoes(limite=200) if r.get("id") == reclamacao_id), None)
        if not reclamacao:
            return {"status": "bloqueado", "acao": "analisar_reclamacao", "motivo": "Reclamação não encontrada."}
        if reclamacao.get("status") in {"resolvida", "encerrada"}:
            return {"status": "bloqueado", "acao": "analisar_reclamacao", "motivo": "A reclamação já foi encerrada."}

        texto = (str(reclamacao.get("assunto") or "") + " " + str(reclamacao.get("descricao") or "")).lower()
        if any(x in texto for x in ("pagamento", "cobrança", "pix", "valor")):
            categoria, providencia = "financeiro", "verificar cobrança e pagamento vinculados antes de responder."
        elif any(x in texto for x in ("entrega", "arquivo", "link", "não recebi", "nao recebi")):
            categoria, providencia = "entrega", "verificar o registro da entrega e disponibilizar novamente o resultado, se necessário."
        elif any(x in texto for x in ("prazo", "atraso", "demora")):
            categoria, providencia = "prazo", "verificar o andamento do pedido e registrar uma previsão objetiva."
        else:
            categoria, providencia = "qualidade", "verificar o escopo contratado e o resultado entregue antes de definir a correção."

        atualizar_reclamacao(
            reclamacao_id,
            status="em_analise",
            resolucao="Categoria: " + categoria + ". Providência recomendada: " + providencia
        )
        pedido = obter_pedido_cliente(reclamacao.get("pedido_id"))
        registrar_evento("reclamacao_analisada", "Reclamação " + reclamacao_id + " analisada; categoria " + categoria + ".")
        return {
            "status": "executado",
            "acao": "analisar_reclamacao",
            "resultado": {
                "receita": 0, "custo": 0,
                "reclamacao_id": reclamacao_id,
                "categoria": categoria,
                "providencia": providencia,
                "pedido_id": reclamacao.get("pedido_id"),
                "pedido_status": (pedido or {}).get("status")
            }
        }

    def resolver_reclamacao(self, decisao):
        """Executa a providência possível para uma reclamação já analisada."""
        from memory import obter_reclamacoes, atualizar_reclamacao, obter_pedido_cliente, obter_pagamento_por_id
        from pedido_fluxo import sincronizar_pedido_pagamento

        reclamacao_id = str(decisao.get("reclamacao_id") or "").strip()
        reclamacao = next((r for r in obter_reclamacoes(limite=200) if r.get("id") == reclamacao_id), None)
        if not reclamacao:
            return {"status": "bloqueado", "acao": "resolver_reclamacao", "motivo": "Reclamação não encontrada."}
        if reclamacao.get("status") in {"resolvida", "encerrada"}:
            return {"status": "bloqueado", "acao": "resolver_reclamacao", "motivo": "A reclamação já foi encerrada."}

        pedido_id = reclamacao.get("pedido_id")
        pedido = obter_pedido_cliente(pedido_id) if pedido_id else None
        if not pedido:
            atualizar_reclamacao(
                reclamacao_id,
                status="em_analise",
                resposta="Não foi possível localizar o pedido vinculado. O caso permanece em análise para correção do vínculo.",
            )
            return {
                "status": "bloqueado", "acao": "resolver_reclamacao",
                "motivo": "Pedido vinculado não encontrado.",
                "resultado": {"receita": 0, "custo": 0, "reclamacao_id": reclamacao_id}
            }

        texto = (str(reclamacao.get("assunto") or "") + " " + str(reclamacao.get("descricao") or "")).lower()
        categoria = "qualidade"
        resolucao = None
        resposta = None

        if any(x in texto for x in ("pagamento", "cobrança", "cobranca", "pix", "valor")):
            categoria = "financeiro"
            pagamento = obter_pagamento_por_id(pedido.get("pagamento_id")) if pedido.get("pagamento_id") else None
            if pagamento and pagamento.get("status") == "pago":
                resolucao = "Pagamento vinculado verificado como pago; não foi feita movimentação financeira automática."
                resposta = "Verificamos o pagamento vinculado ao pedido. Ele consta como confirmado. Se a reclamação for sobre o valor cobrado, o caso precisa de conferência específica antes de qualquer ajuste financeiro."
            elif pagamento:
                resolucao = "Pagamento vinculado localizado, mas ainda não consta como pago."
                resposta = "Verificamos a cobrança vinculada ao pedido. O pagamento ainda não consta como confirmado."
            else:
                resolucao = "Não há pagamento vinculado localizado para este pedido."
                resposta = "Não localizamos um pagamento confirmado vinculado a este pedido. A cobrança precisa ser conferida antes de qualquer conclusão financeira."

        elif any(x in texto for x in ("entrega", "arquivo", "link", "não recebi", "nao recebi")):
            categoria = "entrega"
            entrega = pedido.get("entrega") or {}
            if pedido.get("status") == "entregue" and (entrega.get("texto") or entrega.get("url")):
                resolucao = "Entrega já registrada no pedido; disponibilização adicional depende de canal de envio autorizado."
                resposta = "A entrega consta como registrada no pedido. O conteúdo permanece associado ao pedido para disponibilização novamente; nenhum envio externo foi realizado automaticamente."
            else:
                sincronizar_pedido_pagamento(pedido_id)
                pedido_atual = obter_pedido_cliente(pedido_id) or pedido
                resolucao = "Pedido verificado; a entrega ainda não consta como concluída."
                resposta = "Verificamos o pedido e a entrega ainda não consta como concluída. O caso permanece em análise até que o resultado seja produzido e disponibilizado."
                pedido = pedido_atual

        elif any(x in texto for x in ("prazo", "atraso", "demora")):
            categoria = "prazo"
            resolucao = "Status do pedido verificado; nenhuma previsão foi inventada."
            resposta = "Verificamos o andamento do pedido. O prazo informado ao cliente deve ser baseado no estado real da execução, sem estimativa automática não confirmada."

        else:
            categoria = "qualidade"
            resolucao = "Escopo e estado do pedido verificados; não foi feita alteração de entrega sem evidência de erro."
            resposta = "Verificamos o pedido e o escopo registrado. Qualquer correção de qualidade deve ser baseada no resultado efetivamente entregue, sem substituir o serviço por uma resposta genérica."

        pode_encerrar = categoria == "financeiro" and bool(pedido.get("pagamento_id")) and bool(obter_pagamento_por_id(pedido.get("pagamento_id")))
        if categoria == "financeiro" and "confirmado" in (resposta or "").lower():
            pode_encerrar = True
        if categoria in {"entrega", "prazo", "qualidade"}:
            pode_encerrar = False

        novo_status = "resolvida" if pode_encerrar else "em_analise"
        atualizar_reclamacao(
            reclamacao_id,
            status=novo_status,
            resposta=resposta,
            resolucao="Categoria: " + categoria + ". " + (resolucao or "")
        )
        registrar_evento(
            "reclamacao_resolvida" if novo_status == "resolvida" else "reclamacao_tratada",
            "Reclamação " + reclamacao_id + " tratada na categoria " + categoria + "."
        )
        return {
            "status": "executado",
            "acao": "resolver_reclamacao",
            "resultado": {
                "receita": 0,
                "custo": 0,
                "reclamacao_id": reclamacao_id,
                "pedido_id": pedido_id,
                "categoria": categoria,
                "status_reclamacao": novo_status,
                "resolucao": resolucao,
                "resposta_preparada": resposta,
                "envio_externo": False
            }
        }

    def executar_pedido(self, decisao):
        """Produz o resultado real do serviço contratado usando o Cérebro da EVOLIA."""
        from memory import obter_pedido_cliente, atualizar_pedido_cliente
        from ai import gerar_resultado_servico
        from pedido_fluxo import sincronizar_pedido_pagamento

        pedido_id = str(decisao.get("pedido_id") or "").strip()
        pedido = obter_pedido_cliente(pedido_id)
        if not pedido:
            return {"status": "bloqueado", "acao": "executar_pedido", "motivo": "Pedido não encontrado."}

        if pedido.get("status") == "aguardando_pagamento":
            sincronizar_pedido_pagamento(pedido_id)
            pedido = obter_pedido_cliente(pedido_id) or pedido

        if pedido.get("status") != "em_execucao":
            return {
                "status": "bloqueado",
                "acao": "executar_pedido",
                "motivo": "O pedido precisa estar em execução após pagamento confirmado.",
                "pedido_status": pedido.get("status")
            }

        execucao_anterior = pedido.get("execucao") or {}
        if execucao_anterior.get("status") == "resultado_pronto" and execucao_anterior.get("resultado"):
            return {
                "status": "executado",
                "acao": "executar_pedido",
                "resultado": {
                    "receita": 0,
                    "custo": 0,
                    "pedido_id": pedido_id,
                    "status": "resultado_pronto",
                    "resultado": execucao_anterior.get("resultado"),
                    "ja_existente": True
                }
            }

        producao = gerar_resultado_servico(pedido)
        if producao.get("status") != "sucesso":
            registrar_evento(
                "pedido_producao_bloqueada",
                "Produção do pedido " + pedido_id + " bloqueada: " + str(producao.get("erro") or "erro desconhecido")
            )
            return {
                "status": "bloqueado",
                "acao": "executar_pedido",
                "pedido_id": pedido_id,
                "motivo": producao.get("erro") or "Não foi possível produzir o serviço.",
                "modelo_utilizado": producao.get("modelo_utilizado")
            }

        dados = producao.get("resultado") or {}
        artefato = {
            "tipo": "resultado_de_servico",
            "servico": str(pedido.get("servico") or "").strip(),
            "descricao_cliente": str(pedido.get("descricao") or "").strip(),
            "escopo": (pedido.get("proposta") or {}).get("escopo") or [],
            "titulo": dados.get("titulo"),
            "conteudo": dados.get("entrega"),
            "itens_entregues": dados.get("itens_entregues") or [],
            "limitacoes": dados.get("limitacoes") or [],
            "fontes": dados.get("fontes") or [],
            "confianca": dados.get("confianca"),
            "validacao": {
                "pedido_pago": True,
                "escopo_presente": bool((pedido.get("proposta") or {}).get("escopo")),
                "conteudo_gerado": True,
                "producao_por_ia": True,
                "envio_externo": False
            },
            "produzido_em": agora()
        }

        execucao = {
            "status": "resultado_pronto",
            "iniciada_em": agora(),
            "resultado": artefato
        }
        atualizado = atualizar_pedido_cliente(
            pedido_id,
            execucao=execucao,
            observacao="Resultado real do serviço produzido pela IA e aguardando validação/entrega."
        )
        registrar_evento("pedido_executado", "Resultado real produzido para o pedido " + pedido_id + ".")

        return {
            "status": "executado",
            "acao": "executar_pedido",
            "resultado": {
                "receita": 0,
                "custo": 0,
                "pedido_id": pedido_id,
                "status": "resultado_pronto",
                "resultado": artefato,
                "envio_externo": False
            },
            "pedido": atualizado
        }

    def validar_resultado(self, decisao):
        """Valida o resultado e entrega por e-mail somente após envio confirmado."""
        from memory import obter_pedido_cliente, atualizar_pedido_cliente
        from entrega_email import enviar_resultado_por_email

        pedido_id = str(decisao.get("pedido_id") or "").strip()
        pedido = obter_pedido_cliente(pedido_id)
        if not pedido:
            return {"status": "bloqueado", "acao": "validar_resultado", "motivo": "Pedido não encontrado."}

        if pedido.get("status") != "em_execucao":
            return {"status": "bloqueado", "acao": "validar_resultado", "motivo": "O pedido precisa estar em execução para validação.", "pedido_status": pedido.get("status")}

        execucao = pedido.get("execucao") or {}
        resultado = execucao.get("resultado") or {}
        validacao = resultado.get("validacao") or {}
        checks = {
            "resultado_presente": bool(resultado),
            "servico_identificado": bool(str(resultado.get("servico") or "").strip()),
            "escopo_presente": bool(resultado.get("escopo")),
            "conteudo_presente": bool(str(resultado.get("conteudo") or "").strip()),
            "pedido_pago": validacao.get("pedido_pago") is True,
        }
        if not all(checks.values()):
            return {"status": "bloqueado", "acao": "validar_resultado", "motivo": "O resultado não passou na validação interna.", "checks": checks}

        email = str(pedido.get("email") or "").strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            return {"status": "bloqueado", "acao": "validar_resultado", "motivo": "O pedido não possui um e-mail válido para entrega."}

        entrega_anterior = pedido.get("entrega") or {}
        if entrega_anterior.get("email_enviado") and entrega_anterior.get("resend_id"):
            return {"status": "executado", "acao": "validar_resultado", "resultado": {"receita": 0, "custo": 0, "pedido_id": pedido_id, "validado": True, "checks": checks, "entregue": True, "entrega": entrega_anterior, "envio_externo": True, "ja_enviado": True}}

        envio = enviar_resultado_por_email(pedido, resultado)
        if envio.get("status") != "enviado":
            registrar_evento("pedido_entrega_bloqueada", "Entrega por e-mail do pedido " + pedido_id + " bloqueada: " + str(envio.get("erro") or "erro desconhecido"))
            return {"status": "bloqueado", "acao": "validar_resultado", "pedido_id": pedido_id, "motivo": envio.get("erro") or "Não foi possível enviar o resultado por e-mail.", "envio_externo": False}

        entrega = {
            "texto": str(resultado.get("conteudo") or "").strip(),
            "url": None,
            "email_enviado": True,
            "resend_id": envio.get("id"),
            "destinatario": email,
            "enviado_em": agora()
        }
        atualizado = atualizar_pedido_cliente(pedido_id, status="entregue", entrega=entrega, observacao="Resultado validado e entregue por e-mail via Resend.")
        registrar_evento("pedido_validado_entregue", "Resultado validado e entregue por e-mail no pedido " + pedido_id + ".")
        return {"status": "executado", "acao": "validar_resultado", "resultado": {"receita": 0, "custo": 0, "pedido_id": pedido_id, "validado": True, "checks": checks, "entregue": True, "entrega": entrega, "envio_externo": True, "resend_id": envio.get("id")}, "pedido": atualizado}

    def medir_resultado(self, decisao):
        acoes = obter_acoes_externas(limite=100)
        estrategia = decisao.get("estrategia")
        if estrategia:
            acoes = [a for a in acoes if a.get("estrategia") == estrategia]
        receita = sum(float(f.get("receita") or 0) for a in acoes for f in (a.get("feedback") or []))
        custo = sum(float(f.get("custo") or 0) for a in acoes for f in (a.get("feedback") or []))
        vendas = sum(bool(f.get("venda")) for a in acoes for f in (a.get("feedback") or []))
        registrar_evento("medicao_comercial", "Resultado comercial medido.")
        return {"status": "executado", "acao": "medir_resultado", "resultado": {"receita": receita, "custo": custo, "resultado": receita - custo, "vendas": int(vendas), "acoes_analisadas": len(acoes)}}

    def testar_estrategia(self, decisao):
        anterior = decisao.get("resultado_anterior") or {}
        proposta_anterior = anterior.get("resultado", {}).get("proposta") if isinstance(anterior, dict) else None
        estrategia = decisao.get("estrategia", "estratégia sem nome")
        plano = {
            "objetivo": decisao.get("objetivo"),
            "nicho": decisao.get("nicho"),
            "cliente_alvo": decisao.get("cliente_alvo"),
            "oferta": decisao.get("oferta"),
            "canal": decisao.get("canal"),
            "preco_teste": decisao.get("preco_teste"),
            "custo_teste": decisao.get("custo_teste", 0),
            "acao_imediata": decisao.get("acao_imediata"),
            "proposta_anterior": proposta_anterior
        }
        restricoes = {
            "receita_real": False,
            "custo_real": False,
            "acoes_externas": False,
            "requer_autorizacao_externa": True
        }
        teste = registrar_teste(
            estrategia=estrategia, plano=plano, restricoes=restricoes,
            execucao={"status": "planejado", "acao": "testar_estrategia"},
            receita=0, custo=0, resultado=0, status="planejado"
        )
        registrar_evento("teste_planejado", f"Teste estruturado para a estratégia: {estrategia}")
        return {
            "status": "executado", "acao": "testar_estrategia",
            "resultado": {
                "receita": 0, "custo": 0, "estrategia": estrategia,
                "plano": plano, "restricoes": restricoes, "teste_registrado": teste
            }
        }
