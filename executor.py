from Permissões import solicitar_permissao
from pesquisa import pesquisar


ACOES_INTERNAS = {
    "aguardar",
    "pesquisar",
    "analisar",
    "criar_oferta",
    "criar_proposta",
    "criar_conteudo",
    "testar_estrategia"
}


class Executor:

    def executar(self, decisao):
        acao = decisao.get("acao")

        if not acao:
            return {
                "status": "erro",
                "acao": None,
                "erro": "Nenhuma ação foi definida."
            }

        if acao not in ACOES_INTERNAS:
            return {
                "status": "bloqueado",
                "acao": acao,
                "motivo": "Ação não reconhecida pelo Executor."
            }

        permissao = solicitar_permissao(acao)

        if not permissao.get("permitido"):
            return {
                "status": "bloqueado",
                "acao": acao,
                "motivo": permissao.get(
                    "motivo",
                    "Ação não autorizada."
                )
            }

        try:

            if acao == "aguardar":
                return self.executar_aguardar(decisao)

            if acao == "pesquisar":
                return self.executar_pesquisa(decisao)

            if acao == "analisar":
                return self.executar_analise(decisao)

            if acao == "criar_oferta":
                return self.criar_oferta(decisao)

            if acao == "criar_proposta":
                return self.criar_proposta(decisao)

            if acao == "criar_conteudo":
                return self.criar_conteudo(decisao)

            if acao == "testar_estrategia":
                return self.testar_estrategia(decisao)

        except Exception as erro:
            return {
                "status": "erro",
                "acao": acao,
                "erro": str(erro)
            }

        return {
            "status": "erro",
            "acao": acao,
            "erro": "Ação não implementada."
        }

    # =========================================================
    # AGUARDAR
    # =========================================================

    def executar_aguardar(self, decisao):
        return {
            "status": "aguardando",
            "acao": "aguardar",
            "resultado": {
                "receita": 0,
                "custo": 0
            },
            "motivo": decisao.get(
                "motivo",
                "Nenhuma ação será executada agora."
            )
        }

    # =========================================================
    # PESQUISAR
    # =========================================================

    def executar_pesquisa(self, decisao):

        consulta = (
            decisao.get("consulta")
            or decisao.get("acao_imediata")
            or decisao.get("objetivo")
            or "Encontrar oportunidades de mercado"
        )

        resultado = pesquisar(consulta)

        return {
            "status": "executado",
            "acao": "pesquisar",
            "consulta": consulta,
            "resultado": resultado
        }

    # =========================================================
    # ANALISAR
    # =========================================================

    def executar_analise(self, decisao):

        return {
            "status": "executado",
            "acao": "analisar",
            "resultado": {
                "estrategia": decisao.get(
                    "estrategia"
                ),
                "nicho": decisao.get(
                    "nicho"
                ),
                "cliente_alvo": decisao.get(
                    "cliente_alvo"
                ),
                "problema": decisao.get(
                    "problema"
                ),
                "oferta": decisao.get(
                    "oferta"
                ),
                "canal": decisao.get(
                    "canal"
                )
            }
        }

    # =========================================================
    # CRIAR OFERTA
    # =========================================================

    def criar_oferta(self, decisao):

        oferta = {
            "estrategia": decisao.get(
                "estrategia"
            ),
            "nicho": decisao.get(
                "nicho"
            ),
            "cliente_alvo": decisao.get(
                "cliente_alvo"
            ),
            "problema": decisao.get(
                "problema"
            ),
            "oferta": decisao.get(
                "oferta"
            ),
            "canal": decisao.get(
                "canal"
            ),
            "preco_teste": decisao.get(
                "preco_teste"
            )
        }

        return {
            "status": "executado",
            "acao": "criar_oferta",
            "resultado": {
                "receita": 0,
                "custo": 0,
                "oferta": oferta
            }
        }

    # =========================================================
    # CRIAR PROPOSTA
    # =========================================================

    def criar_proposta(self, decisao):

        cliente = decisao.get(
            "cliente_alvo",
            "cliente potencial"
        )

        oferta = decisao.get(
            "oferta",
            "serviço"
        )

        problema = decisao.get(
            "problema",
            "uma necessidade do cliente"
        )

        preco = decisao.get(
            "preco_teste"
        )

        proposta = (
            f"Olá! Identifiquei que {cliente} pode "
            f"estar enfrentando {problema}. "
            f"Posso oferecer {oferta} "
        )

        if preco:
            proposta += (
                f"em formato de teste por "
                f"R${preco}."
            )

        proposta += (
            " A ideia é começar com um teste pequeno, "
            "medir o resultado e ajustar conforme "
            "a necessidade."
        )

        return {
            "status": "executado",
            "acao": "criar_proposta",
            "resultado": {
                "receita": 0,
                "custo": 0,
                "proposta": proposta
            }
        }

    # =========================================================
    # CRIAR CONTEÚDO
    # =========================================================

    def criar_conteudo(self, decisao):

        conteudo = {
            "tema": decisao.get(
                "problema"
            ),
            "oferta": decisao.get(
                "oferta"
            ),
            "cliente_alvo": decisao.get(
                "cliente_alvo"
            ),
            "canal": decisao.get(
                "canal"
            )
        }

        return {
            "status": "executado",
            "acao": "criar_conteudo",
            "resultado": {
                "receita": 0,
                "custo": 0,
                "conteudo": conteudo
            }
        }

    # =========================================================
    # TESTAR ESTRATÉGIA
    # =========================================================

    def testar_estrategia(self, decisao):

        return {
            "status": "executado",
            "acao": "testar_estrategia",
            "resultado": {
                "receita": 0,
                "custo": 0,
                "estrategia": decisao.get(
                    "estrategia"
                ),
                "plano": {
                    "nicho": decisao.get(
                        "nicho"
                    ),
                    "cliente_alvo": decisao.get(
                        "cliente_alvo"
                    ),
                    "oferta": decisao.get(
                        "oferta"
                    ),
                    "canal": decisao.get(
                        "canal"
                    ),
                    "preco_teste": decisao.get(
                        "preco_teste"
                    )
                }
            }
        }
