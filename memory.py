import json
import os
from datetime import datetime, timezone

try:
    import psycopg
except ImportError:
    psycopg = None


ARQUIVO_MEMORIA = "memory.json"
DATABASE_URL = os.getenv("DATABASE_URL")


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

    memoria["financeiro"].setdefault("receita", 0)
    memoria["financeiro"].setdefault("custos", 0)

    return memoria


def agora():
    return datetime.now(timezone.utc).isoformat()


def _usar_banco():
    return bool(DATABASE_URL and psycopg)


def _conectar():
    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10
    )


def _inicializar_banco():
    if not _usar_banco():
        return False

    try:
        with _conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS evolia_memory (
                        id INTEGER PRIMARY KEY,
                        data JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
        return True
    except Exception:
        return False


def _carregar_banco():
    if not _inicializar_banco():
        return None

    try:
        with _conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    "SELECT data FROM evolia_memory WHERE id = 1"
                )
                linha = cursor.fetchone()

        if linha:
            return garantir_estrutura(linha[0])

        # Migra a memória JSON existente apenas na primeira inicialização.
        if os.path.exists(ARQUIVO_MEMORIA):
            try:
                with open(
                    ARQUIVO_MEMORIA,
                    "r",
                    encoding="utf-8"
                ) as arquivo:
                    memoria = garantir_estrutura(json.load(arquivo))
            except Exception:
                memoria = memoria_padrao()
        else:
            memoria = memoria_padrao()

        _salvar_banco(memoria)
        return memoria

    except Exception:
        return None


def _salvar_banco(memoria):
    if not _inicializar_banco():
        return False

    try:
        memoria = garantir_estrutura(memoria)

        with _conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO evolia_memory (id, data, updated_at)
                    VALUES (1, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        data = EXCLUDED.data,
                        updated_at = NOW()
                    """,
                    (json.dumps(memoria, ensure_ascii=False),)
                )
        return True
    except Exception:
        return False


def carregar_memoria():
    memoria_banco = _carregar_banco()

    if memoria_banco is not None:
        return memoria_banco

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

        return garantir_estrutura(memoria)

    except Exception:
        return memoria_padrao()


def salvar_memoria(memoria):
    memoria = garantir_estrutura(memoria)

    if _usar_banco() and _salvar_banco(memoria):
        return

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


# =========================================================
# EVENTOS
# =========================================================

def registrar_evento(tipo, descricao):
    memoria = carregar_memoria()

    evento = {
        "data": agora(),
        "tipo": tipo,
        "descricao": descricao
    }

    memoria["eventos"].append(evento)
    salvar_memoria(memoria)

    return evento


# =========================================================
# RESULTADOS FINANCEIROS
# =========================================================

def registrar_resultado(
    estrategia,
    receita=0,
    custo=0,
    resultado=None,
    acao=None,
    evidencias=None
):
    memoria = carregar_memoria()

    if resultado is None:
        resultado = receita - custo

    registro = {
        "data": agora(),
        "estrategia": estrategia,
        "acao": acao,
        "receita": receita,
        "custo": custo,
        "resultado": resultado,
        "evidencias": evidencias or []
    }

    memoria["resultados"].append(registro)
    memoria["financeiro"]["receita"] += receita
    memoria["financeiro"]["custos"] += custo

    salvar_memoria(memoria)

    return registro


# =========================================================
# ESTRATÉGIAS
# =========================================================

def registrar_estrategia(nome, descricao, status="em_teste"):
    memoria = carregar_memoria()

    estrategia = {
        "data": agora(),
        "nome": nome,
        "descricao": descricao,
        "status": status
    }

    memoria["estrategias"].append(estrategia)
    salvar_memoria(memoria)

    return estrategia


# =========================================================
# CICLOS
# =========================================================

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


# =========================================================
# TESTES
# =========================================================

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


# =========================================================
# APRENDIZADO
# =========================================================

def registrar_aprendizado(
    aprendizado,
    estrategia=None,
    evidencias=None,
    impacto=None,
    acao=None,
    confianca=None,
    recomendacao=None
):
    memoria = carregar_memoria()

    registro = {
        "data": agora(),
        "aprendizado": aprendizado,
        "estrategia": estrategia,
        "acao": acao,
        "evidencias": evidencias or [],
        "impacto": impacto,
        "confianca": confianca,
        "recomendacao": recomendacao
    }

    memoria["aprendizados"].append(registro)
    salvar_memoria(memoria)

    return registro


# =========================================================
# HISTÓRICO DE UMA ESTRATÉGIA
# =========================================================

def obter_historico_estrategia(estrategia):
    memoria = carregar_memoria()

    resultados = [
        registro
        for registro in memoria["resultados"]
        if registro.get("estrategia") == estrategia
    ]

    testes = [
        teste
        for teste in memoria["testes"]
        if teste.get("estrategia") == estrategia
    ]

    aprendizados = [
        aprendizado
        for aprendizado in memoria["aprendizados"]
        if aprendizado.get("estrategia") == estrategia
    ]

    return {
        "estrategia": estrategia,
        "resultados": resultados,
        "testes": testes,
        "aprendizados": aprendizados
    }


# =========================================================
# ÚLTIMOS APRENDIZADOS
# =========================================================

def obter_ultimos_aprendizados(limite=10):
    memoria = carregar_memoria()
    return memoria["aprendizados"][-limite:]


# =========================================================
# RESUMO FINANCEIRO
# =========================================================

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
        "resultados": len(memoria["resultados"]),
        "ciclos": len(memoria["ciclos"]),
        "testes": len(memoria["testes"]),
        "aprendizados": len(memoria["aprendizados"])
    }
