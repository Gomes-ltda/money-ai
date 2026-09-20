from datetime import datetime, timezone
import uuid

from Permissões import solicitar_permissao
from pesquisa import pesquisar
from memory import registrar_evento, registrar_teste

ACOES_INTERNAS = {
    "aguardar", "pesquisar", "analisar", "criar_oferta",
    "criar_proposta", "criar_conteudo", "testar_estrategia"
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
        analise = {
            "estrategia": decisao.get("estrategia"),
            "nicho": decisao.get("nicho"),
            "cliente_alvo": decisao.get("cliente_alvo"),
            "problema": decisao.get("problema"),
            "oferta": decisao.get("oferta"),
            "canal": decisao.get("canal"),
            "base_anterior": anterior.get("resultado", anterior)
        }
        registrar_evento("analise", f"Análise estruturada para a estratégia: {decisao.get('estrategia')}")
        return {"status": "executado", "acao": "analisar", "resultado": {"receita": 0, "custo": 0, "analise": analise}}

    def criar_oferta(self, decisao):
        anterior = decisao.get("resultado_anterior") or {}
        oferta = {
            "estrategia": decisao.get("estrategia"),
            "nicho": decisao.get("nicho"),
            "cliente_alvo": decisao.get("cliente_alvo"),
            "problema": decisao.get("problema"),
            "oferta": decisao.get("oferta"),
            "canal": decisao.get("canal"),
            "preco_teste": decisao.get("preco_teste"),
            "custo_teste": decisao.get("custo_teste", 0),
            "base_anterior": anterior.get("resultado", anterior)
        }
        registrar_evento("oferta_criada", f"Oferta estruturada: {decisao.get('oferta')}")
        return {"status": "executado", "acao": "criar_oferta", "resultado": {"receita": 0, "custo": 0, "oferta": oferta}}

    def criar_proposta(self, decisao):
        anterior = decisao.get("resultado_anterior") or {}
        cliente = decisao.get("cliente_alvo", "cliente potencial")
        oferta = decisao.get("oferta", "serviço")
        problema = decisao.get("problema", "uma necessidade do cliente")
        base_anterior = anterior.get("resultado", anterior)
        preco = decisao.get("preco_teste")
        proposta = f"Olá! Identifiquei que {cliente} pode estar enfrentando {problema}. Posso oferecer {oferta} "
        if preco is not None:
            proposta += "em formato de teste por R$" + str(preco) + "."
        proposta += " A ideia é começar com um teste pequeno, medir o resultado e ajustar conforme a necessidade."
        registrar_evento("proposta_criada", f"Proposta preparada para: {cliente}")
        return {
            "status": "executado", "acao": "criar_proposta",
            "resultado": {"receita": 0, "custo": 0, "proposta": proposta, "cliente_alvo": cliente, "preco_teste": preco, "base_anterior": base_anterior}
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

    def testar_estrategia(self, decisao):
        estrategia = decisao.get("estrategia", "estratégia sem nome")
        anterior = decisao.get("resultado_anterior") or {}
        plano = {
            "objetivo": decisao.get("objetivo"),
            "nicho": decisao.get("nicho"),
            "cliente_alvo": decisao.get("cliente_alvo"),
            "oferta": decisao.get("oferta"),
            "canal": decisao.get("canal"),
            "preco_teste": decisao.get("preco_teste"),
            "custo_teste": decisao.get("custo_teste", 0),
            "acao_imediata": decisao.get("acao_imediata"),
            "contexto_anterior": anterior.get("resultado", anterior)
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
