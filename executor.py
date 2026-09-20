from datetime import datetime, timezone
import uuid

from Permissões import solicitar_permissao
from pesquisa import pesquisar
from memory import registrar_evento, registrar_teste, registrar_acao_externa, obter_acoes_externas

ACOES_INTERNAS = {
    "aguardar", "pesquisar", "analisar", "criar_oferta",
    "criar_proposta", "criar_conteudo", "preparar_abordagem", "pesquisar_alvo", "testar_estrategia"
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
            elif acao == "criar_oferta":
                resultado = self.criar_oferta(decisao)
            elif acao == "criar_proposta":
                resultado = self.criar_proposta(decisao)
            elif acao == "criar_conteudo":
                resultado = self.criar_conteudo(decisao)
            elif acao == "pesquisar_alvo":
                resultado = self.pesquisar_alvo(decisao)
            elif acao == "preparar_abordagem":
                resultado = self.preparar_abordagem(decisao)
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

        consultas = [
            f'"{cliente}" {nicho} perfil Instagram Brasil site:instagram.com',
            f'"{cliente}" {nicho} LinkedIn Brasil site:linkedin.com/in/',
            f'"{cliente}" {nicho} WhatsApp Brasil site:wa.me',
            f'"{cliente}" {nicho} contato WhatsApp Brasil',
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

        def adicionar_candidato(item, canal):
            url = (item.get("url") or "").strip()
            if not url or url in vistos:
                return
            vistos.add(url)
            candidatos.append({
                "url": url,
                "titulo": item.get("titulo"),
                "site": item.get("site"),
                "resumo": item.get("resumo"),
                "canal": canal
            })

        for item in resultados:
            url = (item.get("url") or "").strip().lower()
            if "instagram.com/" in url and "/explore" not in url and "/accounts/" not in url and "/about" not in url:
                adicionar_candidato(item, "instagram")
            elif "linkedin.com/in/" in url:
                adicionar_candidato(item, "linkedin")
            elif "wa.me/" in url or "api.whatsapp.com/send" in url:
                adicionar_candidato(item, "whatsapp")

        if not candidatos:
            return {
                "status": "bloqueado",
                "acao": "pesquisar_alvo",
                "motivo": "Nenhum alvo público específico e contatável foi encontrado nas pesquisas realizadas.",
                "consultas": consultas_executadas,
                "resultado": {"receita": 0, "custo": 0, "candidatos": []}
            }

        alvo = candidatos[0]
        canal = alvo["canal"]
        registrar_evento("alvo_pesquisado", f"Alvo público encontrado: {alvo['url']} via {canal}.")
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
                "candidatos": candidatos[:5]
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
        problema = (decisao.get("problema") or "").strip()
        oferta = (decisao.get("oferta") or "").strip()
        if not problema or not oferta or cliente == "cliente potencial":
            return {"status": "bloqueado", "acao": "preparar_abordagem", "motivo": "A oportunidade ainda não possui problema, oferta e alvo suficientemente definidos para uma abordagem."}
        mensagem = proposta_anterior or decisao.get("proposta") or (
            f"Olá! Vi seu trabalho e identifiquei uma oportunidade relacionada a {decisao.get('problema', 'uma necessidade do seu negócio')}. "
            f"Tenho uma proposta de teste pequeno para {decisao.get('oferta', 'uma solução específica')}. "
            "Posso te explicar em poucas linhas?"
        )
        contexto = {"objetivo": decisao.get("objetivo"), "nicho": decisao.get("nicho"), "problema": decisao.get("problema"), "oferta": decisao.get("oferta"), "preco_teste": decisao.get("preco_teste"), "url_alvo": url_alvo}
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
