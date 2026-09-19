import os
import requests


TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY")


def pesquisar(consulta, localizacao="BR"):

    if not TINYFISH_API_KEY:
        return {
            "erro": "TINYFISH_API_KEY não configurada."
        }

    params = {
        "query": consulta,
        "location": localizacao,
        "language": "pt",
        "domain_type": "web"
    }

    headers = {
        "X-API-Key": TINYFISH_API_KEY
    }

    try:

        resposta = requests.get(
            "https://api.search.tinyfish.ai",
            params=params,
            headers=headers,
            timeout=30
        )

        if resposta.status_code != 200:
            return {
                "erro": (
                    f"TinyFish HTTP "
                    f"{resposta.status_code}: "
                    f"{resposta.text}"
                )
            }

        dados = resposta.json()

        resultados = []

        for item in dados.get("results", [])[:10]:

            resultados.append({
                "titulo": item.get("title"),
                "site": item.get("site_name"),
                "resumo": item.get("snippet"),
                "url": item.get("url")
            })

        return {
            "consulta": consulta,
            "resultados": resultados
        }

    except Exception as erro:

        return {
            "erro": str(erro)
        }


def pesquisar_varias(consultas, localizacao="BR"):

    resultados = []

    for consulta in consultas:

        pesquisa = pesquisar(
            consulta,
            localizacao
        )

        if "resultados" in pesquisa:
            resultados.extend(
                pesquisa["resultados"]
            )

    return resultados
