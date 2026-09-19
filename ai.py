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

Sua tarefa é pesquisar informações atuais na internet
e encontrar oportunidades reais relacionadas ao objetivo.

Pesquise quando necessário para verificar:
- plataformas disponíveis atualmente;
- oportunidades reais;
- preços e custos atuais;
- requisitos;
- formas de monetização;
- mudanças recentes;
- riscos e limitações.

Não invente oportunidades, valores ou dados.

Para cada oportunidade relevante, informe:
1. O que é.
2. Como funciona.
3. Quanto pode custar para começar.
4. O que é necessário.
5. Como ganhar dinheiro com ela.
6. Dificuldade.
7. Possibilidade de automação.
8. Principais riscos.
9. Primeiros passos práticos.

Priorize oportunidades que possam ser testadas
com pouco dinheiro.

Não prometa ganhos garantidos.

Sempre diferencie fatos encontrados na pesquisa
de estimativas ou hipóteses.

Inclua as fontes utilizadas quando houver informações
importantes baseadas na internet.

Se não encontrar uma oportunidade confiável,
diga claramente que não encontrou.
"""

    for tentativa in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
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
