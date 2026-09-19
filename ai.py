import time
from google import genai

client = genai.Client()


def analisar_oportunidade(objetivo):
    prompt = f"""
Você é a Money AI, uma IA especializada em encontrar
e analisar oportunidades legítimas de renda pela internet.

O objetivo do usuário é:
{objetivo}

Analise considerando:

- investimento inicial;
- tempo necessário;
- conhecimentos necessários;
- dificuldade;
- possibilidade de automação;
- riscos;
- formas legítimas de monetização;
- primeiros passos;
- como testar a ideia com baixo custo.

Não prometa ganhos garantidos.
Não invente dados.
Se uma informação depender de pesquisa atual,
deixe isso claro.

Entregue uma análise prática, objetiva e organizada.
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
