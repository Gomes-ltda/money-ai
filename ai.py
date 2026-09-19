import os
import time
import requests
from google import genai

client = genai.Client()

TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY")


def pesquisar_web(consulta):

    if not TINYFISH_API_KEY:
        return {
            "erro": "TINYFISH_API_KEY não configurada."
        }

    params = {
        "query": consulta,
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
            "resultados": resultados
        }

    except Exception as erro:

        return {
            "erro": str(erro)
        }


def formatar_fontes(fontes):

    contexto = ""

    for i, fonte in enumerate(fontes, 1):

        contexto += (
            f"FONTE {i}\n"
            f"Titulo: {fonte.get('titulo')}\n"
            f"Site: {fonte.get('site')}\n"
            f"Resumo: {fonte.get('resumo')}\n"
            f"URL: {fonte.get('url')}\n\n"
        )

    return contexto


def analisar_oportunidade(objetivo, localizacao):

    consultas = [
        f"{objetivo} {localizacao} trabalho",
        f"bico diaria freelancer {localizacao}",
        f"trabalho temporario pagamento diaria {localizacao}",
        f"servico autonomo renda extra {localizacao}",
        f"contratacao imediata trabalho {localizacao}",
        f"freelancer pagamento rapido {localizacao}",
        f"oportunidades renda extra online Brasil {objetivo}",
        f"freelancer remoto pagamento Brasil {objetivo}",
        f"servicos que posso oferecer hoje {localizacao}",
        f"anuncios contratando servicos {localizacao}"
    ]

    todas_as_fontes = []

    for consulta in consultas:

        pesquisa = pesquisar_web(consulta)

        if "resultados" in pesquisa:
            todas_as_fontes.extend(
                pesquisa["resultados"]
            )

    if not todas_as_fontes:

        return {
            "objetivo": objetivo,
            "localizacao": localizacao,
            "erro": (
                "Nao foi possivel encontrar "
                "resultados na pesquisa."
            ),
            "status": "erro"
        }

    fontes_unicas = []
    urls = set()

    for fonte in todas_as_fontes:

        url = fonte.get("url")

        if url and url not in urls:

            urls.add(url)
            fontes_unicas.append(fonte)

    fontes = fontes_unicas[:40]

    contexto_web = formatar_fontes(fontes)

    prompt_partes = [

        "Voce e a Money AI.",
        "",
        "Sua funcao e encontrar formas legitimas de gerar renda.",
        "",
        "Voce nao deve simplesmente listar sites de empregos.",
        "Deve analisar informacoes atuais da internet, "
        "identificar oportunidades concretas e transformar "
        "essas informacoes em acoes praticas.",
        "",
        "OBJETIVO DO USUARIO:",
        objetivo,
        "",
        "LOCALIZACAO:",
        localizacao,
        "",
        "RESULTADOS ATUAIS DA INTERNET:",
        contexto_web,
        "",
        "REGRAS DE ANALISE:",
        "",
        "1. Priorize oportunidades que possam realmente "
        "ajudar o usuario a atingir o objetivo.",
        "",
        "2. Priorize oportunidades locais, bicos, diarias, "
        "freelancer, servicos, trabalhos temporarios e "
        "oportunidades online.",
        "",
        "3. Se houver valor ou prazo informado pelo usuario, "
        "considere isso na analise.",
        "",
        "4. Nunca invente vagas, clientes, empresas, valores, "
        "contatos, prazos ou disponibilidade.",
        "",
        "5. Plataformas como Workana, Fiverr, 99Freelas, "
        "OLX e Indeed nao sao oportunidades concretas "
        "por si mesmas.",
        "",
        "6. Classifique resultados como:",
        "A - Oportunidade concreta",
        "B - Possivel oportunidade",
        "C - Plataforma",
        "D - Informacao",
        "E - Ideia de servico",
        "",
        "7. So chame algo de oportunidade concreta quando "
        "houver evidencia suficiente na fonte.",
        "",
        "8. Se houver vaga, anuncio ou projeto especifico, "
        "use o link original.",
        "",
        "9. Nao diga que algo esta disponivel agora se isso "
        "nao puder ser confirmado.",
        "",
        "10. Nao prometa ganhos.",
        "",
        "11. Nao recomende fraude, spam, pirataria, golpes "
        "ou atividades ilegais.",
        "",
        "12. Nao recomende pagar para conseguir uma vaga "
        "quando isso for suspeito.",
        "",
        "13. Prefira poucas oportunidades relevantes a uma "
        "lista grande de resultados ruins.",
        "",
        "14. Se nao houver oportunidades concretas, "
        "seja transparente.",
        "",
        "15. Quando nao houver oportunidade concreta, "
        "identifique estrategias de prospeccao que o "
        "usuario possa executar.",
        "",
        "16. Considere esforco, velocidade para comecar, "
        "custos, possivel retorno e riscos.",
        "",
        "FORMATO DA RESPOSTA:",
        "",
        "OBJETIVO",
        "Resuma objetivo, localizacao, prazo e valor desejado.",
        "",
        "OPORTUNIDADES CONCRETAS",
        "Mostre primeiro as oportunidades com evidencia concreta.",
        "",
        "Para cada uma informe:",
        "- Nome",
        "- Tipo",
        "- Classificacao",
        "- Local",
        "- Valor",
        "- O que fazer",
        "- Requisitos",
        "- Prazo",
        "- Pagamento",
        "- Como entrar",
        "- Link",
        "- Por que pode servir",
        "- Limitacoes",
        "",
        "POSSIVEIS OPORTUNIDADES",
        "Mostre oportunidades interessantes que ainda precisam "
        "ser confirmadas.",
        "",
        "OPORTUNIDADES ONLINE",
        "Mostre oportunidades remotas concretas ou possiveis.",
        "",
        "ESTRATEGIAS DE PROSPECCAO",
        "Se faltarem oportunidades concretas, apresente "
        "formas praticas de procurar clientes ou servicos "
        "na regiao do usuario.",
        "",
        "O QUE FAZER AGORA",
        "Crie uma sequencia pratica de acoes.",
        "",
        "PLANO DE EXECUCAO",
        "Crie um plano para as proximas horas.",
        "",
        "MENSAGEM PRONTA",
        "Se for necessario entrar em contato com clientes "
        "ou contratantes, crie uma mensagem curta que "
        "o usuario possa copiar e enviar.",
        "",
        "Nao invente informacoes pessoais do usuario.",
        "",
        "ALERTAS",
        "Informe custos, golpes, concorrencia, requisitos, "
        "deslocamento, prazo de pagamento e riscos.",
        "",
        "FONTES",
        "Liste os links das fontes utilizadas.",
        "",
        "REGRA FINAL:",
        "E melhor dizer que nao foi encontrada uma oportunidade "
        "concreta verificavel do que inventar uma."
    ]

    prompt = "\n".join(prompt_partes)

    for tentativa in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            return {
                "objetivo": objetivo,
                "localizacao": localizacao,
                "analise": response.text,
                "fontes": fontes,
                "status": "sucesso"
            }

        except Exception as erro:

            erro_texto = str(erro)

            if (
                "503" in erro_texto
                and tentativa < 2
            ):
                time.sleep(3)
                continue

            return {
                "objetivo": objetivo,
                "localizacao": localizacao,
                "erro": erro_texto,
                "status": "erro"
            }
