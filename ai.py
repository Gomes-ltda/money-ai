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
        contexto_web += (
            f"Fonte {i}\n"
            f"Título: {fonte.get('titulo')}\n"
            f"Site: {fonte.get('site')}\n"
            f"Resumo: {fonte.get('resumo')}\n"
            f"URL: {fonte.get('url')}\n\n"
        )

    prompt = (
        "Você é a Money AI, uma IA especializada em encontrar "
        "e analisar oportunidades legítimas de renda pela internet.\n\n"
        f"Objetivo do usuário:\n{objetivo}\n\n"
        f"Informações encontradas na internet:\n{contexto_web}\n\n"
        "Produza uma análise prática considerando:\n"
        "- investimento inicial;\n"
        "- tempo necessário;\n"
        "- conhecimentos necessários;\n"
        "- dificuldade;\n"
        "- possibilidade de automação;\n"
        "- riscos;\n"
        "- formas legítimas de monetização;\n"
        "- primeiros passos;\n"
        "- como testar a ideia com baixo custo.\n\n"
        "Não prometa ganhos garantidos.\n"
        "Não invente dados.\n"
        "Diferencie informações encontradas de estimativas.\n"
        "Se as fontes forem insuficientes, deixe isso claro.\n\n"
        "Entregue uma resposta objetiva e organizada."
    )

    for tentativa in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            return {
                "objetivo": objetivo,
                "analise": response.text,
                "fontes": fontes,
                "status": "sucesso"
            }

        except Exception as erro:
            erro_texto = str(erro)

            if "503" in erro_texto and tentativa < 2:
                time.sleep(3)
                continue

            return {
                "objetivo": objetivo,
                "erro": erro_texto,
                "status": "erro"
            }
