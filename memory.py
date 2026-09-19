import json
import os
from datetime import datetime


ARQUIVO_MEMORIA = "memory.json"


def carregar_memoria():

    if not os.path.exists(ARQUIVO_MEMORIA):

        return {
            "eventos": [],
            "estrategias": [],
            "resultados": [],
            "financeiro": {
                "receita": 0,
                "custos": 0
            }
        }

    try:

        with open(
            ARQUIVO_MEMORIA,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)

    except Exception:

        return {
            "eventos": [],
            "estrategias": [],
            "resultados": [],
            "financeiro": {
                "receita": 0,
                "custos": 0
            }
        }


def salvar_memoria(memoria):

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
        "data": datetime.utcnow().isoformat(),
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
        "data": datetime.utcnow().isoformat(),
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
        "data": datetime.utcnow().isoformat(),
        "nome": nome,
        "descricao": descricao,
        "status": status
    }

    memoria["estrategias"].append(
        estrategia
    )

    salvar_memoria(memoria)


def obter_resumo():

    memoria = carregar_memoria()

    receita = memoria["financeiro"]["receita"]
    custos = memoria["financeiro"]["custos"]

    lucro = receita - custos

    return {
        "receita_total": receita,
        "custos_total": custos,
        "resultado_total": lucro,
        "eventos": len(memoria["eventos"]),
        "estrategias": len(memoria["estrategias"]),
        "resultados": len(memoria["resultados"])
    }
