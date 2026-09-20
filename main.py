from flask import Flask, request, jsonify, render_template_string
import os

from ai import analisar_oportunidade
from agent import executar_ciclo
from memory import obter_acoes_externas, atualizar_acao_externa, registrar_feedback_acao_externa, obter_metricas_comerciais
from external import iniciar_acao_autorizada, consultar_acao_externa
from pagamentos import criar_cobranca_pix, validar_webhook, processar_webhook, sincronizar_pagamento
from memory import obter_pagamentos, atualizar_pagamento, validar_venda_para_cobranca


app = Flask(__name__)
APPROVAL_TOKEN = os.getenv("EVOLIA_APPROVAL_TOKEN", "").strip()


def validar_token():
    if not APPROVAL_TOKEN:
        return False
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip() == APPROVAL_TOKEN
    return False


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Evolia AI</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 700px;
            margin: 40px auto;
            padding: 20px;
        }
        textarea, input {
            width: 100%;
            padding: 10px;
            margin-top: 8px;
            box-sizing: border-box;
        }
        textarea {
            height: 120px;
            resize: vertical;
        }
        button {
            margin-top: 12px;
            padding: 12px 20px;
            cursor: pointer;
        }
        #resultado {
            white-space: pre-wrap;
            margin-top: 20px;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <h1>Evolia AI</h1>
    <p>Objetivo atual da Evolia:</p>

    <textarea id="objetivo"
        placeholder="Ex.: Encontrar uma oportunidade de negócio online"></textarea>

    <p>Localização:</p>

    <input id="localizacao" type="text"
        placeholder="Ex.: Brasil">

    <br>

    <button onclick="executarCiclo()">
        Executar ciclo da Evolia
    </button>

    <div id="resultado"></div>
    <hr>
    <h2>Ações externas pendentes</h2>
    <p>Estas ações foram preparadas pela Evolia e aguardam sua autorização.</p>
    <div id="statusAcao"></div>
    <input id="tokenAutorizacao" type="password" placeholder="Token de autorização">
    <button onclick="carregarAcoes()">Carregar ações</button>
    <div id="acoes"></div>
    <hr>
    <h2>Resultados comerciais</h2>
    <p>Use este painel para registrar o que aconteceu depois de uma abordagem executada.</p>
    <div id="historicoAcoes"></div>
    <hr>
    <h2>Pagamentos</h2>
    <div id="pagamentos"></div>

    <script>
        async function executarCiclo() {
            const objetivo = document.getElementById("objetivo").value;
            const localizacao = document.getElementById("localizacao").value;
            const resultado = document.getElementById("resultado");

            if (!objetivo.trim()) {
                resultado.textContent = "Digite um objetivo.";
                return;
            }

            if (!localizacao.trim()) {
                resultado.textContent = "Informe a localização.";
                return;
            }

            resultado.textContent = "Evolia executando ciclo...";

            try {
                const resposta = await fetch("/ciclo", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        objetivo: objetivo,
                        localizacao: localizacao
                    })
                });

                const dados = await resposta.json();

                resultado.textContent = JSON.stringify(dados, null, 2);
            } catch (erro) {
                resultado.textContent = "Erro: " + erro;
            }
        }
        function obterToken() {
            return document.getElementById("tokenAutorizacao").value.trim() || sessionStorage.getItem("evolia_token") || "";
        }
        async function carregarAcoes() {
            const resultado = document.getElementById("acoes");
            const token = obterToken();
            if (!token) {
                resultado.innerHTML = "<p>Informe o token de autorização.</p>";
                return;
            }
            sessionStorage.setItem("evolia_token", token);
            const resposta = await fetch("/acoes-pendentes", {headers: {"Authorization": "Bearer " + token}});
            const dados = await resposta.json();
            if (!resposta.ok) {
                resultado.innerHTML = "<p>" + (dados.erro || "Token inválido.") + "</p>";
                return;
            }
            if (!dados.acoes || dados.acoes.length === 0) {
                resultado.innerHTML = "<p>Nenhuma ação aguardando autorização.</p>";
                return;
            }
            resultado.innerHTML = dados.acoes.map(acao =>
                "<div style='border:1px solid #ccc;padding:15px;margin:12px 0;border-radius:8px'>" +
                "<b>Alvo:</b> " + (acao.alvo || "-") + "<br>" +
                "<b>Canal:</b> " + (acao.canal || "-") +
                "<p><b>Mensagem:</b></p><pre style='white-space:pre-wrap'>" + (acao.mensagem || "") + "</pre>" +
                "<button onclick=" + JSON.stringify("decidirAcao('" + acao.id + "','autorizar')") + ">Autorizar</button> " +
                "<button onclick=" + JSON.stringify("decidirAcao('" + acao.id + "','recusar')") + ">Recusar</button></div>"
            ).join("");
        }
        async function decidirAcao(id, decisao) {
            const token = obterToken();
            const resposta = await fetch("/acoes/" + encodeURIComponent(id) + "/" + decisao, {method:"POST", headers: {"Authorization": "Bearer " + token}});
            const dados = await resposta.json();
            document.getElementById("statusAcao").textContent = dados.mensagem || JSON.stringify(dados);
            carregarAcoes();
        }
        async function carregarAcoesEmAndamento() {
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/acoes-em-andamento", {headers: {"Authorization": "Bearer " + token}});
                if (!resposta.ok) return;
                const dados = await resposta.json();
                const emAndamento = dados.acoes || [];
                if (emAndamento.length > 0) {
                    document.getElementById("statusAcao").textContent = "Há " + emAndamento.length + " ação(ões) externa(s) em execução. A Evolia está acompanhando o resultado."; 
                }
            } catch (erro) {}
        }

        async function carregarPagamentos() {
            const resultado = document.getElementById("pagamentos");
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/pagamentos", {headers: {"Authorization": "Bearer " + token}});
                const dados = await resposta.json();
                if (!resposta.ok) {
                    resultado.innerHTML = "<p>" + (dados.erro || "Não foi possível carregar pagamentos.") + "</p>";
                    return;
                }
                const pagamentos = dados.pagamentos || [];
                if (!pagamentos.length) {
                    resultado.innerHTML = "<p>Nenhum pagamento registrado.</p>";
                    return;
                }
                resultado.innerHTML = pagamentos.slice().reverse().slice(0, 20).map(p => {
                    const valor = Number(p.valor || 0).toLocaleString("pt-BR", {style:"currency", currency:"BRL"});
                    return "<div style='border:1px solid #ccc;padding:15px;margin:12px 0;border-radius:8px'>" +
                        "<b>Status:</b> " + (p.status || "-") + "<br>" +
                        "<b>Valor:</b> " + valor + "<br>" +
                        "<b>Descrição:</b> " + (p.descricao || "-") + "<br>" +
                        "<b>Referência:</b> " + (p.referencia || "-") + "<br>" +
                        "<b>Comprador:</b> " + (p.email_comprador || "-") +
                        (p.ticket_url ? "<br><a href='" + p.ticket_url + "' target='_blank' rel='noopener'>Abrir cobrança</a>" : "") +
                        "</div>";
                }).join("");
            } catch (erro) {
                resultado.innerHTML = "<p>Erro ao carregar pagamentos.</p>";
            }
        }

        async function carregarHistorico() {
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/acoes-historico", {headers: {"Authorization": "Bearer " + token}});
                const dados = await resposta.json();
                if (!resposta.ok) return;
                const metricas = dados.metricas || {};
                document.getElementById("historicoAcoes").innerHTML =
                    "<p>Ações executadas: " + (metricas.executadas || 0) +
                    " | Respostas: " + (metricas.respostas || 0) +
                    " | Interesses: " + (metricas.interesses || 0) +
                    " | Vendas: " + (metricas.vendas || 0) +
                    " | Receita confirmada: " +
                    Number(metricas.receita_confirmada || 0).toLocaleString("pt-BR", {style:"currency", currency:"BRL"}) +
                    "</p>";
            } catch (erro) {}
        }

        let intervaloAcoes = null;
        function iniciarAtualizacaoAutomatica() {
            if (intervaloAcoes) clearInterval(intervaloAcoes);
            if (obterToken()) {
                carregarAcoes();
                carregarAcoesEmAndamento();
                carregarHistorico();
                carregarPagamentos();
                intervaloAcoes = setInterval(() => {
                    if (obterToken()) {
                        carregarAcoes();
                        carregarAcoesEmAndamento();
                        carregarHistorico();
                        carregarPagamentos();
                    }
                }, 10000);
            }
        }
        window.addEventListener("load", iniciarAtualizacaoAutomatica);
        document.getElementById("tokenAutorizacao").addEventListener("change", iniciarAtualizacaoAutomatica);
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "nome": "Evolia AI"
    })


