import json
import os
from datetime import datetime, timezone


ARQUIVO_MEMORIA = "memory.json"


def memoria_padrao():

    return {
        "eventos": [],
        "estrategias": [],
        "resultados": [],
        "ciclos": [],
        "testes": [],
        "aprendizados": [],
        "financeiro": {
            "receita": 0,
            "custos": 0
        }
    }


def garantir_estrutura(memoria):

    padrao = memoria_padrao()

    if not isinstance(memoria, dict):
        memoria = padrao

    for chave, valor in padrao.items():

        if chave not in memoria:

            memoria[chave] = valor

    if not isinstance(memoria.get("financeiro"), dict):

        memoria["financeiro"] = {
            "receita": 0,
            "custos": 0
        }

    memoria["financeiro"].setdefault(
        "receita",
        0
    )

    memoria["financeiro"].setdefault(
        "custos",
        0
    )

    return memoria


def agora():

    return datetime.now(
        timezone.utc
    ).isoformat()


def carregar_memoria():

    if not os.path.exists(ARQUIVO_MEMORIA):

        memoria = memoria_padrao()

        salvar_memoria(memoria)

        return memoria

    try:

        with open(
            ARQUIVO_MEMORIA,
            "r",
            encoding="utf-8"
        ) as arquivo:

            memoria = json.load(arquivo)

        memoria = garantir_estrutura(memoria)

        salvar_memoria(memoria)

        return memoria

    except Exception:

        return memoria_padrao()


def salvar_memoria(memoria):

    memoria = garantir_estrutura(memoria)

    with open(
        ARQUIVO_MEMORIA,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            memoria,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def registrar_evento(tipo, descricao):

    memoria = carregar_memoria()

    evento = {
        "data": agora(),
        "tipo": tipo,
        "descricao": descricao
    }

    memoria["eventos"].append(evento)

    salvar_memoria(memoria)


def registrar_resultado(
    estrategia,
    receita=0,
    custo=0,
    resultado=None
):

    memoria = carregar_memoria()

    if resultado is None:

        resultado = receita - custo

    registro = {
        "data": agora(),
        "estrategia": estrategia,
        "receita": receita,
        "custo": custo,
        "resultado": resultado
    }

    memoria["resultados"].append(registro)

    memoria["financeiro"]["receita"] += receita
    memoria["financeiro"]["custos"] += custo

    salvar_memoria(memoria)


def registrar_estrategia(
    nome,
    descricao,
    status="em_teste"
):

    memoria = carregar_memoria()

    estrategia = {
        "data": agora(),
        "nome": nome,
        "descricao": descricao,
        "status": status
    }

    memoria["estrategias"].append(
        estrategia
    )

    salvar_memoria(memoria)


def registrar_ciclo(
    objetivo,
    localizacao=None,
    pesquisa=None,
    analise=None,
    decisao=None,
    execucao=None,
    medicao=None
):

    memoria = carregar_memoria()

    ciclo = {
        "data": agora(),
        "objetivo": objetivo,
        "localizacao": localizacao,
        "pesquisa": pesquisa,
        "analise": analise,
        "decisao": decisao,
        "execucao": execucao,
        "medicao": medicao
    }

    memoria["ciclos"].append(ciclo)

    salvar_memoria(memoria)

    return ciclo


def registrar_teste(
    estrategia,
    plano=None,
    restricoes=None,
    execucao=None,
    receita=0,
    custo=0,
    resultado=None,
    status="em_andamento",
    ciclo=None
):

    memoria = carregar_memoria()

    if resultado is None:

        resultado = receita - custo

    teste = {
        "data": agora(),
        "ciclo": ciclo,
        "estrategia": estrategia,
        "plano": plano or {},
        "restricoes": restricoes or {},
        "execucao": execucao or {},
        "financeiro": {
            "receita": receita,
            "custo": custo,
            "resultado": resultado
        },
        "status": status
    }

    memoria["testes"].append(teste)

    salvar_memoria(memoria)

    return teste


def registrar_aprendizado(
    aprendizado,
    estrategia=None,
    evidencias=None,
    impacto=None
):

    memoria = carregar_memoria()

    registro = {
        "data": agora(),
        "aprendizado": aprendizado,
        "estrategia": estrategia,
        "evidencias": evidencias or [],
        "impacto": impacto
    }

    memoria["aprendizados"].append(
        registro
    )

    salvar_memoria(memoria)

    return registro


def obter_historico_estrategia(
    estrategia
):

    memoria = carregar_memoria()

    resultados = []

    for registro in memoria["resultados"]:

        if registro.get(
            "estrategia"
        ) == estrategia:

            resultados.append(
                registro
            )

    testes = []

    for teste in memoria["testes"]:

        if teste.get(
            "estrategia"
        ) == estrategia:

            testes.append(
                teste
            )

    aprendizados = []

    for aprendizado in memoria["aprendizados"]:

        if aprendizado.get(
            "estrategia"
        ) == estrategia:

            aprendizados.append(
                aprendizado
            )

    return {
        "estrategia": estrategia,
        "resultados": resultados,
        "testes": testes,
        "aprendizados": aprendizados
    }


def obter_ultimos_aprendizados(
    limite=10
):

    memoria = carregar_memoria()

    aprendizados = memoria[
        "aprendizados"
    ]

    return aprendizados[-limite:]


def obter_resumo():

    memoria = carregar_memoria()

    receita = memoria[
        "financeiro"
    ]["receita"]

    custos = memoria[
        "financeiro"
    ]["custos"]

    lucro = receita - custos

    return {
        "receita_total": receita,
        "custos_total": custos,
        "resultado_total": lucro,
        "eventos": len(
            memoria["eventos"]
        ),
        "estrategias": len(
            memoria["estrategias"]
        ),
        "resultados": len(
            memoria["resultados"]
        ),
        "ciclos": len(
            memoria["ciclos"]
        ),
        "testes": len(
            memoria["testes"]
        ),
        "aprendizados": len(
            memoria["aprendizados"]
        )
    }
