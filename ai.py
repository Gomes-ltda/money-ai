import os

def analisar_oportunidade(objetivo):
    """
    Recebe o objetivo do usuário e prepara a solicitação
    que futuramente será enviada ao modelo de IA.
    """

    prompt = f"""
Você é a Money AI, uma IA especializada em encontrar
e analisar oportunidades legítimas de renda pela internet.

Objetivo do usuário:
{objetivo}

Analise o objetivo considerando:
- investimento inicial;
- tempo disponível;
- conhecimentos necessários;
- dificuldade;
- possibilidade de automação;
- riscos;
- como começar;
- como testar a ideia com baixo custo.

Não prometa ganhos garantidos.
Priorize oportunidades legítimas e legais.

Retorne uma análise prática e objetiva.
"""

    return {
        "objetivo": objetivo,
        "prompt": prompt,
        "status": "pronto_para_IA"
    }
