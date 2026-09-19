from flask import Flask, request, jsonify
from ai import analisar_oportunidade

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "nome": "Money AI",
        "status": "online",
        "mensagem": "Sistema iniciado."
    })


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
