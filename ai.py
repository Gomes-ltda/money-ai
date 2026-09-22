import json
import os
import time
import requests

from google import genai
from google.genai import types

from pesquisa import pesquisar_varias
from memory import obter_ultimos_aprendizados, obter_contexto_estrategico, avaliar_estrategias, obter_metricas_comerciais, obter_ultimo_ciclo, obter_estado_comercial


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").strip().lower()

MODELOS = [modelo.strip() for modelo in os.getenv("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.7-flash,gemini-3.6-flash,gemini-3.5-flash-lite").split(",") if modelo.strip()]


def _extrair_json(texto):
    texto = (texto or "").strip()
    if texto.startswith("```"):
        texto = texto.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fim = texto.rfind("}")
        if inicio >= 0 and fim > inicio:
            return json.loads(texto[inicio:fim + 1])
        raise


def _gerar_json(cliente, prompt):
    ultimo_erro = None
    for modelo in MODELOS:
        try:
            resposta = cliente.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            dados = _extrair_json(resposta.text)
            return dados, modelo, None
        except Exception as erro:
            mensagem = str(erro)
            ultimo_erro = mensagem
            if ("429" in mensagem or "RESOURCE_EXHAUSTED" in mensagem or
                    "503" in mensagem or "UNAVAILABLE" in mensagem or
                    "high demand" in mensagem.lower()):
                continue
            continue
    return None, None, ultimo_erro

def _gerar_openai(prompt):
    if not OPENAI_API_KEY:
        return None, None, None
    try:
        resposta = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": OPENAI_MODEL, "input": prompt},
            timeout=90
        )
        resposta.raise_for_status()
        bruto = resposta.json()
        texto = bruto.get("output_text", "")
        if not texto:
            partes = []
            for item in bruto.get("output", []):
                for conteudo in item.get("content", []):
                    if conteudo.get("type") in {"output_text", "text"}:
                        partes.append(conteudo.get("text", ""))
            texto = "".join(partes)
        texto = texto.strip()
        if texto.startswith("```"):
            texto = texto.replace("```json", "").replace("```", "").strip()
        return _extrair_json(texto), OPENAI_MODEL, None
    except Exception as erro:
        return None, OPENAI_MODEL, str(erro)

