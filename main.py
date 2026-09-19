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

        textarea {
            width: 100%;
            height: 120px;
            padding: 10px;
            box-sizing: border-box;
        }

        button {
            margin-top: 10px;
            padding: 12px 20px;
            cursor: pointer;
        }

        #resultado {
            white-space: pre-wrap;
            margin-top: 20px;
        }
    </style>
</head>

<body>
    <h1>Money AI</h1>

    <p>O que você quer alcançar?</p>

    <textarea id="objetivo"
        placeholder="Ex.: Quero ganhar R$ 1.000 por mês pela internet sem aparecer."></textarea>

    <br>

    <button onclick="analisar()">Analisar oportunidade</button>

    <div id="resultado"></div>

    <script>
        async function analisar() {
            const objetivo = document.getElementById("objetivo").value;
            const resultado = document.getElementById("resultado");

            if (!objetivo.trim()) {
                resultado.textContent = "Digite um objetivo.";
                return;
            }

            resultado.textContent = "Analisando...";

            try {
                const resposta = await fetch("/analisar", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        objetivo: objetivo
                    })
                });

                const dados = await resposta.json();

                if (dados.analise) {
                    resultado.textContent = dados.analise;
                } else {
                    resultado.textContent =
                        "Erro: " + (dados.erro || "resposta inesperada");
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

    if not objetivo:
        return jsonify({
            "erro": "Informe um objetivo."
        }), 400

    resultado = analisar_oportunidade(objetivo)

    return jsonify(resultado)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
