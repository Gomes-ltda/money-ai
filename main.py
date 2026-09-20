from flask import Flask, request, jsonify, render_template_string
import os

from ai import analisar_oportunidade
from agent import executar_ciclo
from memory import obter_acoes_externas, atualizar_acao_externa
from external import iniciar_acao_autorizada, consultar_acao_externa


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
        let intervaloAcoes = null;
        function iniciarAtualizacaoAutomatica() {
            if (intervaloAcoes) clearInterval(intervaloAcoes);
            if (obterToken()) {
                carregarAcoes();
                intervaloAcoes = setInterval(() => {
                    if (obterToken()) carregarAcoes();
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


@app.route("/acoes-pendentes")
def acoes_pendentes():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify({"acoes": obter_acoes_externas(status="aguardando_autorizacao", limite=20)})


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


@app.route("/acoes/<acao_id>/status")
def status_acao(acao_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify(consultar_acao_externa(acao_id))


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
