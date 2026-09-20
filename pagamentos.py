import hashlib
import hmac
import os
import uuid
import re
from datetime import datetime, timezone

import requests

from memory import registrar_pagamento, atualizar_pagamento, obter_pagamentos


MP_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip()
MP_WEBHOOK_SECRET = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "").strip()
MP_API = "https://api.mercadopago.com"


def agora():
    return datetime.now(timezone.utc).isoformat()


def criar_cobranca_pix(valor, descricao, referencia=None, email=None, acao_id=None):
    if not MP_ACCESS_TOKEN:
        return {
            "status": "aguardando_configuracao",
            "erro": "MERCADOPAGO_ACCESS_TOKEN não configurado."
        }

    valor = float(valor)
    if valor <= 0:
        return {"status": "erro", "erro": "O valor deve ser maior que zero."}

    email = (email or "").strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return {"status": "erro", "erro": "Informe um e-mail válido do comprador para criar a cobrança Pix."}

    referencia = (referencia or uuid.uuid4().hex).strip()
    if len(referencia) > 64:
        return {"status": "erro", "erro": "A referência deve ter no máximo 64 caracteres."}
    existente = next((x for x in obter_pagamentos() if x.get("referencia") == referencia), None)
    if existente:
        return {"status": "ja_existente", "pagamento": existente}

    payload = {
        "type": "online",
        "total_amount": f"{valor:.2f}",
        "external_reference": referencia,
        "processing_mode": "automatic",
        "transactions": {
            "payments": [{
                "amount": f"{valor:.2f}",
                "payment_method": {"id": "pix", "type": "bank_transfer"}
            }]
        },
        "payer": {"email": email}
    }

    try:
        resposta = requests.post(
            f"{MP_API}/v1/orders",
            headers={
                "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": referencia
            },
            json=payload,
            timeout=30
        )
        dados = resposta.json()
        if not resposta.ok:
            return {"status": "erro", "codigo": resposta.status_code, "detalhes": dados}

        order_id = str(dados.get("id"))
        payment = {
            "id": order_id,
            "provedor": "mercado_pago",
            "tipo": "pix",
            "status": "aguardando_pagamento",
            "valor": valor,
            "descricao": descricao,
            "referencia": referencia,
            "email_comprador": email,
            "acao_id": acao_id,
            "criado_em": agora(),
            "ticket_url": None,
            "qr_code": None
        }

        transactions = (dados.get("transactions") or {}).get("payments") or []
        if transactions:
            method = transactions[0].get("payment_method") or {}
            payment["ticket_url"] = method.get("ticket_url")
            payment["qr_code"] = method.get("qr_code")

        registrar_pagamento(payment)
        return {"status": "criado", "pagamento": payment}
    except Exception as erro:
        return {"status": "erro", "erro": str(erro)}


def consultar_order(order_id):
    if not MP_ACCESS_TOKEN or not order_id:
        return None
    try:
        resposta = requests.get(
            f"{MP_API}/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
            timeout=20
        )
        if not resposta.ok:
            return None
        return resposta.json()
    except Exception:
        return None


def validar_webhook(headers, data_id):
    if not MP_WEBHOOK_SECRET:
        return False

    signature = headers.get("x-signature", "")
    request_id = headers.get("x-request-id", "")
    if not signature:
        return False

    partes = {}
    for parte in signature.split(","):
        chave, separador, valor = parte.partition("=")
        if separador:
            partes[chave.strip()] = valor.strip()

    ts = partes.get("ts")
    recebido = partes.get("v1")
    if not ts or not recebido:
        return False

    manifest = f"id:{str(data_id or '').lower()};request-id:{request_id};ts:{ts};"
    esperado = hmac.new(
        MP_WEBHOOK_SECRET.encode(),
        manifest.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(esperado, recebido)


def processar_webhook(payload, data_id):
    if not data_id:
        return {"status": "ignorado", "motivo": "data.id ausente"}

    pagamento_id = str(data_id)
    existente = next((x for x in obter_pagamentos() if str(x.get("id")) == pagamento_id), None)

    if not existente:
        return {"status": "ignorado", "motivo": "pagamento não registrado pela Evolia", "id": pagamento_id}

    action = payload.get("action", "")
    tipo = payload.get("type", "")
    atualizado = atualizar_pagamento(
        pagamento_id,
        ultimo_evento=action,
        tipo_evento=tipo,
        webhook_recebido_em=agora()
    )

    if action in {"order.processed", "order.updated", "payment.updated"}:
        order = consultar_order(pagamento_id)
        status_order = (order or {}).get("status")
        status_detail = (order or {}).get("status_detail")
        pagamentos = ((order or {}).get("transactions") or {}).get("payments") or []
        status_pagamento = pagamentos[0].get("status") if pagamentos else None

        confirmado = (
            status_order == "processed"
            or status_pagamento in {"approved", "processed"}
        )
        falhou = (
            status_order in {"canceled", "cancelled", "rejected", "failed", "expired"}
            or status_pagamento in {"rejected", "cancelled", "canceled", "refunded", "charged_back"}
        )

        if confirmado:
            atualizar_pagamento(
                pagamento_id,
                status="pago",
                status_provedor=status_order or status_pagamento,
                status_detail=status_detail
            )

            # Recarrega o registro após a atualização para manter o webhook idempotente.
            atual = next(
                (x for x in obter_pagamentos() if str(x.get("id")) == pagamento_id),
                existente
            )
            if not atual.get("receita_registrada"):
                # A venda já é contabilizada quando o feedback de venda é confirmado.
                # O pagamento apenas liquida essa venda; não registra receita novamente.
                atualizar_pagamento(
                    pagamento_id,
                    receita_registrada=True,
                    receita_reconhecida_em=agora()
                )
        elif falhou:
            atualizar_pagamento(
                pagamento_id,
                status="falhou",
                status_provedor=status_order or status_pagamento,
                status_detail=status_detail
            )

    final = next(
        (x for x in obter_pagamentos() if str(x.get("id")) == pagamento_id),
        existente
    )
    return {"status": "processado", "pagamento": final}
