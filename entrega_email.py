import html
import os
import re
import requests

RESEND_API_URL = "https://api.resend.com/emails"

def _email_valido(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(email or "").strip()))

def enviar_resultado_por_email(pedido, resultado):
    """Entrega o resultado de um serviço contratado via Resend."""
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    remetente = os.getenv("EVOLIA_EMAIL_FROM", "onboarding@resend.dev").strip()
    destinatario = str(pedido.get("email") or "").strip().lower()

    if not api_key:
        return {"status": "erro", "erro": "RESEND_API_KEY não configurada."}
    if not _email_valido(destinatario):
        return {"status": "erro", "erro": "E-mail do pedido inválido."}

    servico = html.escape(str(pedido.get("servico") or "Serviço"))
    titulo = html.escape(str(resultado.get("titulo") or "Entrega do serviço"))
    conteudo = html.escape(str(resultado.get("conteudo") or "").strip()).replace("\n", "<br>")
    itens = resultado.get("itens_entregues") or []
    limitacoes = resultado.get("limitacoes") or []
    fontes = resultado.get("fontes") or []

    itens_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in itens)
    limitacoes_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in limitacoes)
    fontes_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in fontes)

    corpo_html = f"""
    <html><body>
      <h2>{titulo}</h2>
      <p><strong>Serviço:</strong> {servico}</p>
      <h3>Entrega</h3>
      <p>{conteudo}</p>
      {"<h3>Itens entregues</h3><ul>" + itens_html + "</ul>" if itens_html else ""}
      {"<h3>Limitações</h3><ul>" + limitacoes_html + "</ul>" if limitacoes_html else ""}
      {"<h3>Fontes</h3><ul>" + fontes_html + "</ul>" if fontes_html else ""}
      <hr><p>Entrega realizada pela EVOLIA AI.</p>
    </body></html>
    """

    payload = {
        "from": remetente,
        "to": [destinatario],
        "subject": f"EVOLIA AI — Entrega: {str(pedido.get('servico') or 'Serviço')}",
        "html": corpo_html,
        "text": str(resultado.get("conteudo") or "").strip(),
    }

    try:
        resposta = requests.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
    except requests.RequestException as erro:
        return {"status": "erro", "erro": f"Falha de comunicação com o Resend: {erro}"}

    if resposta.status_code not in {200, 201}:
        try:
            detalhes = resposta.json()
        except ValueError:
            detalhes = resposta.text[:500]
        return {"status": "erro", "erro": "Resend recusou o envio.", "status_code": resposta.status_code, "detalhes": detalhes}

    try:
        dados = resposta.json()
    except ValueError:
        return {"status": "erro", "erro": "Resend respondeu sem JSON válido."}

    return {"status": "enviado", "id": dados.get("id")}
