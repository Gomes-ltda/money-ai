from memory import (
    registrar_ciclo,
    registrar_resultado,
    registrar_aprendizado,
    obter_ultimos_aprendizados
)


class MoneyAgent:

    def __init__(
        self,
        objetivo="Encontrar oportunidade de ganho de dinheiro online",
        localizacao="Brasil"
    ):
        self.objetivo = objetivo
        self.localizacao = localizacao
        self.ciclo = 0

    def ciclo_agente(
        self,
        objetivo=None,
        localizacao=None
    ):

        from ai import analisar_oportunidade
        from executor import executar

        self.ciclo += 1

        objetivo = objetivo or self.objetivo
        localizacao = localizacao or self.localizacao

        # 1. Carrega aprendizados anteriores
        try:
            memoria = obter_ultimos_aprendizados(10)
        except Exception:
            memoria = []

        # 2. Cérebro pesquisa, analisa e considera memória
        analise = analisar_oportunidade(
            objetivo,
            localizacao,
            contexto_memoria=memoria
        )

        # 3. Verifica erro
        if analise.get("status") == "erro":

            medicao = {
                "status": "erro",
                "receita": 0,
                "custo": 0,
                "resultado": 0
            }

            ciclo = registrar_ciclo(
                objetivo=objetivo,
                localizacao=localizacao,
                pesquisa=analise,
                analise=analise,
                decisao=None,
                execucao=None,
                medicao=medicao
            )

            return {
                "status": "erro",
                "ciclo": self.ciclo,
                "erro": analise.get("erro"),
                "ciclo_memoria": ciclo
            }

        # 4. Extrai decisão estruturada
        decisao_ia = analise.get(
            "decisao",
            {}
        )

        if not isinstance(decisao_ia, dict):
            decisao_ia = {}

        estrategia = decisao_ia.get(
            "estrategia"
        )

        nicho = decisao_ia.get(
            "nicho"
        )

        cliente_alvo = decisao_ia.get(
            "cliente_alvo"
        )

        problema = decisao_ia.get(
            "problema"
        )

        oferta = decisao_ia.get(
            "oferta"
        )

        canal = decisao_ia.get(
            "canal"
        )

        acao_imediata = decisao_ia.get(
            "acao_imediata"
        )

        precisa_permissao = decisao_ia.get(
            "precisa_permissao",
            False
        )

        # 5. Sem estratégia válida
        if not estrategia:

            decisao = {
                "acao": "pesquisar",
                "motivo": (
                    "O Cérebro não informou uma "
                    "estratégia válida. Será feita "
                    "pesquisa adicional."
                ),
                "consulta": objetivo,
                "analise": analise
            }

        # 6. Próxima ação exige permissão
        elif precisa_permissao:

            consulta = (
                f"Pesquise oportunidades reais "
                f"relacionadas à estratégia: "
                f"{estrategia}. "
                f"Nicho: {nicho}. "
                f"Canal: {canal}. "
                f"Problema: {problema}. "
                f"Oferta: {oferta}. "
                f"Procure demanda atual, "
                f"concorrentes, preços e "
                f"oportunidades concretas no Brasil. "
                f"Não criar contas, não enviar "
                f"mensagens e não gastar dinheiro."
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
                    "permissão. A Money AI fará "
                    "primeiro uma etapa preparatória "
                    "sem custo."
                )
            }

        # 7. Ação segura
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
                    f"Pesquise demanda, clientes, "
                    f"concorrência e preços atuais."
                )
            }

        # 8. Executa
        execucao = executar(
            decisao
        )

        # 9. Mede resultado
        receita = 0
        custo = 0

        if isinstance(execucao, dict):

            receita = (
                execucao.get(
                    "receita",
                    0
                ) or 0
            )

            custo = (
                execucao.get(
                    "custo",
                    0
                ) or 0
            )

        resultado_financeiro = (
            receita - custo
        )

        medicao = {
            "receita": receita,
            "custo": custo,
            "resultado": resultado_financeiro,
            "status": (
                execucao.get(
                    "status",
                    "desconhecido"
                )
                if isinstance(
                    execucao,
                    dict
                )
                else "desconhecido"
            )
        }

        # 10. Registra resultado
        if estrategia:

            registrar_resultado(
                estrategia=estrategia,
                receita=receita,
                custo=custo,
                resultado=resultado_financeiro
            )

            registrar_aprendizado(
                aprendizado=(
                    "A Money AI executou uma "
                    "etapa do teste da estratégia "
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

        # 11. Salva ciclo completo
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
            "memoria_utilizada": memoria,
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

    agente = MoneyAgent(
        objetivo=objetivo,
        localizacao=localizacao
    )

    return agente.ciclo_agente()
