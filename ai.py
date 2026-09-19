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
                "erro":
                    f"TinyFish HTTP "
                    f"{resposta.status_code}: "
                    f"{resposta.text}"
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
            f"Título: {fonte.get('titulo')}\n"
            f"Site: {fonte.get('site')}\n"
            f"Resumo: {fonte.get('resumo')}\n"
            f"URL: {fonte.get('url')}\n\n"
        )

    return contexto


def analisar_oportunidade(objetivo, localizacao):

    consultas = [

        f"{objetivo} oportunidades em {localizacao}",

        f"freelancer diária trabalho temporário "
        f"vagas em {localizacao}",

        f"serviços autônomos renda extra "
        f"em {localizacao}",

        f"vagas freelancer trabalho rápido "
        f"{localizacao}",

        f"oportunidades de trabalho online "
        f"Brasil {objetivo}"

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
            "erro":
                "Não foi possível encontrar "
                "resultados na pesquisa.",
            "status": "erro"
        }

    fontes_unicas = []
    urls = set()

    for fonte in todas_as_fontes:

        url = fonte.get("url")

        if url and url not in urls:

            urls.add(url)
            fontes_unicas.append(fonte)

    fontes = fontes_unicas[:25]

    contexto_web = formatar_fontes(fontes)

    prompt = f"""
Você é a Money AI.

Sua função é encontrar oportunidades legítimas de geração
de renda e transformar pesquisas atuais da internet em
ações concretas que o usuário possa executar.

OBJETIVO DO USUÁRIO:

{objetivo}

LOCALIZAÇÃO DO USUÁRIO:

{localizacao}

RESULTADOS ENCONTRADOS NA INTERNET:

{contexto_web}

Analise cuidadosamente os resultados.

REGRAS IMPORTANTES:

1. Priorize oportunidades próximas da localização informada.

2. Também considere oportunidades totalmente online.

3. Não invente empresas, vagas, clientes, valores ou oportunidades.

4. Uma plataforma como Workana, Fiverr ou 99Freelas NÃO deve
ser apresentada como uma oportunidade concreta por si só.

5. Diferencie:
   - oportunidade concreta;
   - plataforma;
   - artigo ou conteúdo informativo;
   - estimativa.

6. Se houver uma vaga, projeto ou anúncio específico,
informe o link original.

7. Não diga que uma oportunidade está disponível agora
se a fonte não permitir confirmar isso.

8. Não prometa ganhos.

9. Não incentive golpes, fraude, spam, pirataria ou
qualquer atividade ilegal.

10. Nunca recomende pagar para conseguir uma vaga,
quando isso for suspeito.

11. Considere que o usuário está no Brasil.

12. Se não encontrar oportunidades concretas suficientes,
diga claramente que a pesquisa não encontrou evidências
suficientes.

ORGANIZE A RESPOSTA ASSIM:

OBJETIVO

Resuma o objetivo e a localização informados.

OPORTUNIDADES LOCAIS

Liste primeiro oportunidades concretas encontradas
na cidade ou região do usuário.

Para cada uma:

- Nome:
- Tipo:
- Local:
- Valor:
- O que fazer:
- Requisitos:
- Prazo:
- Pagamento:
- Link:
- Limitações:

OPORTUNIDADES ONLINE

Liste oportunidades concretas que podem ser realizadas
remotamente.

Use a mesma estrutura.

PLATAFORMAS

Se houver plataformas relevantes, coloque-as separadamente.
Não trate a existência da plataforma como garantia de trabalho.

O QUE FAZER AGORA

Escolha as oportunidades que parecem mais rápidas de testar
e explique os próximos passos.

PLANO DE TESTE

Crie um teste de baixo custo ou sem custo para o usuário
começar.

ALERTAS

Informe golpes, custos, requisitos, concorrência,
prazos de pagamento ou outras limitações relevantes.

FONTES

Liste os URLs utilizados.

Se não houver oportunidades concretas verificáveis,
não invente. Explique o que foi encontrado e por que
não é possível confirmar uma oportunidade específica.
"""

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
