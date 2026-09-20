from ai import analisar_oportunidade
from executor import Executor

from memory import (
    registrar_ciclo,
    registrar_resultado,
    registrar_aprendizado,
    obter_ultimos_aprendizados
)


ACOES_PERMITIDAS = {
    "aguardar",
    "pesquisar",
    "analisar",
    "criar_oferta",
    "criar_proposta",
    "criar_conteudo",
    "testar_estrategia"
}


def executar_ciclo(objetivo, localizacao="Brasil"):
    memoria = obter_ultimos_aprendizados(10)

    # =========================================================
    # 1. CÉREBRO
    # =========================================================

    decisao_ia = analisar_oportunidade(
        objetivo,
        localizacao,
        contexto_memoria=memoria
    )

    # =========================================================
    # 2. ERROS DO CÉREBRO
    # =========================================================

    if decisao_ia.get("status") in {
        "erro_cota",
        "erro",
        "erro_configuracao"
    }:

        ciclo = registrar_ciclo(
            objetivo=objetivo,
            localizacao=localizacao,
            pesquisa=None,
            analise=decisao_ia,
            decisao={
                "acao": "aguardar",
                "motivo": (
                    "O Cérebro não está disponível no momento. "
                    "O ciclo será interrompido sem repetir ações."
                )
            },
            execucao={
                "acao": "aguardar",
                "status": "bloqueado"
            },
            medicao={
                "receita": 0,
                "custo": 0,
                "resultado": 0,
                "status": "aguardando_cerebro"
            }
        )

        return {
            "status": "aguardando_cerebro",
            "motivo": decisao_ia.get(
                "erro",
                "Cérebro indisponível."
            ),
            "decisao_ia": decisao_ia,
            "decisao": {
                "acao": "aguardar"
            },
            "execucao": {
                "acao": "aguardar",
                "status": "bloqueado"
            },
            "medicao": {
                "receita": 0,
                "custo": 0,
                "resultado": 0,
                "status": "aguardando_cerebro"
            },
            "ciclo_memoria": ciclo
        }

    # =========================================================
    # 3. EXTRAI DECISÃO DA IA
    # =========================================================

    decisao_ia_detalhes = decisao_ia.get("decisao", {})

    estrategia = decisao_ia_detalhes.get(
        "estrategia"
    )

    acao_executor = decisao_ia_detalhes.get(
        "acao_executor",
        decisao_ia.get("acao_executor")
    )

    precisa_permissao = decisao_ia_detalhes.get(
        "precisa_permissao",
        False
    )

    # =========================================================
    # 4. VALIDA AÇÃO
    # =========================================================

    if acao_executor not in ACOES_PERMITIDAS:

        acao_executor = "aguardar"

        motivo = (
            "A IA retornou uma ação inexistente ou não autorizada "
            "pela arquitetura atual."
        )

    else:
        motivo = (
            "Ação escolhida pelo Cérebro "
            "com base na análise e memória."
        )

    # =========================================================
    # 5. SE PRECISAR DE PERMISSÃO
    # =========================================================

    if precisa_permissao:

        decisao = {
            "acao": "aguardar",
            "acao_solicitada": acao_executor,
            "estrategia": estrategia,
            "precisa_permissao": True,
            "motivo": (
                "A próxima ação exige autorização do usuário."
            )
        }

    else:

        decisao = {
            "acao": acao_executor,
            "estrategia": estrategia,
            "nicho": decisao_ia_detalhes.get("nicho"),
            "cliente_alvo": decisao_ia_detalhes.get(
                "cliente_alvo"
            ),
            "problema": decisao_ia_detalhes.get(
                "problema"
            ),
            "oferta": decisao_ia_detalhes.get(
                "oferta"
            ),
            "canal": decisao_ia_detalhes.get(
                "canal"
            ),
            "preco_teste": decisao_ia_detalhes.get(
                "preco_teste"
            ),
            "custo_teste": decisao_ia_detalhes.get(
                "custo_teste"
            ),
            "acao_imediata": decisao_ia_detalhes.get(
                "acao_imediata"
            ),
            "precisa_permissao": False,
            "motivo": motivo
        }

    # =========================================================
    # 6. EXECUTOR
    # =========================================================

    executor = Executor()

    execucao = executor.executar(decisao)

    # =========================================================
    # 7. MEDIÇÃO
    # =========================================================

    resultado_execucao = execucao.get(
        "resultado",
        {}
    )

    receita = resultado_execucao.get(
        "receita",
        0
    )

    custo = resultado_execucao.get(
        "custo",
        0
    )

    resultado = receita - custo

    medicao = {
        "receita": receita,
        "custo": custo,
        "resultado": resultado,
        "status": execucao.get(
            "status",
            "executado"
        )
    }

    # =========================================================
    # 8. REGISTRA RESULTADO
    # =========================================================

    if estrategia:

        registrar_resultado(
            estrategia=estrategia,
            receita=receita,
            custo=custo,
            resultado=resultado
        )

    # =========================================================
    # 9. APRENDIZADO
    # =========================================================

    registrar_aprendizado(
        aprendizado=(
            f"A estratégia '{estrategia}' teve "
            f"a ação '{decisao.get('acao')}' executada. "
            f"Resultado financeiro: R${resultado:.2f}."
        ),
        estrategia=estrategia,
        evidencias=[
            execucao
        ],
        impacto=resultado
    )

    # =========================================================
    # 10. MEMÓRIA DO CICLO
    # =========================================================

    ciclo = registrar_ciclo(
        objetivo=objetivo,
        localizacao=localizacao,
        pesquisa=decisao_ia.get(
            "fontes_utilizadas"
        ),
        analise=decisao_ia,
        decisao=decisao,
        execucao=execucao,
        medicao=medicao
    )

    # =========================================================
    # 11. RETORNO
    # =========================================================

    return {
        "status": "sucesso",
        "objetivo": objetivo,
        "localizacao": localizacao,
        "memoria_utilizada": memoria,
        "decisao_ia": decisao_ia,
        "decisao": decisao,
        "execucao": execucao,
        "medicao": medicao,
        "ciclo_memoria": ciclo
    }