@app.route("/acoes-em-andamento")
def acoes_em_andamento():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    acoes = obter_acoes_externas(status="executando", limite=50)
    resultados = [consultar_acao_externa(acao.get("id")) for acao in acoes]
    return jsonify({"acoes": resultados})


@app.route("/acoes-pendentes")
def acoes_pendentes():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    acoes = obter_acoes_externas(status="aguardando_autorizacao", limite=50)
    validas = [
        acao for acao in acoes
        if (acao.get("alvo") or "").strip()
        and (acao.get("mensagem") or "").strip()
        and ((acao.get("contexto") or {}).get("url_alvo") or "").startswith(("https://", "http://"))
    ]
    return jsonify({"acoes": validas[:20]})


@app.route("/acoes/<acao_id>/<decisao>", methods=["POST"])
def decidir_acao(acao_id, decisao):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    if decisao not in {"autorizar", "recusar"}:
        return jsonify({"erro": "Decisão inválida."}), 400
    acao = next((x for x in obter_acoes_externas(limite=100) if x.get("id") == acao_id), None)
    if not acao:
        return jsonify({"erro": "Ação não encontrada."}), 404
    if acao.get("status") != "aguardando_autorizacao":
        return jsonify({"erro": "Esta ação já foi processada."}), 409
    if decisao == "autorizar":
        contexto = acao.get("contexto") or {}
        if not (contexto.get("url_alvo") or "").startswith(("https://", "http://")):
            return jsonify({"erro": "Esta ação ainda não possui uma URL de destino válida. Ela não pode ser executada."}), 400

        atualizar_acao_externa(acao_id, "autorizada", {"origem": "interface_usuario"})
        execucao = iniciar_acao_autorizada(acao_id)

        if execucao.get("status") == "executando":
            return jsonify({
                "status": "executando",
                "mensagem": "Ação autorizada e execução externa iniciada.",
                "execucao": execucao
            })

        return jsonify({
            "status": execucao.get("status", "falhou"),
            "mensagem": "Ação autorizada, mas a execução não foi iniciada.",
            "execucao": execucao
        }), 502

    atualizar_acao_externa(acao_id, "cancelada", {"origem": "interface_usuario"})
    return jsonify({"status": "cancelada", "mensagem": "Ação recusada e cancelada."})


