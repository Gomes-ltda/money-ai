import json
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

Sua função é transformar pesquisa de mercado em decisões
operacionais para uma IA que precisa testar formas legítimas
de gerar receita.

A Money AI começa com R$0 de capital.

OBJETIVO:
{objetivo}

LOCALIZAÇÃO:
{localizacao}

PESQUISA REALIZADA:
{contexto}

REGRAS:

1. Não invente fatos, clientes, preços ou resultados.

2. Diferencie claramente evidência encontrada,
hipótese e decisão da IA.

3. Não considere uma oportunidade validada apenas
porque parece interessante.

4. Procure oportunidades que possam ser testadas
com R$0 inicialmente.

5. Priorize ações que possam levar à primeira receita
sem exigir investimento inicial.

6. Não prometa ganhos.

7. Não recomende golpes, spam, fraude, práticas
enganosas ou atividades ilegais.

8. A Money AI deve agir como operadora de um negócio,
não apenas como consultora.

9. Escolha UMA oportunidade principal para o próximo teste.

10. A oportunidade escolhida deve ser específica.

11. Se a pesquisa não possuir evidência suficiente,
declare isso e indique qual pesquisa adicional deve
ser feita antes de executar.

12. Nunca invente potenciais clientes.

13. Toda ação externa que envolva publicação, mensagens,
criação de contas ou dinheiro deve respeitar as permissões.

RESPONDA EXATAMENTE EM JSON VÁLIDO.

Use esta estrutura:

{{
    "objetivo": "...",
    "oportunidades": [
        {{
            "nome": "...",
            "descricao": "...",
            "evidencias": [],
            "demanda": "...",
            "concorrencia": "...",
            "custos": "...",
            "riscos": "...",
            "modelo_receita": "...",
            "nivel_confianca": "baixo|medio|alto"
        }}
    ],
    "decisao": {{
        "estrategia": "...",
        "nicho": "...",
        "cliente_alvo": "...",
        "problema": "...",
        "oferta": "...",
        "canal": "...",
        "preco_teste": "...",
        "custo_teste": 0,
        "acao_imediata": "...",
        "precisa_permissao": false,
        "motivo_escolha": "..."
    }},
    "proximo_passo": "...",
    "pesquisa_adicional_necessaria": [],
    "fontes_utilizadas": []
}}

IMPORTANTE:

- "custo_teste" deve ser um número.
- Enquanto a Money AI estiver na fase R$0,
  "custo_teste" deve ser 0.
- "precisa_permissao" deve ser true se a próxima
  ação exigir publicação, envio de mensagens,
  criação de conta ou movimentação/gasto de dinheiro.
- "acao_imediata" deve ser uma ação concreta.
- Não coloque explicações fora do JSON.
"""

    for tentativa in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            texto = response.text.strip()

            if texto.startswith("```"):
                texto = texto.replace("```json", "")
                texto = texto.replace("```", "")
                texto = texto.strip()

            try:
                decisao = json.loads(texto)

            except json.JSONDecodeError:

                return {
                    "objetivo": objetivo,
                    "localizacao": localizacao,
                    "analise": response.text,
                    "fontes": fontes,
                    "erro": "A IA respondeu, mas não retornou JSON válido.",
                    "status": "erro"
                }

            decisao["fontes_brutas"] = fontes
            decisao["status"] = "sucesso"

            return decisao

        except Exception as erro:

            erro_texto = str(erro)

            if "503" in erro_texto and tentativa < 2:
                time.sleep(3)
                continue

            return {
                "objetivo": objetivo,
                "localizacao": localizacao,
                "erro": erro_texto,
                "status": "erro"
            }
