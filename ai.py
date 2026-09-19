import os
import time

from google import genai
from pesquisa import pesquisar_varias


client = genai.Client()


def analisar_oportunidade(objetivo, localizacao):

    consultas = [
        objetivo,
        f"mercado e oportunidades {objetivo}",
        f"negocios e servicos {localizacao}",
        f"clientes e demanda {localizacao}",
        f"tendencias de mercado Brasil {objetivo}",
        f"ideias de negocios {objetivo}",
    ]

    fontes = pesquisar_varias(
        consultas,
        localizacao
    )

    if not fontes:

        return {
            "objetivo": objetivo,
            "localizacao": localizacao,
            "erro": "Nenhuma informação encontrada.",
            "status": "erro"
        }

    contexto = ""

    for i, fonte in enumerate(fontes[:40], 1):

        contexto += (
            f"FONTE {i}\n"
            f"Título: {fonte.get('titulo')}\n"
            f"Site: {fonte.get('site')}\n"
            f"Resumo: {fonte.get('resumo')}\n"
            f"URL: {fonte.get('url')}\n\n"
        )

    prompt = f"""
Você é o Cérebro da Money AI.

Seu trabalho é analisar informações reais coletadas
pela camada de Pesquisa e transformar essas informações
em decisões econômicas.

OBJETIVO ATUAL:
{objetivo}

LOCALIZAÇÃO:
{localizacao}

INFORMAÇÕES COLETADAS:
{contexto}

REGRAS:

1. Não invente informações.

2. Diferencie fatos encontrados nas fontes de hipóteses
ou ideias criadas pela própria IA.

3. Procure oportunidades econômicas reais.

4. Analise demanda, concorrência, custos, riscos,
possível receita e dificuldade de execução.

5. Pense como uma empresa que precisa gerar receita,
e não como um consultor dando dicas ao usuário.

6. Uma ideia não deve ser tratada como negócio validado
sem evidências.

7. Se uma estratégia parecer ruim, descarte-a.

8. Se uma estratégia parecer promissora, explique por quê
e indique como ela poderia ser testada.

9. Não prometa ganhos.

10. Não recomende atividades ilegais, golpes, spam,
fraudes ou práticas enganosas.

RESPONDA COM:

OBJETIVO

OPORTUNIDADES IDENTIFICADAS

Para cada oportunidade:
- O que é
- Evidências
- Demanda
- Concorrência
- Custos
- Riscos
- Como testar
- Possível modelo de receita

ESTRATÉGIAS PARA TESTAR

Liste estratégias que a Money AI poderia testar
posteriormente.

PRÓXIMA AÇÃO

Indique qual deveria ser a próxima ação da Money AI
com base nas informações disponíveis.

FONTES

Liste as fontes utilizadas.
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
