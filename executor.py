import re

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

        estrategia = decisao.get("estrategia")

        if not estrategia and isinstance(analise, dict):

            estrategia = analise.get("estrategia")

        texto_analise = ""

        if isinstance(analise, dict):

            texto_analise = analise.get(
                "analise",
                ""
            )

        elif isinstance(analise, str):

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
                    "a estratégia escolhida pelo Cérebro."
                )
            }

        plano = self.criar_plano_teste(
            estrategia,
            texto_analise
        )

        return {
            "status": "executado",
            "acao": "testar_estrategia",
            "tipo": "teste_r0",

            "estrategia": estrategia,

            "hipotese": plano["hipotese"],

            "objetivo_teste": plano[
                "objetivo_teste"
            ],

            "acoes_planejadas": plano[
                "acoes_planejadas"
            ],

            "metricas": plano[
                "metricas"
            ],

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
                "Executar as etapas permitidas "
                "do teste R$0 e medir os resultados."
            )
        }

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

                estrategia = resultado.group(1).strip()

                estrategia = estrategia.split(
                    "\n"
                )[0].strip()

                estrategia = estrategia.rstrip(
                    "."
                )

                if len(estrategia) > 200:

                    estrategia = estrategia[:200].strip()

                return estrategia

        return None

    def criar_plano_teste(
        self,
        estrategia,
        texto_analise
    ):

        estrategia_lower = estrategia.lower()

        if (
            "automação" in estrategia_lower
            or "automacao" in estrategia_lower
            or "ia" in estrategia_lower
        ):

            hipotese = (
                "Pequenas empresas podem ter problemas "
                "operacionais que podem ser resolvidos "
                "com automação ou ferramentas de IA."
            )

            objetivo = (
                "Validar se existe uma demanda concreta "
                "por uma solução simples de automação "
                "ou IA sem gastar dinheiro."
            )

            acoes = [
                "Definir uma oferta mínima e específica.",
                "Definir o tipo de pequeno negócio a ser testado.",
                "Identificar problemas que podem ser automatizados.",
                "Pesquisar potenciais clientes e sinais de demanda.",
                "Preparar uma proposta de solução.",
                "Registrar os resultados do teste."
            ]

        elif (
            "freelance" in estrategia_lower
            or "freela" in estrategia_lower
            or "serviço" in estrategia_lower
            or "servico" in estrategia_lower
        ):

            hipotese = (
                "Existe demanda por serviços digitais "
                "específicos que podem ser oferecidos "
                "sem investimento inicial."
            )

            objetivo = (
                "Identificar um serviço simples que possa "
                "ser validado sem custo."
            )

            acoes = [
                "Definir um serviço específico.",
                "Definir o público que pode precisar dele.",
                "Pesquisar demanda e concorrentes.",
                "Definir uma oferta inicial.",
                "Preparar uma demonstração ou exemplo.",
                "Registrar os resultados do teste."
            ]

        else:

            hipotese = (
                "A estratégia identificada pode possuir "
                "uma oportunidade de geração de receita "
                "sem investimento inicial."
            )

            objetivo = (
                "Validar a estratégia utilizando somente "
                "pesquisa, análise e preparação, sem gastos."
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

    return executor.executar(decisao)
