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

    # --------------------------------------------------
    # 1. CARREGAR MEMÓRIA
    # --------------------------------------------------

    if contexto_memoria is None:

        try:
            contexto_memoria = (
                obter_ultimos_aprendizados(10)
            )

        except Exception:
            contexto_memoria = []

    # --------------------------------------------------
    # 2. PESQUISA
    # --------------------------------------------------

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
            "erro": (
                "Nenhuma informação encontrada."
            ),
            "status": "erro"
        }

    # --------------------------------------------------
    # 3. PREPARAR PESQUISA
    # --------------------------------------------------

    contexto = ""

    for i, fonte in enumerate(
        fontes[:40],
        1
    ):

        contexto += (
            f"FONTE {i}\n"
            f"Título: {fonte.get('titulo')}\n"
            f"Site: {fonte.get('site')}\n"
            f"Resumo: {fonte.get('resumo')}\n"
            f"URL: {fonte.get('url')}\n\n"
        )

    # --------------------------------------------------
    # 4. PREPARAR MEMÓRIA
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 5. PROMPT DO CÉREBRO
    # --------------------------------------------------

    prompt = f"""
Você é o Cérebro da Money AI.

Sua função é transformar pesquisa de mercado,
memória de experiências anteriores e resultados
em decisões operacionais.

A Money AI começa com R$0 de capital.

OBJETIVO:
{objetivo}

LOCALIZAÇÃO:
{localizacao}

MEMÓRIA:
{memoria_texto}

PESQUISA ATUAL:
{contexto}

REGRAS:

1. Não invente fatos, clientes, preços ou resultados.

2. Diferencie evidência, hipótese e decisão.

3. Use a memória para melhorar decisões futuras.

4. Não repita automaticamente estratégias que
apresentaram resultados ruins.

5. Se uma estratégia apresentou sinais positivos,
considere aprofundá-la.

6. R$0 de capital operacional.

7. Não recomende golpes, spam, fraude ou atividades ilegais.

8. Não prometa ganhos.

9. A Money AI deve agir como operadora de um negócio,
não apenas como consultora.

10. Escolha UMA oportunidade principal.

11. A oportunidade deve ser específica.

12. O objetivo é chegar à primeira receita real.

13. Priorize ações que possam ser realizadas sem
investimento inicial.

14. Ações externas envolvendo contas, mensagens,
publicações ou dinheiro devem respeitar permissões.

15. Se a próxima etapa puder ser realizada internamente,
ela pode ser executada sem pedir permissão.

16. Não considere uma oportunidade validada apenas
porque parece interessante.

17. Use evidências da pesquisa.

18. Se faltar informação, indique exatamente o que
precisa ser pesquisado.

19. Pense em sequência:
pesquisa → decisão → execução → medição → aprendizado.

20. O próximo passo deve aproximar a Money AI da
primeira receita.

RESPONDA SOMENTE COM JSON VÁLIDO.

ESTRUTURA:

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
        "acao_executor": "pesquisar|analisar|criar_oferta|criar_proposta|criar_conteudo|testar_estrategia|aguardar",
        "precisa_permissao": false,
        "motivo_escolha": "..."
    }},

    "proximo_passo": "...",

    "pesquisa_adicional_necessaria": [],

    "fontes_utilizadas": []
}}

IMPORTANTE:

- custo_teste deve ser número.
- Na fase R$0, custo_teste deve ser 0.
- acao_executor deve representar exatamente a ação
que o Executor deverá realizar.
- Se a ação for preparar uma oferta, use
"criar_oferta".
- Se for preparar uma proposta, use
"criar_proposta".
- Se for apenas pesquisar, use "pesquisar".
- Se for produzir conteúdo, use "criar_conteudo".
- Não coloque explicações fora do JSON.
"""

    # --------------------------------------------------
    # 6. CHAMADA AO CÉREBRO
    # --------------------------------------------------

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

            decisao = json.loads(
                texto
            )

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

    # --------------------------------------------------
    # 7. TRATAMENTO DE ERROS
    # --------------------------------------------------

    except Exception as erro:

        erro_texto = str(erro)

        if "429" in erro_texto:

            return {
                "objetivo": objetivo,
                "localizacao": localizacao,
                "erro": (
                    "Cota da Gemini excedida. "
                    "Nenhuma nova tentativa foi "
                    "realizada para evitar consumir "
                    "mais requisições."
                ),
                "detalhes": erro_texto,
                "status": "erro_cota"
            }

        if "503" in erro_texto:

            time.sleep(3)

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

                decisao = json.loads(
                    texto
                )

                decisao["fontes_brutas"] = fontes
                decisao["status"] = "sucesso"

                return decisao

            except Exception as segundo_erro:

                return {
                    "objetivo": objetivo,
                    "localizacao": localizacao,
                    "erro": str(
                        segundo_erro
                    ),
                    "status": "erro"
                }

        return {
            "objetivo": objetivo,
            "localizacao": localizacao,
            "erro": erro_texto,
            "status": "erro"
        }
