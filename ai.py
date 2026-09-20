import json
import os
import time

from google import genai

from pesquisa import pesquisar_varias
from memory import obter_ultimos_aprendizados


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

MODELO = "gemini-3.6-flash"


def analisar_oportunidade(
    objetivo,
    localizacao="Brasil",
    contexto_memoria=None
):

    if not GEMINI_API_KEY:
        return {
            "status": "erro_configuracao",
            "erro": "GEMINI_API_KEY não configurada.",
            "objetivo": objetivo,
            "localizacao": localizacao
        }

    # =========================================================
    # 1. MEMÓRIA
    # =========================================================

    if contexto_memoria is None:
        contexto_memoria = obter_ultimos_aprendizados(
            10
        )

    # =========================================================
    # 2. PESQUISA
    # =========================================================

    consultas = [
        objetivo,
        f"mercado e oportunidades {objetivo}",
        f"clientes e demanda {objetivo}",
        f"serviços com demanda {localizacao}",
        f"tendências de mercado Brasil {objetivo}",
        f"formas legítimas de monetizar {objetivo}"
    ]

    pesquisa = pesquisar_varias(
        consultas,
        localizacao
    )

    fontes = pesquisa[:40]

    # =========================================================
    # 3. CONTEXTO DA MEMÓRIA
    # =========================================================

    memoria_texto = json.dumps(
        contexto_memoria,
        ensure_ascii=False,
        indent=2
    )

    fontes_texto = json.dumps(
        fontes,
        ensure_ascii=False,
        indent=2
    )

    # =========================================================
    # 4. PROMPT DO CÉREBRO
    # =========================================================

    prompt = f"""
Você é o Cérebro da Money AI.

A Money AI é um agente criado para encontrar,
testar e desenvolver formas legítimas de gerar
receita online.

OBJETIVO ATUAL:
{objetivo}

LOCALIZAÇÃO:
{localizacao}

MEMÓRIA DE APRENDIZADOS ANTERIORES:
{memoria_texto}

PESQUISA ATUAL:
{fontes_texto}

Sua função NÃO é simplesmente listar ideias.

Você deve:

1. analisar as oportunidades encontradas;
2. considerar o que a Money AI já aprendeu;
3. evitar repetir estratégias que apresentaram
   resultados ruins sem uma justificativa;
4. preservar e aprofundar estratégias que
   apresentaram sinais positivos;
5. identificar oportunidades que possam ser
   testadas com custo zero ou muito baixo;
6. escolher uma estratégia concreta;
7. definir uma oferta concreta;
8. identificar o cliente-alvo;
9. escolher um canal;
10. definir a próxima ação executável;
11. decidir qual ação o Executor deve realizar;
12. registrar o que deverá ser aprendido com o teste.

REGRA IMPORTANTE:

A Money AI possui R$0 de capital inicial.

Portanto, priorize estratégias que possam começar
sem investimento financeiro.

A Money AI não deve:

- movimentar dinheiro sem autorização;
- criar contas sem autorização;
- realizar compromissos legais;
- enviar mensagens externas sem autorização;
- publicar externamente sem autorização;
- inventar resultados;
- considerar receita inexistente como receita real.

AÇÕES DISPONÍVEIS AO EXECUTOR:

- aguardar
- pesquisar
- analisar
- criar_oferta
- criar_proposta
- criar_conteudo
- testar_estrategia

ESCOLHA EXATAMENTE UMA.

A ação deve representar a PRÓXIMA etapa lógica
do processo.

Se ainda faltar informação:
"pesquisar"

Se a oportunidade estiver suficientemente
entendida, mas ainda precisar ser estruturada:
"analisar"

Se for hora de montar uma oferta:
"criar_oferta"

Se for hora de preparar uma proposta comercial:
"criar_proposta"

Se for hora de produzir material:
"criar_conteudo"

Se já existir uma estratégia pronta para teste:
"testar_estrategia"

Se nenhuma ação segura fizer sentido:
"aguardar"

Não escolha uma ação apenas para gerar atividade.
A ação deve aproximar a Money AI da geração
real de receita.

RETORNE SOMENTE JSON VÁLIDO.

FORMATO:

{{
    "objetivo": "...",

    "aprendizado_utilizado": [
        "..."
    ],

    "oportunidades": [
        {{
            "nome": "...",
            "descricao": "...",
            "potencial": "...",
            "custo_inicial": 0
        }}
    ],

    "decisao": {{
        "estrategia": "...",
        "nicho": "...",
        "cliente_alvo": "...",
        "problema": "...",
        "oferta": "...",
        "canal": "...",
        "preco_teste": 0,
        "custo_teste": 0,
        "acao_imediata": "...",
        "acao_executor": "...",
        "precisa_permissao": false,
        "motivo_escolha": "..."
    }},

    "aprendizado_esperado": "...",

    "proximo_passo": "...",

    "pesquisa_adicional_necessaria": true,

    "fontes_utilizadas": []
}}
"""

    # =========================================================
    # 5. CHAMADA GEMINI
    # =========================================================

    try:

        cliente = genai.Client(
            api_key=GEMINI_API_KEY
        )

        resposta = cliente.models.generate_content(
            model=MODELO,
            contents=prompt
        )

        texto = resposta.text.strip()

        # Remove possíveis blocos Markdown
        if texto.startswith("```"):
            texto = texto.replace(
                "```json",
                ""
            ).replace(
                "```",
                ""
            ).strip()

        dados = json.loads(
            texto
        )

        return {
            "status": "sucesso",
            "objetivo": objetivo,
            "localizacao": localizacao,
            "decisao": dados.get(
                "decisao",
                {}
            ),
            "oportunidades": dados.get(
                "oportunidades",
                []
            ),
            "aprendizado_utilizado": dados.get(
                "aprendizado_utilizado",
                []
            ),
            "aprendizado_esperado": dados.get(
                "aprendizado_esperado"
            ),
            "proximo_passo": dados.get(
                "proximo_passo"
            ),
            "pesquisa_adicional_necessaria": dados.get(
                "pesquisa_adicional_necessaria",
                False
            ),
            "fontes_utilizadas": dados.get(
                "fontes_utilizadas",
                []
            )
        }

    except Exception as erro:

        mensagem = str(erro)

        if (
            "429" in mensagem
            or "RESOURCE_EXHAUSTED" in mensagem
            or "quota" in mensagem.lower()
        ):

            return {
                "status": "erro_cota",
                "erro": (
                    "Cota da Gemini excedida. "
                    "Nenhuma nova tentativa foi realizada "
                    "para evitar consumir mais requisições."
                ),
                "detalhes": mensagem,
                "objetivo": objetivo,
                "localizacao": localizacao
            }

        # Uma única tentativa adicional apenas
        # para erros temporários de servidor.
        if (
            "503" in mensagem
            or "UNAVAILABLE" in mensagem
        ):

            try:

                time.sleep(2)

                resposta = cliente.models.generate_content(
                    model=MODELO,
                    contents=prompt
                )

                texto = resposta.text.strip()

                if texto.startswith("```"):
                    texto = texto.replace(
                        "```json",
                        ""
                    ).replace(
                        "```",
                        ""
                    ).strip()

                dados = json.loads(
                    texto
                )

                return {
                    "status": "sucesso",
                    "objetivo": objetivo,
                    "localizacao": localizacao,
                    "decisao": dados.get(
                        "decisao",
                        {}
                    ),
                    "oportunidades": dados.get(
                        "oportunidades",
                        []
                    ),
                    "aprendizado_utilizado": dados.get(
                        "aprendizado_utilizado",
                        []
                    ),
                    "aprendizado_esperado": dados.get(
                        "aprendizado_esperado"
                    ),
                    "proximo_passo": dados.get(
                        "proximo_passo"
                    ),
                    "pesquisa_adicional_necessaria": dados.get(
                        "pesquisa_adicional_necessaria",
                        False
                    ),
                    "fontes_utilizadas": dados.get(
                        "fontes_utilizadas",
                        []
                    )
                }

            except Exception as segundo_erro:

                return {
                    "status": "erro",
                    "erro": str(
                        segundo_erro
                    ),
                    "objetivo": objetivo,
                    "localizacao": localizacao
                }

        return {
            "status": "erro",
            "erro": mensagem,
            "objetivo": objetivo,
            "localizacao": localizacao
        }
