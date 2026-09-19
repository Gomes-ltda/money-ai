from flask import Flask, request, jsonify, render_template_string
from ai import analisar_oportunidade

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Money AI</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
        }

        textarea,
        input {
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

    <h1>Money AI</h1>

    <p>O que você quer alcançar?</p>

    <textarea
        id="objetivo"
        placeholder="Ex.: Quero ganhar R$ 200 esta semana sem aparecer."
    ></textarea>

    <p>Em qual cidade e estado você está?</p>

    <input
        id="localizacao"
        type="text"
        placeholder="Ex.: Porto Velho, RO"
    >

    <br>

    <button onclick="analisar()">Encontrar oportunidades</button>

    <div id="resultado"></div>

    <script>
        async function analisar() {

            const objetivo =
                document.getElementById("objetivo").value;

            const localizacao =
                document.getElementById("localizacao").value;

            const resultado =
                document.getElementById("resultado");

            if (!objetivo.trim()) {
                resultado.textContent =
                    "Digite o que você quer alcançar.";
                return;
            }

            if (!localizacao.trim()) {
                resultado.textContent =
                    "Informe sua cidade e estado.";
                return;
            }

            resultado.textContent =
                "Pesquisando oportunidades próximas e online...";

            try {

                const resposta = await fetch("/analisar", {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        objetivo: objetivo,
                        localizacao: localizacao
                    })
                });

                const dados = await resposta.json();

                if (dados.analise) {

                    resultado.textContent =
                        dados.analise;

                } else {

                    resultado.textContent =
                        "Erro: " +
                        (dados.erro || "resposta inesperada");

                }

            } catch (erro) {

                resultado.textContent =
                    "Erro de conexão: " + erro;

            }
        }
    </script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/analisar", methods=["POST"])
def analisar():

    dados = request.get_json(silent=True) or {}

    objetivo = dados.get("objetivo", "").strip()
    localizacao = dados.get("localizacao", "").strip()

    if not objetivo:
        return jsonify({
            "erro": "Informe um objetivo."
        }), 400

    if not localizacao:
        return jsonify({
            "erro": "Informe sua cidade e estado."
        }), 400

    resultado = analisar_oportunidade(
        objetivo,
        localizacao
    )

    return jsonify(resultado)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
