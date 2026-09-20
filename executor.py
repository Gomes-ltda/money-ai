import re

from Permissões import solicitar_permissao
from pesquisa import pesquisar


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

        return {
            "status": "bloqueado",
            "acao": acao,
            "motivo": (
                "Executor ainda não possui "
                "essa ação."
            )
        }

    # --------------------------------------------------
    # PESQUISA
    # --------------------------------------------------

    def executar_pesquisa(self, decisao):

        consulta = (
            decisao.get("consulta")
            or decisao.get("objetivo")
            or decisao.get("estrategia")
        )

        if not consulta:
            return {
                "status": "erro",
                "acao": "pesquisar",
                "motivo": (
                    "Nenhuma consulta foi definida."
                )
            }

        try:

            resultado = pesquisar(consulta)

            return {
                "status": "executado",
                "acao": "pesquisar",
                "consulta": consulta,
                "resultado": resultado
            }

        except Exception as erro:

            return {
                "status": "erro",
                "acao": "pesquisar",
                "consulta": consulta,
                "motivo": str(erro)
            }

    # --------------------------------------------------
    # ANÁLISE
    # --------------------------------------------------

    def executar_analise(self, decisao):

        dados = decisao.get("dados")

        if not dados:
            dados = decisao.get("pesquisa")

        if not dados:
            return {
                "status": "erro",
                "acao": "analisar",
                "motivo": (
                    "Nenhum dado foi fornecido "
                    "para análise."
                )
            }

        return {
            "status": "executado",
            "acao": "analisar",
            "resultado": (
                "Dados preparados para análise "
                "pelo Cérebro."
            ),
            "dados": dados
        }

    # --------------------------------------------------
    # CRIAÇÃO DE OFERTA
    # --------------------------------------------------

    def criar_oferta(self, decisao):

        estrategia = decisao.get(
            "estrategia",
            ""
        )

        nicho = decisao.get(
            "nicho",
            ""
        )

        problema = decisao.get(
            "problema",
            ""
        )

        cliente = decisao.get(
            "cliente_alvo",
            ""
        )

        oferta = decisao.get(
            "oferta",
            ""
        )

        preco = decisao.get(
            "preco_teste",
            ""
        )

        if not oferta:

            return {
                "status": "erro",
                "acao": "criar_oferta",
                "motivo": (
                    "Nenhuma descrição de oferta "
                    "foi fornecida."
                )
            }

        proposta = {
            "nome": (
                "Oferta de teste - "
                f"{estrategia}"
            ),
            "cliente_alvo": cliente,
            "nicho": nicho,
            "problema": problema,
            "servico": oferta,
            "preco_teste": preco,
            "custo_teste": 0,
            "objetivo": (
                "Validar interesse real "
                "sem investimento inicial."
            )
        }

        return {
            "status": "executado",
            "acao": "criar_oferta",
            "resultado": proposta,
            "custo": 0,
            "receita": 0
        }

    # --------------------------------------------------
    # CRIAÇÃO DE PROPOSTA
    # --------------------------------------------------

    def criar_proposta(self, decisao):

        cliente = decisao.get(
            "cliente_alvo",
            ""
        )

        problema = decisao.get(
            "problema",
            ""
        )

        oferta = decisao.get(
            "oferta",
            ""
        )

        preco = decisao.get(
            "preco_teste",
            ""
        )

        canal = decisao.get(
            "canal",
            ""
        )

        if not oferta:

            return {
                "status": "erro",
                "acao": "criar_proposta",
                "motivo": (
                    "Oferta não definida."
                )
            }

        texto = (
            "PROPOSTA COMERCIAL\n\n"
            f"Cliente-alvo: {cliente}\n\n"
            f"Problema identificado: {problema}\n\n"
            f"Serviço oferecido: {oferta}\n\n"
            f"Canal previsto: {canal}\n\n"
            f"Preço inicial de teste: {preco}\n\n"
            "Objetivo: realizar um teste inicial "
            "com baixo risco e sem investimento "
            "financeiro da Money AI.\n"
        )

        return {
            "status": "executado",
            "acao": "criar_proposta",
            "resultado": {
                "texto": texto,
                "cliente_alvo": cliente,
                "oferta": oferta,
                "preco": preco
            },
            "custo": 0,
            "receita": 0
        }

    # --------------------------------------------------
    # CRIAÇÃO DE CONTEÚDO
    # --------------------------------------------------

    def criar_conteudo(self, decisao):

        tema = (
            decisao.get("tema")
            or decisao.get("oferta")
            or decisao.get("estrategia")
        )

        if not tema:

            return {
                "status": "erro",
                "acao": "criar_conteudo",
                "motivo": (
                    "Nenhum tema foi definido."
                )
            }

        return {
            "status": "executado",
            "acao": "criar_conteudo",
            "resultado": {
                "tema": tema,
                "status": (
                    "Conteúdo preparado "
                    "para revisão."
                )
            },
            "custo": 0,
            "receita": 0
        }

    # --------------------------------------------------
    # TESTE DE ESTRATÉGIA
    # --------------------------------------------------

    def testar_estrategia(self, decisao):

        analise = decisao.get(
            "analise",
            {}
        )

        estrategia = decisao.get(
            "estrategia"
        )

        if not estrategia and isinstance(
            analise,
            dict
        ):
            estrategia = analise.get(
                "estrategia"
            )

        texto_analise = ""

        if isinstance(
            analise,
            dict
        ):
            texto_analise = analise.get(
                "analise",
                ""
            )

        elif isinstance(
            analise,
            str
        ):
            texto_analise = analise

        if not estrategia and texto_analise:

            estrategia = self.extrair_estrategia(
                texto_analise
            )

        if not estrategia:

            return {
                "status": "erro",
                "acao": "testar_estrategia",
                "motivo": (
                    "Não foi possível identificar "
                    "a estratégia escolhida pelo "
                    "Cérebro."
                )
            }

        plano = self.criar_plano_teste(
            estrategia,
            texto_analise
        )

        pesquisa_consulta = (
            self.criar_consulta_pesquisa(
                estrategia,
                plano
            )
        )

        pesquisa_resultado = (
            self.executar_pesquisa({
                "consulta":
                    pesquisa_consulta
            })
        )

        return {
            "status": "executado",
            "acao": "testar_estrategia",
            "tipo": "teste_r0",
            "estrategia": estrategia,
            "hipotese": plano["hipotese"],
            "objetivo_teste": (
                plano["objetivo_teste"]
            ),
            "acoes_planejadas": (
                plano["acoes_planejadas"]
            ),
            "pesquisa": {
                "consulta":
                    pesquisa_consulta,
                "resultado":
                    pesquisa_resultado
            },
            "metricas": plano["metricas"],
            "restricoes": {
                "custo_maximo": 0,
                "publicacao_externa": False,
                "envio_de_mensagens": False,
                "movimentacao_financeira": False,
                "criacao_de_contas": False
            },
            "custo_planejado": 0,
            "custo_real": 0,
            "receita": 0,
            "resultado": 0,
            "proximo_passo": (
                "Analisar os resultados da pesquisa "
                "e preparar uma oferta R$0."
            )
        }

    # --------------------------------------------------
    # AUXILIARES
    # --------------------------------------------------

    def criar_consulta_pesquisa(
        self,
        estrategia,
        plano
    ):

        return (
            "Pesquise oportunidades reais de "
            "geração de receita para a seguinte "
            f"estratégia: {estrategia}. "
            f"Objetivo: {plano['objetivo_teste']}. "
            "Identifique demanda, potenciais "
            "clientes, problemas existentes, "
            "concorrentes, preços praticados "
            "e formas de testar a oferta sem "
            "investimento inicial."
        )

    def extrair_estrategia(self, texto):

        padroes = [
            r"Oportunidade\s*1\s*:\s*(.+)",
            r"Oportunidade\s+1\s*[-–—]\s*(.+)",
            r"Estratégia\s*:\s*(.+)"
        ]

        for padrao in padroes:

            resultado = re.search(
                padrao,
                texto,
                re.IGNORECASE
            )

            if resultado:

                estrategia = (
                    resultado.group(1)
                    .strip()
                )

                estrategia = (
                    estrategia
                    .split("\n")[0]
                    .strip()
                )

                if len(estrategia) > 200:
                    estrategia = (
                        estrategia[:200]
                        .strip()
                    )

                return estrategia.rstrip(".")

        return None

    def criar_plano_teste(
        self,
        estrategia,
        texto_analise
    ):

        estrategia_lower = (
            estrategia.lower()
        )

        if (
            "automação" in estrategia_lower
            or "automacao" in estrategia_lower
            or "ia" in estrategia_lower
        ):

            hipotese = (
                "Pequenas empresas podem ter "
                "problemas operacionais que "
                "podem ser resolvidos com "
                "automação ou ferramentas de IA."
            )

            objetivo = (
                "Validar se existe demanda concreta "
                "por uma solução simples de automação "
                "ou IA sem gastar dinheiro."
            )

            acoes = [
                "Definir uma oferta mínima e específica.",
                "Definir o tipo de pequeno negócio a ser testado.",
                "Pesquisar problemas reais desse público.",
                "Identificar potenciais clientes.",
                "Pesquisar concorrentes e preços.",
                "Preparar uma proposta de solução.",
                "Registrar os resultados."
            ]

        elif (
            "freelance" in estrategia_lower
            or "freela" in estrategia_lower
            or "serviço" in estrategia_lower
            or "servico" in estrategia_lower
            or "suporte" in estrategia_lower
            or "atendimento" in estrategia_lower
        ):

            hipotese = (
                "Existe demanda por serviços "
                "operacionais específicos que "
                "podem ser oferecidos sem "
                "investimento inicial."
            )

            objetivo = (
                "Identificar um serviço específico "
                "que possa ser validado sem custo."
            )

            acoes = [
                "Definir um serviço específico.",
                "Definir o público que pode precisar dele.",
                "Pesquisar demanda.",
                "Pesquisar concorrentes.",
                "Pesquisar preços.",
                "Definir uma oferta inicial.",
                "Preparar uma proposta.",
                "Registrar os resultados."
            ]

        else:

            hipotese = (
                "A estratégia identificada pode "
                "possuir uma oportunidade de geração "
                "de receita sem investimento inicial."
            )

            objetivo = (
                "Validar a estratégia utilizando "
                "pesquisa, análise e preparação, "
                "sem gastos."
            )

            acoes = [
                "Definir a oferta.",
                "Definir o público-alvo.",
                "Pesquisar demanda.",
                "Pesquisar concorrentes.",
                "Criar uma proposta inicial.",
                "Registrar os resultados."
            ]

        metricas = [
            "Quantidade de potenciais clientes identificados",
            "Quantidade de sinais de demanda encontrados",
            "Quantidade de concorrentes encontrados",
            "Faixa de preços identificada",
            "Quantidade de ofertas preparadas",
            "Custo do teste",
            "Receita gerada",
            "Resultado financeiro"
        ]

        return {
            "hipotese": hipotese,
            "objetivo_teste": objetivo,
            "acoes_planejadas": acoes,
            "metricas": metricas
        }


def executar(decisao):

    executor = Executor()

    return executor.executar(
        decisao
    )
