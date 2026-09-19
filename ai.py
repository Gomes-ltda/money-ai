import os
import time
import requests
from google import genai

client = genai.Client()

TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY")


def pesquisar_web(objetivo):
    if not TINYFISH_API_KEY:
        return {
            "erro": "TINYFISH_API_KEY não configurada."
        }

    params = {
        "query": objetivo,
        "location": "BR",
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
                "erro": f"TinyFish HTTP {resposta.status_code}: {resposta.text}"
            }

        dados = resposta.json()

        resultados = []

        for item in dados.get("results", [])[:8]:
            resultados.append({
                "titulo": item.get("title"),
                "site": item.get("site_name"),
                "resumo": item.get("snippet"),
                "url": item.get("url")
            })

        return {
            "resultados": resultados
        }

    except Exception as erro:
        return {
            "erro": str(erro)
        }


def analisar_oportunidade(objetivo):

    pesquisa = pesquisar_web(
        f"{objetivo} oportunidades legítimas atuais Brasil"
    )

    if "erro" in pesquisa:
        return {
            "objetivo": objetivo,
            "erro": pesquisa["erro"],
            "status": "erro"
        }

    fontes = pesquisa.get("resultados", [])

    contexto_web = ""

    for i, fonte in enumerate(fontes, 1):
        contexto_web += f"""
Fonte {i}
Título: {fonte.get('titulo')}
Site: {fonte.get('site')}
Resumo: {fonte.get('resumo')}
URL: {fonte.get('url')}
"""

    prompt = f"""
