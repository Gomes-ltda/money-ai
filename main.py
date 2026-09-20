from flask import Flask, request, jsonify, render_template_string

from ai import analisar_oportunidade
from agent import executar_ciclo


app = Flask(__name__)


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