def analisar_oportunidade(
    objetivo,
    localizacao="Brasil",
    contexto_memoria=None
):

    provider = AI_PROVIDER if AI_PROVIDER in {"auto", "gemini", "openai"} else "auto"

    if provider == "gemini" and not GEMINI_API_KEY:
        return {"status": "erro_configuracao", "erro": "AI_PROVIDER=gemini, mas GEMINI_API_KEY não está configurada.", "objetivo": objetivo, "localizacao": localizacao}

    if provider == "openai" and not OPENAI_API_KEY:
        return {"status": "erro_configuracao", "erro": "AI_PROVIDER=openai, mas OPENAI_API_KEY não está configurada.", "objetivo": objetivo, "localizacao": localizacao}

    if provider == "auto" and not GEMINI_API_KEY and not OPENAI_API_KEY:
        return {
            "status": "erro_configuracao",
            "erro": "Nenhum provedor de IA configurado. Configure GEMINI_API_KEY ou OPENAI_API_KEY.",
            "objetivo": objetivo,
            "localizacao": localizacao
        }

    # =========================================================
    # 1. MEMÓRIA
    # =========================================================

    if contexto_memoria is None:
        contexto_memoria = obter_ultimos_aprendizados(10)

    contexto_estrategico = obter_contexto_estrategico()
    avaliacao_estrategias = avaliar_estrategias()
    metricas_comerciais = obter_metricas_comerciais()
    ciclo_anterior = obter_ultimo_ciclo()
    estado_comercial = obter_estado_comercial()

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

    ciclo_anterior_texto = json.dumps(
        ciclo_anterior or {},
        ensure_ascii=False,
        indent=2
    )

    # =========================================================
    # 4. PROMPT DO CÉREBRO
    # =========================================================

    prompt = f"""
Você é o Cérebro da Evolia AI.

A Evolia AI é um agente criado para encontrar,
testar e desenvolver formas legítimas de gerar
receita online.

OBJETIVO ATUAL:
{objetivo}

LOCALIZAÇÃO:
{localizacao}

MEMÓRIA DE APRENDIZADOS ANTERIORES:
{memoria_texto}

DESEMPENHO E RESULTADOS DOS TESTES:
{json.dumps(contexto_estrategico, ensure_ascii=False, indent=2)}

AVALIAÇÃO OBJETIVA DAS ESTRATÉGIAS:
{json.dumps(avaliacao_estrategias, ensure_ascii=False, indent=2)}

CICLO IMEDIATAMENTE ANTERIOR:
{ciclo_anterior_texto}

ESTADO ATUAL DO FUNIL COMERCIAL:
{json.dumps(estado_comercial, ensure_ascii=False, indent=2)}

REGRA DO FUNIL:
O estado comercial representa o progresso real. Se houver ação aguardando autorização, aguarde em vez de criar outro alvo equivalente. Se houver ação executada sem resposta, priorize acompanhamento antes de reiniciar a prospecção. Se houver interesse, avance para proposta. Se houver venda confirmada, priorize medição e expansão.

REGRA DO CICLO:
O ciclo anterior é a experiência mais recente da Evolia. Não reinicie o processo do zero. Determine o que aconteceu, quais evidências foram obtidas, o que não foi concluído e qual é a consequência lógica para ESTE ciclo. Se encontrou um alvo válido, avance; se não encontrou evidência suficiente, mude a pesquisa; se preparou uma ação externa, não duplique o alvo; se houve resultado financeiro positivo, aprofunde a estratégia; se houve perda financeira repetida, modifique a estratégia.

Use o desempenho acima como evidência. Estratégias sem resultado financeiro positivo não devem ser tratadas como validadas. Resultados zero significam que ainda não houve receita real. Abordagens preparadas ou enviadas, sem resposta ou venda confirmada, não devem ser tratadas como receita. Testes internos com receita zero não são, por si só, fracassos financeiros. Se uma estratégia tiver evidência repetida de baixo desempenho, procure uma variação ou outra oportunidade em vez de repetir mecanicamente.

Ao decidir sobre uma estratégia, use:
- continuar: quando houver evidência financeira positiva registrada;
- modificar: quando houver sinais negativos repetidos ou resultado total negativo;
- testar_nova: quando não houver evidência suficiente ou quando for uma estratégia nova;
- aguardar: quando nenhuma ação adicional for justificada.
Nunca trate uma estratégia como validada apenas porque foi criada, pesquisada ou planejada.

PESQUISA ATUAL:
{fontes_texto}

Sua função NÃO é simplesmente listar ideias.

Você deve:

1. analisar as oportunidades encontradas;
2. considerar o que a Evolia AI já aprendeu;
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
12. quando escolher "preparar_abordagem", identificar uma URL pública e específica do alvo no campo "url_alvo";
13. registrar o que deverá ser aprendido com o teste;
14. definir explicitamente a consequência do ciclo anterior para a decisão atual;
15. explicar em "justificativa_evidencia" quais fatos do ciclo anterior e da memória sustentam a escolha.

REGRA IMPORTANTE:

A Evolia AI possui R$0 de capital inicial.

Portanto, priorize estratégias que possam começar
sem investimento financeiro.

A Evolia AI não deve:

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
- preparar_abordagem
- pesquisar_alvo
- validar_alvo
- testar_estrategia
- acompanhar_lead
- preparar_followup
- medir_resultado

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

Se a oportunidade já estiver definida, mas ainda não houver um alvo público específico:
"pesquisar_alvo"

Se existir um alvo público encontrado, mas ainda faltar evidência suficiente para confirmar aderência ao problema:
"validar_alvo"

Se já existir uma estratégia com oferta, cliente-alvo, proposta e um alvo específico identificado, e também tiver um canal exatamente igual a "instagram", "linkedin", "whatsapp" ou "email", com uma URL pública e específica do alvo no campo "url_alvo":
"preparar_abordagem"

REGRAS OBRIGATÓRIAS PARA "preparar_abordagem":
- "canal" deve ser EXATAMENTE um destes valores: "instagram", "linkedin", "whatsapp" ou "email".
- Não use descrições genéricas como "redes sociais", "mensagens diretas", "diretórios locais" ou "contato online".
- "url_alvo" deve ser uma URL pública específica do alvo, começando por http:// ou https://.
- O alvo deve estar claramente identificado na pesquisa atual.
- Se canal ou url_alvo não estiverem disponíveis, NÃO escolha "preparar_abordagem". Escolha "pesquisar" para localizar um alvo específico ou "analisar" para estruturar melhor a oportunidade.
- Nunca invente uma URL ou um alvo apenas para preencher o campo.

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
        "url_alvo": "...",
        "preco_teste": 0,
        "custo_teste": 0,
        "acao_imediata": "...",
        "acao_executor": "...",
        "precisa_permissao": false,
        "acao_sobre_estrategia": "continuar|modificar|testar_nova|aguardar",
        "estrategia_base": "...",
        "justificativa_evidencia": "...",
        "motivo_escolha": "...",
        "proxima_acao_ciclo": "..."
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
        dados = None
        modelo_usado = None
        erro = None

        if provider in {"auto", "gemini"} and GEMINI_API_KEY:
            cliente = genai.Client(api_key=GEMINI_API_KEY)
            dados, modelo_usado, erro = _gerar_json(cliente, prompt)

        if dados is None and provider in {"auto", "openai"}:
            dados_openai, modelo_openai, erro_openai = _gerar_openai(prompt)
            if dados_openai is not None:
                dados = dados_openai
                modelo_usado = modelo_openai
            else:
                mensagem = erro_openai or erro or "Nenhum provedor de IA conseguiu responder."
                if provider == "auto":
                    return {
                        "status": "modo_degradado",
                        "objetivo": objetivo,
                        "localizacao": localizacao,
                        "modelo_utilizado": None,
                        "ai_provider": provider,
                        "degradacao": True,
                        "erro": mensagem,
                        "detalhes": erro,
                        "erro_openai": erro_openai,
                        "modelos_tentados": MODELOS,
                        "openai_configurado": bool(OPENAI_API_KEY),
                        "decisao": {
                            "estrategia": "pesquisa incremental de oportunidades",
                            "acao_executor": "pesquisar",
                            "acao_imediata": objetivo,
                            "precisa_permissao": False,
                            "motivo_escolha": "Os provedores de IA estão indisponíveis; a Evolia continuará coletando dados sem fingir que uma decisão inteligente foi produzida."
                        },
                        "oportunidades": [],
                        "aprendizado_utilizado": [],
                        "aprendizado_esperado": "Coletar dados adicionais para o próximo ciclo.",
                        "proximo_passo": "Executar pesquisa e tentar novamente a análise em um ciclo posterior.",
                        "pesquisa_adicional_necessaria": True,
                        "fontes_utilizadas": []
                    }

                return {
                    "status": "erro_cota" if ("429" in mensagem or "RESOURCE_EXHAUSTED" in mensagem or "quota" in mensagem.lower()) else "erro",
                    "erro": mensagem,
                    "detalhes": erro,
                    "erro_openai": erro_openai,
                    "modelos_tentados": MODELOS,
                    "openai_configurado": bool(OPENAI_API_KEY),
                    "ai_provider": provider,
                    "objetivo": objetivo,
                    "localizacao": localizacao
                }

        return {
            "status": "sucesso",
            "objetivo": objetivo,
            "localizacao": localizacao,
            "modelo_utilizado": modelo_usado,
            "ai_provider": provider,
            "decisao": dados.get("decisao", {}),
            "oportunidades": dados.get("oportunidades", []),
            "aprendizado_utilizado": dados.get("aprendizado_utilizado", []),
            "aprendizado_esperado": dados.get("aprendizado_esperado"),
            "proximo_passo": dados.get("proximo_passo"),
            "pesquisa_adicional_necessaria": dados.get("pesquisa_adicional_necessaria", False),
            "fontes_utilizadas": dados.get("fontes_utilizadas", []),
            "metricas_comerciais_consideradas": metricas_comerciais
        }

    except Exception as erro:
        if provider == "auto":
            return {
                "status": "modo_degradado",
                "objetivo": objetivo,
                "localizacao": localizacao,
                "modelo_utilizado": None,
                "ai_provider": provider,
                "degradacao": True,
                "erro": str(erro),
                "decisao": {
                    "estrategia": "pesquisa incremental de oportunidades",
                    "acao_executor": "pesquisar",
                    "acao_imediata": objetivo,
                    "precisa_permissao": False,
                    "motivo_escolha": "Falha inesperada no cérebro; continuar pesquisando é a ação segura."
                },
                "oportunidades": [],
                "aprendizado_utilizado": [],
                "aprendizado_esperado": "Coletar dados adicionais para nova análise.",
                "proximo_passo": "Pesquisar e tentar nova análise posteriormente.",
                "pesquisa_adicional_necessaria": True,
                "fontes_utilizadas": []
            }
        return {
            "status": "erro",
            "erro": str(erro),
            "objetivo": objetivo,
            "localizacao": localizacao
        }


def analisar_pedido_cliente(pedido, localizacao="Brasil"):
    pedido = pedido or {}
    nome = str(pedido.get("nome", "")).strip()
    servico = str(pedido.get("servico", "")).strip()
    descricao = str(pedido.get("descricao", "")).strip()
    provider = AI_PROVIDER if AI_PROVIDER in {"auto", "gemini", "openai"} else "auto"

    if provider == "gemini" and not GEMINI_API_KEY:
        return {"status": "erro_configuracao", "erro": "GEMINI_API_KEY não configurada."}
    if provider == "openai" and not OPENAI_API_KEY:
        return {"status": "erro_configuracao", "erro": "OPENAI_API_KEY não configurada."}
    if provider == "auto" and not GEMINI_API_KEY and not OPENAI_API_KEY:
        return {"status": "erro_configuracao", "erro": "Nenhum provedor de IA configurado."}

    consultas = [
        f"como entregar {servico} para um cliente no Brasil",
        f"preço de mercado para {servico} Brasil",
        f"boas práticas e escopo de {servico}"
    ]
    try:
        pesquisa = pesquisar_varias(consultas, localizacao)[:20]
    except Exception:
        pesquisa = []

    prompt = f"""
