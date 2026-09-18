from flask import Flask, request, jsonify

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
    dados = request.json or {}
    objetivo = dados.get("objetivo", "")

    return jsonify({
        "objetivo": objetivo,
        "status": "recebido",
        "proxima_etapa": "Analisar oportunidades."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
