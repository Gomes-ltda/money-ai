from Permissões import solicitar_permissao


class Executor:

    def executar(self, decisao):

        acao = decisao.get("acao")

        if not acao:
            return {
                "status": "erro",
                "motivo": "Nenhuma ação foi definida."
            }

        permissao = solicitar_permissao(acao)

        if not permissao["permitido"]:

            return {
                "status": "bloqueado",
                "acao": acao,
                "motivo": permissao["motivo"]
            }

        return self.executar_seguro(decisao)

    def executar_seguro(self, decisao):

        acao = decisao.get("acao")

        if acao == "aguardar":

            return {
                "status": "aguardando",
                "acao": acao
            }

        if acao == "pesquisar":

            return {
                "status": "executado",
                "acao": acao,
                "resultado": "Pesquisa autorizada."
            }

        if acao == "analisar":

            return {
                "status": "executado",
                "acao": acao,
                "resultado": "Análise autorizada."
            }

        if acao == "testar_estrategia":

            return self.testar_estrategia(decisao)

        return {
            "status": "bloqueado",
            "acao": acao,
            "motivo": "Executor ainda não possui essa ação."
        }

    def testar_estrategia(self, decisao):

        analise = decisao.get("analise", {})
        estrategia = decisao.get(
            "estrategia",
            analise.get(
                "estrategia",
                "Estratégia não especificada."
            )
        )

        return {
            "status": "executado",
            "acao": "testar_estrategia",
            "tipo": "teste_r0",
            "estrategia": estrategia,
            "custo_planejado": 0,
            "custo_real": 0,
            "receita": 0,
            "resultado": 0,
            "proximo_passo": (
                "Criar um plano de teste sem gasto, "
                "sem publicação externa e sem movimentação financeira."
            )
        }


def executar(decisao):

    executor = Executor()

    return executor.executar(decisao)
