import json
import time

from google import genai
from pesquisa import pesquisar_varias
from memory import obter_ultimos_aprendizados


client = genai.Client()


def analisar_oportunidade(
    objetivo,
    localizacao,
    contexto_memoria=None
):

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

    # Memória anterior
    if contexto_memoria is None:
        try:
            contexto_memoria = obter_ultimos_aprendizados(10)
        except Exception:
            contexto_memoria = []

    memoria_texto = ""

    if contexto_memoria:

        for i, aprendizado in enumerate(
            contexto_memoria,
            1
        ):
            memoria_texto += (
                f"APRENDIZADO {i}\n"
                f"Estratégia: "
                f"{aprendizado.get('estrategia')}\n"
                f"Aprendizado: "
                f"{aprendizado.get('aprendizado')}\n"
                f"Evidências: "
                f"{aprendizado.get('evidencias')}\n"
                f"Impacto: "
                f"{aprendizado.get('impacto')}\n\n"
            )

    else:

        memoria_texto = (
            "Nenhum aprendizado anterior disponível."
        )

    prompt = f"""
Você é o Cérebro da Money AI.

Sua função é transformar pesquisa de mercado,
histórico de testes e resultados em decisões
operacionais para uma IA que precisa testar formas
legítimas de gerar receita.

A Money AI começa com R$0 de capital.

OBJETIVO:
{objetivo}

LOCALIZAÇÃO:
{localizacao}

MEMÓRIA DOS CICLOS ANTERIORES:
{memoria_texto}

PESQUISA REALIZADA AGORA:
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

11. USE A MEMÓRIA.

12. Não repita automaticamente uma estratégia
que já apresentou resultado ruim sem uma justificativa
baseada em novas evidências.

13. Se uma estratégia anterior apresentou sinais
positivos, considere aprofundá-la.

14. Se uma estratégia anterior não produziu receita,
isso NÃO significa automaticamente que ela é inútil.
Analise se o problema foi a estratégia, a oferta,
o público, o canal ou simplesmente a falta de execução.

15. Diferencie:
- estratégia testada
- estratégia ainda não testada
- estratégia que apresentou resultado positivo
- estratégia que apresentou resultado negativo
- estratégia que ainda precisa de evidência

16. O aprendizado deve influenciar a próxima decisão.

17. Se a pesquisa não possuir evidência suficiente,
declare isso e indique qual pesquisa adicional deve
ser feita antes de executar.

18. Nunca invente potenciais clientes.

19. Toda ação externa que envolva publicação,
mensagens, criação de contas ou dinheiro deve
respeitar as permissões.

20. Enquanto a Money AI estiver na fase R$0,
o custo do teste deve permanecer em 0.

21. O objetivo atual não é apenas pesquisar.
O objetivo é avançar progressivamente em direção
à primeira receita real.

22. Quando uma etapa preparatória estiver concluída,
identifique qual deve ser a próxima ação concreta.

RESPONDA EXATAMENTE EM JSON VÁLIDO.

Use esta estrutura:

{{
    "objetivo": "...",

    "aprendizado_utilizado": [
        "..."
    ],

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
- "aprendizado_utilizado" deve explicar quais
  aprendizados anteriores influenciaram a decisão.
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
                texto = texto.replace(
                    "```json",
                    ""
                )
                texto = texto.replace(
                    "```",
                    ""
                )
                texto = texto.strip()

            try:

                decisao = json.loads(texto)

            except json.JSONDecodeError:

                return {
                    "objetivo": objetivo,
                    "localizacao": localizacao,
                    "analise": response.text,
                    "fontes": fontes,
                    "erro": (
                        "A IA respondeu, mas não "
                        "retornou JSON válido."
                    ),
                    "status": "erro"
                }

            decisao["fontes_brutas"] = fontes
            decisao["status"] = "sucesso"

            return decisao

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
