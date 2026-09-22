from datetime import datetime, timezone
import uuid

from Permissões import solicitar_permissao
from pesquisa import pesquisar
from memory import registrar_evento, registrar_teste, registrar_acao_externa, obter_acoes_externas, registrar_lead, obter_leads, atualizar_lead

ACOES_INTERNAS = {
    "aguardar", "pesquisar", "analisar", "analisar_reclamacao", "criar_oferta",
    "criar_proposta", "criar_conteudo", "preparar_abordagem", "preparar_followup", "acompanhar_lead", "processar_resposta", "medir_resultado", "pesquisar_alvo", "validar_alvo", "testar_estrategia"
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
            elif acao == "criar_oferta":
                resultado = self.criar_oferta(decisao)
            elif acao == "criar_proposta":
                resultado = self.criar_proposta(decisao)
            elif acao == "criar_conteudo":
                resultado = self.criar_conteudo(decisao)
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

    def criar_oferta(self, decisao):
        anterior = decisao.get("resultado_anterior") or {}
        analise_anterior = anterior.get("resultado", {}).get("analise") if isinstance(anterior, dict) else None
        oferta = {
            "estrategia": decisao.get("estrategia"),
            "nicho": decisao.get("nicho"),
            "cliente_alvo": decisao.get("cliente_alvo"),
            "problema": decisao.get("problema"),
            "oferta": decisao.get("oferta"),
            "canal": decisao.get("canal"),
            "preco_teste": decisao.get("preco_teste"),
            "custo_teste": decisao.get("custo_teste", 0),
            "analise_anterior": analise_anterior
        }
        registrar_evento("oferta_criada", f"Oferta estruturada: {decisao.get('oferta')}")
        return {"status": "executado", "acao": "criar_oferta", "resultado": {"receita": 0, "custo": 0, "oferta": oferta}}

    def criar_proposta(self, decisao):
        anterior = decisao.get("resultado_anterior") or {}
        oferta_anterior = anterior.get("resultado", {}).get("oferta") if isinstance(anterior, dict) else None
        cliente = decisao.get("cliente_alvo", "cliente potencial")
        oferta = decisao.get("oferta", "serviço")
        if isinstance(oferta_anterior, dict):
            oferta = oferta_anterior.get("oferta") or oferta
        problema = decisao.get("problema", "uma necessidade do cliente")
        preco = decisao.get("preco_teste")
        proposta = f"Olá! Identifiquei que {cliente} pode estar enfrentando {problema}. Posso oferecer {oferta} "
        if preco is not None:
            proposta += "em formato de teste por R$" + str(preco) + "."
        proposta += " A ideia é começar com um teste pequeno, medir o resultado e ajustar conforme a necessidade."
        registrar_evento("proposta_criada", f"Proposta preparada para: {cliente}")
        return {
            "status": "executado", "acao": "criar_proposta",
            "resultado": {"receita": 0, "custo": 0, "proposta": proposta, "cliente_alvo": cliente, "preco_teste": preco}
        }

    def criar_conteudo(self, decisao):
        conteudo = {
            "tema": decisao.get("problema"),
            "oferta": decisao.get("oferta"),
            "cliente_alvo": decisao.get("cliente_alvo"),
            "canal": decisao.get("canal"),
            "formato": decisao.get("formato", "rascunho")
        }
        registrar_evento("conteudo_criado", f"Conteúdo preparado para o canal: {decisao.get('canal')}")
        return {"status": "executado", "acao": "criar_conteudo", "resultado": {"receita": 0, "custo": 0, "conteudo": conteudo}}

    def pesquisar_alvo(self, decisao):
        cliente = decisao.get("cliente_alvo") or "pequenos negócios"
        nicho = decisao.get("nicho") or ""
        localizacao = decisao.get("localizacao", "Brasil")

        termos_busca = " ".join(
            palavra for palavra in str(nicho or "").replace(",", " ").split()
            if len(palavra.strip()) >= 4
        ).strip()
        consultas = [
            f'site:linkedin.com/in/ {termos_busca} Brasil consultor fundador consultoria',
            f'site:linkedin.com/in/ {termos_busca} Brasil vendas gestão processos',
            f'site:linkedin.com/in/ {termos_busca} Brasil "co-fundador" OR "fundador"',
            f'site:linkedin.com/in/ {termos_busca} Brasil "consultoria" "B2B"',
        ]

        resultados = []
        consultas_executadas = []
        for consulta in consultas:
            pesquisa = pesquisar(consulta, localizacao)
            consultas_executadas.append(consulta)
            if isinstance(pesquisa, dict):
                resultados.extend(pesquisa.get("resultados", []))

        candidatos = []
        vistos = set()
        urls_existentes = {
            str(lead.get("url") or "").strip().rstrip("/").lower()
            for lead in obter_leads(limite=500)
            if lead.get("url")
        }

        def normalizar_url(url):
            return str(url or "").strip().rstrip("/").lower()

        def adicionar_candidato(item, canal):
            url = (item.get("url") or "").strip()
            chave = normalizar_url(url)
            if not chave or chave in vistos:
                return
            vistos.add(chave)
            if chave in urls_existentes:
                return
            candidatos.append({
                "url": url,
                "titulo": item.get("titulo"),
                "site": item.get("site"),
                "resumo": item.get("resumo"),
                "canal": canal
            })

        palavras_nicho = [
            palavra.lower() for palavra in str(nicho or "").replace(",", " ").split()
            if len(palavra.strip()) >= 4
        ]
        palavras_negocio = [
            "consultor", "consultoria", "fundador", "co-fundador", "vendas",
            "gestão", "gestao", "processos", "b2b", "comercial", "negócios",
            "negocios", "serviços", "servicos"
        ]

        for item in resultados:
            url = (item.get("url") or "").strip().lower()
            texto = " ".join([
                str(item.get("titulo") or ""),
                str(item.get("resumo") or "")
            ]).lower()
            if "linkedin.com/in/" in url:
                sinais_nicho = sum(1 for palavra in palavras_nicho if palavra in texto)
                sinais_negocio = sum(1 for palavra in palavras_negocio if palavra in texto)
                if sinais_nicho >= 1 and sinais_negocio >= 1:
                    adicionar_candidato(item, "linkedin")

        if not candidatos:
            return {
                "status": "bloqueado",
                "acao": "pesquisar_alvo",
                "motivo": "Nenhum alvo público específico e contatável foi encontrado nas pesquisas realizadas.",
                "consultas": consultas_executadas,
                "resultado": {"receita": 0, "custo": 0, "candidatos": []}
            }

        leads = []
        for candidato in candidatos[:5]:
            titulo = (candidato.get("titulo") or "").strip()
            resumo = (candidato.get("resumo") or "").strip()
            motivo = (
                f"Alvo encontrado em pesquisa pública para o nicho '{nicho or cliente}'. "
                f"O canal '{candidato.get('canal')}' possui URL específica e pode permitir contato."
            )
            evidencia = [
                {"tipo": "url_publica", "url": candidato.get("url")},
                {"tipo": "resultado_pesquisa", "resumo": resumo}
            ]
            lead = registrar_lead(
                proveniencia="pesquisa_alvo",
                url=candidato.get("url"),
                canal=candidato.get("canal"),
                nome=titulo,
                resumo=resumo,
                motivo_aderencia=motivo,
                evidencia_publica=evidencia,
                estrategia=decisao.get("estrategia"),
                nicho=nicho,
                problema=decisao.get("problema"),
                oferta=decisao.get("oferta"),
                confianca="media"
            )
            if lead:
                leads.append(lead)

        # Ranqueia os candidatos antes de escolher o principal.
        # O ranking usa somente evidencias ja retornadas pela pesquisa.
        termos = []
        for campo in (nicho, cliente, decisao.get("problema")):
            termos.extend(
                palavra.lower()
                for palavra in str(campo or "").replace(",", " ").split()
                if len(palavra.strip()) >= 4
            )
        termos = list(dict.fromkeys(termos))

        def pontuar(candidato):
            texto = " ".join([
                str(candidato.get("titulo") or ""),
                str(candidato.get("resumo") or "")
            ]).lower()
            score = 0
            if candidato.get("canal") in {"linkedin", "instagram"}:
                score += 2
            if "/in/" in str(candidato.get("url") or "") or "instagram.com/" in str(candidato.get("url") or ""):
                score += 2
            score += min(6, sum(1 for termo in termos if termo in texto))
            if candidato.get("resumo"):
                score += 1
            candidato["score_aderencia"] = score
            return score

        candidatos.sort(key=pontuar, reverse=True)

        alvo = candidatos[0]
        canal = alvo["canal"]
        lead_principal = next(
            (lead for lead in leads if lead.get("url") == alvo.get("url")),
            leads[0] if leads else None
        )
        registrar_evento(
            "alvo_pesquisado",
            f"Alvo público encontrado: {alvo['url']} via {canal}; lead registrado com proveniência e evidências."
        )
        return {
            "status": "executado",
            "acao": "pesquisar_alvo",
            "consultas": consultas_executadas,
            "resultado": {
                "receita": 0,
                "custo": 0,
                "url_alvo": alvo["url"],
                "canal": canal,
                "alvo_encontrado": alvo,
                "lead_principal": lead_principal,
                "leads_registrados": leads,
                "candidatos": candidatos[:5]
            }
        }

    def validar_alvo(self, decisao):
        """Valida o alvo com evidencia publica antes de permitir uma abordagem."""
        anterior = decisao.get("resultado_anterior") or {}
        resultado_anterior = anterior.get("resultado", {}) if isinstance(anterior, dict) else {}
        alvo = resultado_anterior.get("alvo_encontrado") or {}
        url = (resultado_anterior.get("url_alvo") or decisao.get("url_alvo") or "").strip()

        if not url.startswith(("https://", "http://")):
            return {"status": "bloqueado", "acao": "validar_alvo", "motivo": "Nao ha URL publica especifica para validar o alvo."}

        consulta = f'site:linkedin.com/in/ "{url}" {decisao.get("nicho", "")} {decisao.get("cliente_alvo", "")}'
        pesquisa = pesquisar(consulta, decisao.get("localizacao", "Brasil"))
        resultados = pesquisa.get("resultados", []) if isinstance(pesquisa, dict) else []

        texto_alvo = " ".join([
            str(alvo.get("titulo") or ""),
            str(alvo.get("resumo") or "")
        ]).strip()
        texto_pesquisa = " ".join(
            str(item.get("resumo") or "")
            for item in resultados
            if isinstance(item, dict)
        ).strip()
        texto = f"{texto_alvo} {texto_pesquisa}".strip().lower()

        palavras_nicho = [
            termo.lower() for termo in str(decisao.get("nicho") or "").replace(",", " ").split()
            if len(termo.strip()) >= 4
        ]
        sinais_nicho = [termo for termo in palavras_nicho if termo in texto]

        sinais_negocio = [
            termo for termo in [
                "consultor", "consultoria", "fundador", "co-fundador", "vendas",
                "gestão", "gestao", "processos", "b2b", "comercial", "negócios",
                "negocios", "serviços", "servicos"
            ] if termo in texto
        ]

        sinais = list(dict.fromkeys(sinais_nicho + sinais_negocio))
        confianca = "alta" if len(sinais_nicho) >= 2 and len(sinais_negocio) >= 2 else "media" if sinais_nicho and sinais_negocio else "baixa"
        validado = bool(url) and bool(texto_alvo) and bool(sinais_nicho) and bool(sinais_negocio)

        evidencia = [
            {"tipo": "url_alvo", "url": url},
            {"tipo": "sinais_aderencia", "termos_nicho": sinais_nicho, "termos_negocio": sinais_negocio},
            {"tipo": "resultado_validacao", "resumos": [
                str(item.get("resumo") or "")[:500]
                for item in resultados[:5] if isinstance(item, dict)
            ]}
        ]
        motivo = (
            "O perfil público apresenta sinais de aderência ao nicho e à atividade comercial pesquisada. "
            "Isso valida o alvo como potencial cliente, mas não prova que ele tenha o problema específico."
            if validado else
            "A pesquisa pública não trouxe evidência suficiente de que o perfil pertença ao nicho e à atividade pesquisados."
        )

        lead = resultado_anterior.get("lead_principal") or {}
        if not lead.get("id"):
            for lead_memoria in reversed(obter_leads(limite=100)):
                if (lead_memoria.get("url") or "").strip() == url and (
                    not decisao.get("estrategia") or lead_memoria.get("estrategia") == decisao.get("estrategia")
                ):
                    lead = lead_memoria
                    break
        if lead.get("id"):
            atualizar_lead(
                lead["id"],
                status="validado" if validado else "nao_validado",
                evidencia_publica=evidencia,
                motivo_aderencia=motivo,
                confianca=confianca
            )

        registrar_evento("validacao_alvo", f"Alvo {'validado' if validado else 'nao validado'} por aderencia de nicho: {url}")
        lead_principal = lead
        return {
            "status": "executado" if validado else "bloqueado",
            "acao": "validar_alvo",
            "resultado": {
                "receita": 0, "custo": 0, "validado": validado,
                "confianca": confianca, "url_alvo": url,
                "canal": lead_principal.get("canal") or alvo.get("canal"),
                "cliente_alvo": lead_principal.get("nome") or alvo.get("titulo"),
                "alvo": alvo, "lead_principal": lead_principal,
                "sinais_aderencia": sinais, "evidencia": evidencia, "motivo": motivo
            }
        }

    def preparar_abordagem(self, decisao):
        anterior = decisao.get("resultado_anterior") or {}
        proposta_anterior = None
        if isinstance(anterior, dict):
            proposta_anterior = anterior.get("resultado", {}).get("proposta")
        cliente = decisao.get("cliente_alvo") or "cliente potencial"
        canal = decisao.get("canal", "canal não definido")
        url_alvo = (decisao.get("url_alvo") or "").strip()
        alvo_encontrado = None
        if isinstance(anterior, dict):
            resultado_anterior = anterior.get("resultado", {})
            if isinstance(resultado_anterior, dict):
                canal = resultado_anterior.get("canal") or canal
                url_alvo = (resultado_anterior.get("url_alvo") or url_alvo).strip()
                alvo_encontrado = resultado_anterior.get("alvo_encontrado") or {}
                cliente = alvo_encontrado.get("titulo") or cliente
        if canal not in {"instagram", "linkedin", "whatsapp", "email"}:
            return {"status": "bloqueado", "acao": "preparar_abordagem", "motivo": "Canal externo não suportado ou não definido."}
        if not url_alvo.startswith(("https://", "http://")):
            return {"status": "bloqueado", "acao": "preparar_abordagem", "motivo": "URL pública específica do alvo não foi definida."}
        alvo_ja_validado = bool(decisao.get("alvo_validado"))
        if isinstance(anterior, dict) and anterior.get("acao") == "validar_alvo":
            validacao = anterior.get("resultado", {}) or {}
            if not validacao.get("validado"):
                return {
                    "status": "bloqueado",
                    "acao": "preparar_abordagem",
                    "motivo": "A abordagem foi bloqueada porque o alvo nao apresentou evidencia publica suficiente de aderencia ao nicho e à atividade pesquisada."
                }
            url_alvo = (validacao.get("url_alvo") or url_alvo).strip()
            canal = validacao.get("canal") or canal
            cliente = validacao.get("cliente_alvo") or cliente
            alvo_ja_validado = True
        if not alvo_ja_validado:
            return {
                "status": "bloqueado",
                "acao": "preparar_abordagem",
                "motivo": "A abordagem exige validação pública do alvo antes do contato."
            }

        problema = (decisao.get("problema") or "").strip()
        oferta = (decisao.get("oferta") or "").strip()
        if not problema or not oferta or cliente == "cliente potencial":
            return {"status": "bloqueado", "acao": "preparar_abordagem", "motivo": "A oportunidade ainda não possui problema, oferta e alvo suficientemente definidos para uma abordagem."}
        mensagem = proposta_anterior or decisao.get("proposta") or (
            f"Olá! Vi seu trabalho e acredito que uma solução relacionada a {decisao.get('oferta', 'uma solução específica')} pode ser relevante para o seu contexto. "
            "Tenho uma ideia de teste pequeno, sem compromisso. Posso te explicar em poucas linhas?"
        )
        contexto = {"objetivo": decisao.get("objetivo"), "nicho": decisao.get("nicho"), "problema": decisao.get("problema"), "oferta": decisao.get("oferta"), "preco_teste": decisao.get("preco_teste"), "url_alvo": url_alvo}
        leads = obter_leads(limite=100)
        lead_encontrado = None
        for lead in reversed(leads):
            lead_url = (lead.get("url") or "").strip()
            if lead_url == url_alvo or (lead.get("nome") == cliente and lead.get("estrategia") == decisao.get("estrategia")):
                lead_encontrado = lead
                contexto["lead_id"] = lead.get("id")
                contexto["evidencia_alvo"] = lead.get("evidencia_publica") or []
                break

        # A flag recebida pela IA não substitui o estado persistido do funil.
        # Somente um lead realmente marcado como "validado" pode gerar abordagem.
        if not lead_encontrado or lead_encontrado.get("status") != "validado":
            return {
                "status": "bloqueado",
                "acao": "preparar_abordagem",
                "motivo": "A abordagem exige um lead persistido com status 'validado'."
            }

        existentes = obter_acoes_externas(limite=100)
        for existente in reversed(existentes):
            contexto_existente = existente.get("contexto") or {}
            url_existente = (contexto_existente.get("url_alvo") or "").strip()
            mesma_estrategia = existente.get("estrategia") == decisao.get("estrategia")
            mesmo_alvo = existente.get("alvo") == cliente
            mesma_url = bool(url_existente and url_existente == url_alvo)
            status_existente = existente.get("status")
            if (existente.get("tipo") == "abordagem_comercial"
                    and mesma_estrategia
                    and (mesmo_alvo or mesma_url)
                    and status_existente in {"aguardando_autorizacao", "autorizada", "executando", "executada"}):
                return {"status": "executado", "acao": "preparar_abordagem", "resultado": {"receita": 0, "custo": 0, "acao_externa_id": existente["id"], "status_acao_externa": status_existente, "alvo": cliente, "canal": canal, "mensagem": existente.get("mensagem", mensagem), "duplicata": True, "motivo": "Alvo ou URL já abordado nesta estratégia; nova abordagem bloqueada para evitar duplicidade."}}
        acao = registrar_acao_externa(
            tipo="abordagem_comercial", alvo=cliente, canal=canal, mensagem=mensagem,
            estrategia=decisao.get("estrategia"), contexto=contexto
        )
        registrar_evento("abordagem_preparada", f"Abordagem preparada para {cliente} no canal {canal}; aguardando autorização.")
        return {"status": "executado", "acao": "preparar_abordagem", "resultado": {"receita": 0, "custo": 0, "acao_externa_id": acao["id"], "status_acao_externa": acao["status"], "alvo": cliente, "canal": canal, "mensagem": mensagem}}
    def acompanhar_lead(self, decisao):
        acoes = obter_acoes_externas(limite=100)
        estrategia = decisao.get("estrategia")
        url_alvo = (decisao.get("url_alvo") or "").strip()
        cliente = (decisao.get("cliente_alvo") or "").strip()
        if estrategia:
            acoes = [a for a in acoes if a.get("estrategia") == estrategia]
        if url_alvo or cliente:
            acoes_alvo = [
                a for a in acoes
                if (url_alvo and (a.get("contexto", {}).get("url_alvo") or "") == url_alvo)
                or (cliente and (a.get("alvo") or "") == cliente)
            ]
            if acoes_alvo:
                acoes = acoes_alvo

        ultimo = acoes[-1] if acoes else None
        feedbacks = (ultimo or {}).get("feedback", []) or []
        respostas = [f for a in feedbacks if f.get("resposta")]
        interesses = [f for f in feedbacks if f.get("interesse")]
        vendas = [f for f in feedbacks if f.get("venda")]

        # O acompanhamento passa a produzir um estado comercial explícito.
        # Isso permite ao próximo ciclo decidir entre esperar, avançar ou
        # preparar follow-up sem tratar todo contato executado como lead frio.
        if vendas:
            fase = "venda"
        elif interesses:
            fase = "interesse"
        elif respostas:
            fase = "resposta"
        elif ultimo and ultimo.get("status") == "executada":
            fase = "aguardando_resposta"
        elif ultimo and ultimo.get("status") in {"aguardando_autorizacao", "autorizada"}:
            fase = "aguardando_contato"
        elif ultimo:
            fase = ultimo.get("status") or "em_acompanhamento"
        else:
            fase = "sem_contato"

        lead_id = (ultimo.get("contexto") or {}).get("lead_id") if ultimo else None
        if lead_id:
            status_lead = {
                "venda": "venda",
                "interesse": "interesse",
                "resposta": "resposta",
                "aguardando_resposta": "contato_executado",
                "aguardando_contato": "abordagem_preparada"
            }.get(fase)
            if status_lead:
                atualizar_lead(
                    lead_id,
                    status=status_lead,
                    ultima_acao_externa_id=ultimo.get("id"),
                    fase_comercial=fase
                )

        registrar_evento("acompanhamento_lead", f"Estado comercial identificado: {fase}.")
        return {"status": "executado", "acao": "acompanhar_lead", "resultado": {
            "receita": 0, "custo": 0, "ultima_acao": ultimo,
            "feedbacks": feedbacks, "fase_comercial": fase,
            "respostas": len(respostas), "interesses": len(interesses),
            "vendas": len(vendas), "acoes_analisadas": len(acoes)
        }}

    def processar_resposta(self, decisao):
        """Interpreta feedback já registrado e define o próximo passo sem contato externo automático."""
        acoes = obter_acoes_externas(limite=100)
        estrategia = decisao.get("estrategia")
        url_alvo = (decisao.get("url_alvo") or "").strip()
        cliente = (decisao.get("cliente_alvo") or "").strip()

        if estrategia:
            acoes = [a for a in acoes if a.get("estrategia") == estrategia]
        if url_alvo or cliente:
            filtradas = [
                a for a in acoes
                if (url_alvo and (a.get("contexto", {}).get("url_alvo") or "") == url_alvo)
                or (cliente and (a.get("alvo") or "") == cliente)
            ]
            if filtradas:
                acoes = filtradas

        candidatos = []
        for acao in acoes:
            for feedback in acao.get("feedback", []) or []:
                candidatos.append((acao, feedback))

        if not candidatos:
            return {"status": "bloqueado", "acao": "processar_resposta", "motivo": "Não há resposta ou interesse registrado para processar."}

        origem, feedback = candidatos[-1]
        if feedback.get("venda"):
            proximo_passo = "encaminhar para o ciclo de pedido, pagamento e entrega."
            fase = "venda"
            lead_id = (origem.get("contexto") or {}).get("lead_id")
            lead_venda = next((x for x in obter_leads(limite=100) if x.get("id") == lead_id), None)
            if lead_venda:
                try:
                    from pedido_fluxo import criar_pedido_de_venda_lead
                    pedido_resultado = criar_pedido_de_venda_lead(lead_venda, origem, feedback)
                except Exception as erro:
                    pedido_resultado = {"ok": False, "erro": str(erro)}
            else:
                pedido_resultado = {"ok": False, "erro": "Lead da venda não encontrado na memória."}
        elif feedback.get("interesse"):
            proximo_passo = "preparar proposta ou próximo passo comercial específico para o interesse demonstrado."
            fase = "interesse"
        elif feedback.get("resposta"):
            proximo_passo = "analisar a resposta e preparar uma resposta comercial adequada; não enviar automaticamente."
            fase = "resposta"
        else:
            proximo_passo = "aguardar novo sinal do lead."
            fase = "aguardando_resposta"

        lead_id = (origem.get("contexto") or {}).get("lead_id")
        if lead_id:
            atualizar_lead(
                lead_id,
                status=fase,
                ultima_acao_externa_id=origem.get("id"),
                fase_comercial=fase,
                proxima_acao=proximo_passo
            )

        registrar_evento("processamento_resposta", f"Próximo passo comercial definido: {fase}.")
        return {
            "status": "executado",
            "acao": "processar_resposta",
            "resultado": {
                "receita": 0,
                "custo": 0,
                "fase_comercial": fase,
                "acao_origem_id": origem.get("id"),
                "feedback": feedback,
                "proximo_passo": proximo_passo,
                "contato_externo_automatico": False,
                "pedido": pedido_resultado if fase == "venda" else None
            }
        }

    def preparar_followup(self, decisao):
        acoes = obter_acoes_externas(limite=100)
        candidatas = [a for a in acoes if a.get("status") == "executada"]
        estrategia = decisao.get("estrategia")
        url_alvo = (decisao.get("url_alvo") or "").strip()
        cliente = (decisao.get("cliente_alvo") or "").strip()
        if estrategia:
            candidatas = [a for a in candidatas if a.get("estrategia") == estrategia]
        if url_alvo or cliente:
            filtradas = [
                a for a in candidatas
                if (url_alvo and (a.get("contexto", {}).get("url_alvo") or "") == url_alvo)
                or (cliente and (a.get("alvo") or "") == cliente)
            ]
            if filtradas:
                candidatas = filtradas
        if not candidatas:
            return {"status": "bloqueado", "acao": "preparar_followup", "motivo": "Não há abordagem executada disponível para o alvo relevante."}
        origem = candidatas[-1]

        feedbacks_origem = origem.get("feedback", []) or []
        if any(f.get("venda") for f in feedbacks_origem):
            return {"status": "bloqueado", "acao": "preparar_followup", "motivo": "A venda já foi confirmada; não criar follow-up comercial."}
        if any(f.get("interesse") or f.get("resposta") for f in feedbacks_origem):
            return {"status": "bloqueado", "acao": "preparar_followup", "motivo": "O alvo já respondeu ou demonstrou interesse; o próximo passo deve tratar a resposta existente."}

        if origem.get("tipo") == "followup_comercial":
            return {"status": "bloqueado", "acao": "preparar_followup", "motivo": "O último contato já foi um follow-up; aguarde novo feedback antes de criar outro."}
        if any(a.get("contexto", {}).get("acao_origem_id") == origem.get("id") for a in acoes):
            return {"status": "bloqueado", "acao": "preparar_followup", "motivo": "Este contato já possui follow-up registrado."}
        mensagem = "Olá! Passando para acompanhar nossa conversa. Se ainda fizer sentido, posso apresentar rapidamente a proposta."
        contexto = dict(origem.get("contexto") or {})
        if any(
            a.get("tipo") == "followup_comercial"
            and a.get("estrategia") == origem.get("estrategia")
            and (
                a.get("alvo") == origem.get("alvo")
                or ((a.get("contexto") or {}).get("url_alvo") and
                    (a.get("contexto") or {}).get("url_alvo") == (origem.get("contexto") or {}).get("url_alvo"))
            )
            and a.get("status") in {"aguardando_autorizacao", "autorizada", "executada"}
            for a in acoes
        ):
            return {"status": "bloqueado", "acao": "preparar_followup", "motivo": "Já existe follow-up ativo ou executado para este alvo."}
        contexto["acao_origem_id"] = origem.get("id")
        nova = registrar_acao_externa("followup_comercial", origem.get("alvo"), origem.get("canal"), mensagem, origem.get("estrategia"), contexto)
        registrar_evento("followup_preparado", "Follow-up preparado; aguardando autorização.")
        return {"status": "executado", "acao": "preparar_followup", "resultado": {"receita": 0, "custo": 0, "acao_externa_id": nova["id"], "status_acao_externa": nova["status"], "acao_origem_id": origem.get("id"), "mensagem": mensagem}}

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
