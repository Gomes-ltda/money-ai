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

        return {
            "status": "bloqueado",
            "acao": acao,
            "motivo": "Executor ainda não possui essa ação."
        }
