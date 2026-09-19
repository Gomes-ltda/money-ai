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

        f'"{objetivo}" {localizacao} trabalho',

        f'bico diária freelancer {localizacao}',

        f'trabalho temporário pagamento diária {localizacao}',

        f'serviço autônomo renda extra {localizacao}',

        f'contratação imediata trabalho {localizacao}',

        f'freelancer pagamento rápido {localizacao}',

        f'oportunidades renda extra online Brasil {objetivo}',

        f'freelancer remoto pagamento Brasil {objetivo}',

        f'serviços que posso oferecer hoje {localizacao}',

        f'anúncios contratando serviços {localizacao}'

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

    fontes = fontes_unicas[:40]

    contexto_web = formatar_fontes(fontes)

    prompt = f"""
Você é a Money AI, um agente especializado em encontrar
formas legítimas de gerar renda.

Sua função NÃO é simplesmente listar sites de empregos.

Sua função é analisar informações atuais da internet,
identificar oportunidades concretas e transformar essas
informações em ações que o usuário possa executar.

OBJETIVO DO USUÁRIO:

{objetivo}

LOCALIZAÇÃO:

{localizacao}

RESULTADOS ATUAIS DA INTERNET:

{contexto_web}


========================
REGRAS DE ANÁLISE
========================

1. Priorize oportunidades que possam realmente ajudar o
usuário a atingir o objetivo informado.

2. Dê prioridade para oportunidades:
- locais;
- de contratação rápida;
- de curto prazo;
- freelancer;
- bicos;
- diárias;
- serviços;
- trabalhos que possam começar rapidamente;
- oportunidades online que não dependam de localização.

3. Se o usuário informou uma meta de dinheiro e prazo,
avalie se a oportunidade tem potencial de contribuir
para essa meta.

4. NÃO invente:
- vagas;
- clientes;
- empresas;
- valores;
- contatos;
- prazos;
- disponibilidade;
- requisitos.

5. Não trate uma plataforma como Workana, Fiverr,
99Freelas, OLX, Indeed etc. como se ela própria fosse
uma oportunidade concreta.

6. Diferencie claramente:
- OPORTUNIDADE CONCRETA
- PLATAFORMA
- FONTE INFORMATIVA
- IDEIA DE SERVIÇO
- ESTIMATIVA

7. Uma oportunidade só deve ser chamada de "concreta"
quando existir evidência suficiente na fonte apresentada.

8. Se a fonte mostrar uma vaga, anúncio, projeto ou pedido
específico, use o link original.

9. Não diga que uma vaga ainda está disponível se isso
não puder ser confirmado.

10. Não prometa ganhos.

11. Não recomende fraude, spam, pirataria, golpes,
manipulação, atividades ilegais ou qualquer método
que dependa de enganar outra pessoa.

12. Não recomende pagar para conseguir uma vaga quando
isso for suspeito.

13. Considere que o usuário está no Brasil.

14. Se não houver oportunidades concretas suficientes,
seja transparente.

15. Não transforme qualquer resultado de pesquisa em
uma oportunidade apenas para preencher a resposta.

16. Prefira poucas oportunidades relevantes a uma lista
grande de resultados ruins.

17. Quando uma oportunidade exigir contato com alguém,
explique exatamente quem deve ser contatado e por qual
meio, desde que essa informação esteja disponível na fonte.

18. Quando não houver oportunidade concreta, procure
também identificar serviços que o usuário poderia oferecer
na própria região, mas deixe claro que isso é uma estratégia
de prospecção e não um cliente já encontrado.

19. Considere o esforço necessário, velocidade para começar,
possível retorno, custos e riscos.

20. Nunca