@app.route("/acoes-historico")
def acoes_historico():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    acoes = obter_acoes_externas(limite=100)
    concluidas = [x for x in acoes if x.get("status") in {"executada", "falhou", "cancelada"}]
    return jsonify({
        "acoes": concluidas[-30:],
        "metricas": obter_metricas_comerciais()
    })


@app.route("/acoes/<acao_id>/feedback", methods=["POST"])
def feedback_acao(acao_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    dados = request.get_json(silent=True) or {}
    interesse = dados.get("interesse")
    venda = bool(dados.get("venda", False))
    try:
        receita = float(dados.get("receita", 0) or 0)
        custo = float(dados.get("custo", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Receita e custo devem ser números."}), 400
    if receita < 0 or custo < 0:
        return jsonify({"erro": "Receita e custo não podem ser negativos."}), 400
    feedback = registrar_feedback_acao_externa(acao_id, resposta=str(dados.get("resposta", "")).strip() or None, interesse=str(interesse).strip() if interesse is not None else None, venda=venda, receita=receita, custo=custo, observacao=str(dados.get("observacao", "")).strip() or None)
    if feedback is None:
        return jsonify({"erro": "Ação externa não encontrada."}), 404
    if isinstance(feedback, dict) and feedback.get("erro"):
        return jsonify(feedback), 409
    return jsonify({"status": "registrado", "feedback": feedback})


@app.route("/acoes/<acao_id>/status")
def status_acao(acao_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify(consultar_acao_externa(acao_id))


@app.route("/pagamentos/sincronizar-pendentes", methods=["POST"])
def pagamentos_sincronizar_pendentes():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not verificar_token_aprovacao(token):
        return jsonify({"erro": "Não autorizado."}), 401

    pendentes = [
        p for p in obter_pagamentos(limite=200)
        if p.get("status") in {"aguardando_pagamento", "processando", "pendente"}
    ]
    resultados = []
    for pagamento in pendentes:
        resultados.append(sincronizar_pagamento(pagamento.get("id")))

    return jsonify({
        "status": "sincronizado",
        "quantidade": len(resultados),
        "resultados": resultados
    })


@app.route("/pagamentos/<pagamento_id>/sincronizar", methods=["POST"])
def pagamento_sincronizar(pagamento_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not verificar_token_aprovacao(token):
        return jsonify({"erro": "Não autorizado."}), 401
    resultado = sincronizar_pagamento(pagamento_id)
    if resultado.get("status") == "nao_encontrado":
        return jsonify(resultado), 404
    if resultado.get("status") == "indisponivel":
        return jsonify(resultado), 503
    return jsonify(resultado)


@app.route("/pagamentos/<pagamento_id>", methods=["GET"])
def pagamento_detalhe(pagamento_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not verificar_token_aprovacao(token):
        return jsonify({"erro": "Não autorizado."}), 401

    pagamento = obter_pagamento_por_id(pagamento_id)
    if not pagamento:
        return jsonify({"erro": "Pagamento não encontrado."}), 404

    return jsonify({"pagamento": pagamento})


@app.route("/pagamentos", methods=["GET"])
def listar_pagamentos():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify({"pagamentos": obter_pagamentos()})


@app.route("/pagamentos/pix", methods=["POST"])
def criar_pagamento_pix():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401

    dados = request.get_json(silent=True) or {}
    try:
        valor = float(dados.get("valor", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor inválido."}), 400

    if valor <= 0:
        return jsonify({"erro": "O valor deve ser maior que zero."}), 400

    email = str(dados.get("email", "")).strip()
    if not email:
        return jsonify({"erro": "Informe o e-mail do comprador para gerar a cobrança Pix."}), 400

    acao_id = str(dados.get("acao_id", "")).strip()
    if not acao_id:
        return jsonify({"erro": "Informe a ação comercial que originou esta cobrança."}), 400

    venda = validar_venda_para_cobranca(acao_id)
    if not venda.get("ok"):
        return jsonify({"erro": venda.get("motivo", "Venda não confirmada.")}), 409

    referencia = str(dados.get("referencia", "")).strip() or ("venda-" + acao_id[:32])

    resultado = criar_cobranca_pix(
        valor=valor,
        descricao=str(dados.get("descricao", "Serviço Evolia")).strip() or "Serviço Evolia",
        referencia=referencia,
        email=email,
        acao_id=acao_id
    )
    if resultado.get("status") == "criado":
        pagamento = resultado.get("pagamento") or {}
        estrategia = str(dados.get("estrategia", "")).strip() or None
        if estrategia and pagamento.get("id"):
            atualizar_pagamento(pagamento["id"], estrategia=estrategia)
            pagamento["estrategia"] = estrategia
    return jsonify(resultado), (200 if resultado.get("status") == "criado" else 400)


@app.route("/pagamentos/webhook", methods=["POST"])
def pagamentos_webhook():
    dados = request.get_json(silent=True) or {}
    data_id = request.args.get("data.id") or ((dados.get("data") or {}).get("id"))
    if not validar_webhook(request.headers, data_id):
        return jsonify({"erro": "Assinatura do webhook inválida."}), 401

    resultado = processar_webhook(dados, data_id)
    return jsonify(resultado), 200


@app.route("/ciclo", methods=["POST"])
def ciclo():
    dados = request.get_json(silent=True) or {}

    objetivo = str(
        dados.get("objetivo", "Gerar receita")
    ).strip()

    localizacao = str(
        dados.get("localizacao", "Brasil")
    ).strip()

    if not objetivo:
        return jsonify({"erro": "Informe um objetivo."}), 400

    if not localizacao:
        return jsonify({"erro": "Informe a localização."}), 400

    try:
        resultado = executar_ciclo(
            objetivo,
            localizacao
        )
        return jsonify(resultado)
    except Exception as erro:
        return jsonify({
            "status": "erro",
            "erro": str(erro)
        }), 500


@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.get_json(silent=True) or {}

    objetivo = str(
        dados.get("objetivo", "")
    ).strip()

    localizacao = str(
        dados.get("localizacao", "")
    ).strip()

    if not objetivo:
        return jsonify({
            "erro": "Informe um objetivo."
        }), 400

    if not localizacao:
        return jsonify({
            "erro": "Informe sua cidade e estado."
        }), 400

    try:
        resultado = analisar_oportunidade(
            objetivo,
            localizacao
        )
        return jsonify(resultado)
    except Exception as erro:
        return jsonify({
            "status": "erro",
            "erro": str(erro)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
