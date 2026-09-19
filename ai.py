import time
from google import genai
from google.genai import types

client = genai.Client()

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)


def analisar_oportunidade(objetivo):
    prompt = f"""
Você é a Money AI, uma IA especializada em encontrar
e analisar oportunidades legítimas de renda pela internet.

OBJETIVO DO USUÁRIO:
{objetivo}

Pesquise na internet informações atuais relacionadas ao objetivo.

Verifique, quando necessário:
- plataformas disponíveis atualmente;
- oportunidades reais;
- preços e custos;
- requisitos;
- formas de monetização;
- mudanças recentes;
- riscos e limitações.

Para cada oportunidade relevante, informe:
1. O que é.
2. Como funciona.
3. Custo inicial.
4. Requisitos.
5. Como ganhar dinheiro.
6. Dificuldade.
7. Possibilidade de automação.
8. Riscos.
9. Primeiros passos.

Priorize oportunidades que possam ser testadas com pouco dinheiro.

Não prometa ganhos garantidos.
Não invente dados.
Diferencie fatos encontrados na pesquisa de estimativas.

Inclua as fontes utilizadas quando houver informações
importantes baseadas na internet.
"""

    for tentativa in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config=config
            )

            return {
                "objetivo": objetivo,
                "analise": response.text,
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
