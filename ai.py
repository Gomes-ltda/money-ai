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
                "erro": f"TinyFish HTTP {resposta.status_code}: {resposta.text}"
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


def analisar_oportunidade(objetivo):

    consultas = [
        f"{objetivo} oportunidades trabalho renda freelancer Brasil",
        f"{objetivo} serviços freelas clientes Brasil",
        f"{objetivo} ganhar dinheiro online oportunidades atuais Brasil"
    ]

    todas_as_fontes = []

    for consulta in consultas:
        pesquisa = pesquisar_web(consulta)

        if "resultados" in pesquisa:
            todas_as_fontes.extend(pesquisa["resultados"])

    if not todas_as_fontes:
        return {
            "objetivo": objetivo,
            "erro": "Não foi possível encontrar resultados na pesquisa.",
            "status": "erro"
        }

    # Remove URLs duplicadas
    fontes_unicas = []
    urls = set()

    for fonte in todas_as_fontes:
        url = fonte.get("url")

        if url and url not in urls:
            urls.add(url)
            fontes_unicas.append(fonte)

    fontes = fontes_unicas[:20]

    contexto_web = formatar_fontes(fontes)

    prompt = f"""
Você é a Money AI.

Sua função é encontrar oportunidades legítimas de geração de renda
e transformar pesquisas na internet em ações concretas que o usuário
possa executar.

OBJETIVO DO USUÁRIO:

{objetivo}

RESULTADOS ENCONTRADOS NA INTERNET:

{contexto_web}

Analise cuidadosamente os resultados.

IMPORTANTE:

1. Não invente oportunidades, empresas, valores, clientes ou vagas.

2. Não trate uma informação encontrada no snippet como fato confirmado
se a fonte não fornecer evidência suficiente.

3. Sempre mantenha o URL original quando uma oportunidade concreta
possuir um link.

4. Diferencie claramente:
   - oportunidade encontrada;
   - informação confirmada;
   - estimativa;
   - recomendação de ação.

5. Não prometa ganhos.

6. Não incentive golpes, spam, fraude, manipulação, pirataria,
falsificação, lavagem de dinheiro ou qualquer atividade ilegal.

7. Não recomende pagar para conseguir trabalho quando isso for
suspeito ou incompatível com a oportunidade.

8. Se o objetivo tiver prazo curto, priorize oportunidades que possam
ser executadas rapidamente.

9. Se uma oportunidade exigir cadastro, entrevista, aprovação,
portfólio ou espera para saque, informe isso claramente.

10. Considere que o usuário está no Brasil.

Agora produza uma resposta prática.

Use esta estrutura:

OBJETIVO
Explique brevemente o que o usuário quer alcançar.

OPORTUNIDADES ENCONTRADAS
Liste as oportunidades concretas encontradas nas fontes.

Para cada oportunidade informe:

- Nome:
- Tipo:
- Onde foi encontrada:
- Valor ou faixa de valor, se houver:
- O que precisa fazer:
- Requisitos:
- Tempo estimado para começar:
- Forma de pagamento, se disponível:
- Link:
- Nível de dificuldade:
- Principais riscos ou limitações:

OPORTUNIDADES QUE PODEM SER EXECUTADAS AGORA
Selecione somente as oportunidades que, de acordo com as fontes,
parecem poder ser iniciadas imediatamente.

PRÓXIMA AÇÃO
Explique exatamente o que o usuário deveria fazer primeiro para testar
a oportunidade.

PLANO DE TESTE
Crie um pequeno teste de baixo custo ou sem custo para validar a ideia.

ALERTAS
Liste possíveis golpes, custos escondidos, requisitos, prazos de saque
ou outras limitações relevantes.

FONTES
Liste as fontes utilizadas com seus URLs.

Se não houver oportunidades concretas suficientes, diga isso claramente
em vez de inventar.
"""

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
