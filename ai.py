from ai import analisar_oportunidade
from executor import executar
from memory import (
    registrar_ciclo,
    registrar_resultado,
    registrar_aprendizado
)


class MoneyAgent:

    def __init__(self):
        self.ciclo = 0

    def ciclo_agente(
        self,
        objetivo="Encontrar oportunidade de ganho de dinheiro online",
        localizacao="Brasil"
    ):

        self.ciclo += 1

        # 1. O Cérebro pesquisa e analisa
        analise = analisar_oportunidade(
            objetivo,
            localizacao
        )

        if analise.get("status") == "erro":

            ciclo = registrar_ciclo(
                objetivo=objetivo,
                localizacao=localizacao,
                pesquisa=analise,
                analise=analise,
                decisao=None,
                execucao=None,
                medicao={
                    "status": "erro",
                    "receita": 0,
                    "custo": 0,
                    "resultado": 0
                }
            )

            return {
                "status": "erro",
                "ciclo": self.ciclo,
                "erro": analise.get("erro"),
                "ciclo_memoria": ciclo
            }

        # 2. Extrai a decisão estruturada
        decisao_ia = analise.get("decisao", {})

        if not isinstance(decisao_ia, dict):
            decisao_ia = {}

        estrategia = decisao_ia.get("estrategia")
        nicho = decisao_ia.get("nicho")
        cliente_alvo = decisao_ia.get("cliente_alvo")
        problema = decisao_ia.get("problema")
        oferta = decisao_ia.get("oferta")
        canal = decisao_ia.get("canal")
        acao_imediata = decisao_ia.get("acao_imediata")
        precisa_permissao = decisao_ia.get(
            "precisa_permissao",
            False
        )

        # 3. Se não houver estratégia, não executa
        if not estrategia:

            decisao = {
                "acao": "aguardar",
                "motivo": (
                    "O Cérebro não informou "
                    "uma estratégia válida."
                ),
                "analise": analise
            }

            ciclo = registrar_ciclo(
                objetivo=objetivo,
                localizacao=localizacao,
                pesquisa=analise.get("fontes_brutas"),
                analise=analise,
                decisao=decisao,
                execucao=None,
                medicao={
                    "status": "sem_estrategia",
                    "receita": 0,
                    "custo": 0,
                    "resultado": 0
                }
            )

            return {
                "status": "aguardando",
                "ciclo": self.ciclo,
                "decisao": decisao,
                "ciclo_memoria": ciclo
            }

        # 4. Decide a próxima ação segura
        #
        # Se a próxima ação exigir permissão externa,
        # a Money AI não executa essa ação.
        #
        # Em vez disso, pesquisa mais informações
        # para preparar o próximo passo.

        if precisa_permissao:

            consulta = (
                f"{estrategia}. "
                f"Nicho: {nicho}. "
                f"Canal: {canal}. "
                f"Pesquisar oportunidades reais, "
                f"demanda atual, preços e potenciais "
                f"necessidades de clientes no Brasil. "
                f"Objetivo: preparar a oferta "
                f"sem criar contas, enviar mensagens "
                f"ou gastar dinheiro."
            )

            decisao = {
                "acao": "pesquisar",
                "estrategia": estrategia,
                "nicho": nicho,
                "cliente_alvo": cliente_alvo,
                "problema": problema,
                "oferta": oferta,
                "canal": canal,
                "acao_imediata": acao_imediata,
                "precisa_permissao": True,
                "consulta": consulta,
                "motivo": (
                    "A próxima ação externa exige "
                    "permissão. A Money AI realizará "
                    "primeiro uma etapa preparatória "
                    "sem custo."
                )
            }

        else:

            decisao = {
                "acao": "pesquisar",
                "estrategia": estrategia,
                "nicho": nicho,
                "cliente_alvo": cliente_alvo,
                "problema": problema,
                "oferta": oferta,
                "canal": canal,
                "acao_imediata": acao_imediata,
                "precisa_permissao": False,
                "consulta": (
                    f"{estrategia}. "
                    f"Pesquisar demanda, clientes, "
                    f"concorrência e preços atuais."
                )
            }

        # 5. Executa somente o que estiver autorizado
        execucao = executar(decisao)

        # 6. Mede o resultado financeiro
        receita = 0
        custo = 0

        if isinstance(execucao, dict):

            receita = execucao.get(
                "receita",
                0
            ) or 0

            custo = execucao.get(
                "custo",
                0
            ) or 0

        resultado_financeiro = receita - custo

        medicao = {
            "receita": receita,
            "custo": custo,
            "resultado": resultado_financeiro,
            "status": execucao.get(
                "status",
                "desconhecido"
            )
            if isinstance(execucao, dict)
            else "desconhecido"
        }

        # 7. Registra resultado
        registrar_resultado(
            estrategia=estrategia,
            receita=receita,
            custo=custo,
            resultado=resultado_financeiro
        )

        # 8. Registra aprendizado inicial
        if isinstance(execucao, dict):

            registrar_aprendizado(
                aprendizado=(
                    "A Money AI executou uma etapa "
                    "do teste da estratégia "
                    f"'{estrategia}'."
                ),
                estrategia=estrategia,
                evidencias=[
                    execucao
                ],
                impacto=(
                    "Resultado financeiro: "
                    f"R${resultado_financeiro:.2f}"
                )
            )

        # 9. Salva o ciclo completo
        ciclo = registrar_ciclo(
            objetivo=objetivo,
            localizacao=localizacao,
            pesquisa=analise.get(
                "fontes_brutas"
            ),
            analise=analise,
            decisao=decisao,
            execucao=execucao,
            medicao=medicao
        )

        return {
            "status": "sucesso",
            "ciclo": self.ciclo,
            "decisao_ia": analise,
            "decisao": decisao,
            "execucao": execucao,
            "medicao": medicao,
            "ciclo_memoria": ciclo
        }


def executar_ciclo(
    objetivo="Encontrar oportunidade de ganho de dinheiro online",
    localizacao="Brasil"
):
    agente = MoneyAgent()

    return agente.ciclo_agente(
        objetivo,
        localizacao
    )