Você é o núcleo comercial da Evolia AI.
Analise esta solicitação de cliente e prepare uma proposta realista.

CLIENTE: {nome}
SERVIÇO: {servico}
PEDIDO: {descricao}
LOCALIZAÇÃO: {localizacao}

PESQUISA DE APOIO:
{json.dumps(pesquisa, ensure_ascii=False, indent=2)}

Regras:
- Não invente informações.
- Defina escopo claro e pequeno o suficiente para ser entregue.
- Sugira preço em reais somente se houver base suficiente; caso contrário, use null.
- Defina prazo realista.
- Liste informações que ainda precisam ser confirmadas.
- Não envie mensagens, cobre, publique ou execute ações externas.
- A saída será revisada antes de ser publicada ao cliente.

Retorne somente JSON:
{{
  "resumo": "...",
  "escopo": ["..."],
  "nao_incluido": ["..."],
  "valor_sugerido": null,
  "prazo_sugerido": "...",
  "perguntas": ["..."],
  "justificativa_preco": "...",
  "riscos": ["..."],
  "proposta_cliente": "...",
  "confianca": "baixa|media|alta"
}}
"""
    dados = None
    modelo_usado = None
    erro = None

    if provider in {"auto", "gemini"} and GEMINI_API_KEY:
        try:
            cliente = genai.Client(api_key=GEMINI_API_KEY)
            dados, modelo_usado, erro = _gerar_json(cliente, prompt)
        except Exception as exc:
            erro = str(exc)

    if dados is None and provider in {"auto", "openai"}:
        dados_openai, modelo_openai, erro_openai = _gerar_openai(prompt)
        if dados_openai is not None:
            dados, modelo_usado, erro = dados_openai, modelo_openai, None
        else:
            erro = erro_openai or erro

    if dados is None:
        return {"status": "erro_cerebro", "erro": erro or "Não foi possível analisar o pedido.", "pedido_id": pedido.get("id")}

    return {
        "status": "sucesso",
        "pedido_id": pedido.get("id"),
        "modelo_utilizado": modelo_usado,
        "analise": dados,
        "fontes_utilizadas": pesquisa
    }
