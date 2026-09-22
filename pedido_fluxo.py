from datetime import datetime, timezone

from memory import (
    obter_pedido_cliente,
    atualizar_pedido_cliente,
    obter_pagamento_por_id,
    obter_pagamentos,
)
from pagamentos import criar_cobranca_pix

STATUS = {
    "recebido",
    "em_analise",
    "proposta_preparada",
    "proposta_enviada",
    "aguardando_pagamento",
    "em_execucao",
    "entregue",
    "cancelado",
}

TRANSICOES = {
    "recebido": {"em_analise", "cancelado"},
    "em_analise": {"proposta_preparada", "cancelado"},
    "proposta_preparada": {"proposta_enviada", "cancelado"},
    "proposta_enviada": {"aguardando_pagamento", "cancelado"},
    "aguardando_pagamento": {"em_execucao", "cancelado"},
    "em_execucao": {"entregue", "cancelado"},
    "entregue": set(),
    "cancelado": set(),
}


def agora():
    return datetime.now(timezone.utc).isoformat()


def registrar_ciclo_pedido(pedido_id, etapa, status, detalhe=None):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return None

    ciclo = pedido.get("ciclo") or {}
    historico = ciclo.get("historico") or []
    historico.append({
        "data": agora(),
        "etapa": etapa,
        "status": status,
        "detalhe": detalhe or "",
    })

    return atualizar_pedido_cliente(
        pedido_id,
        ciclo={
            **ciclo,
            "etapa_atual": etapa,
            "status": status,
            "ultima_atualizacao": agora(),
            "historico": historico[-50:],
        },
    )


def transicionar_pedido(pedido_id, novo_status, observacao=None):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return {"ok": False, "erro": "Pedido não encontrado."}

    atual = pedido.get("status", "recebido")
    if novo_status not in STATUS:
        return {"ok": False, "erro": "Status inválido."}

    if atual == novo_status:
        return {"ok": True, "pedido": pedido, "status": novo_status, "alteracao": False}

    if novo_status not in TRANSICOES.get(atual, set()):
        return {
            "ok": False,
            "erro": f"Transição não permitida: {atual} -> {novo_status}.",
            "status_atual": atual,
        }

    atualizado = atualizar_pedido_cliente(
        pedido_id,
        status=novo_status,
        observacao=observacao or f"Fluxo avançou de {atual} para {novo_status}.",
    )
    registrar_ciclo_pedido(
        pedido_id,
        etapa=novo_status,
        status=novo_status,
        detalhe=observacao,
    )
    return {"ok": True, "pedido": atualizado, "status": novo_status, "alteracao": True}


def publicar_proposta(pedido_id):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return {"ok": False, "erro": "Pedido não encontrado."}
    proposta = pedido.get("proposta") or {}
    if not proposta.get("texto"):
        return {"ok": False, "erro": "Não existe proposta pronta para publicar."}
    return transicionar_pedido(
        pedido_id,
        "proposta_enviada",
        "Proposta publicada na página privada do cliente após autorização do usuário.",
    )


def aceitar_proposta(pedido_id):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return {"ok": False, "erro": "Pedido não encontrado."}

    if pedido.get("status") != "proposta_enviada":
        return {"ok": False, "erro": "A proposta ainda não está disponível para aceite."}

    proposta = pedido.get("proposta") or {}
    valor = proposta.get("valor")
    if valor is None:
        return {"ok": False, "erro": "A proposta precisa ter um valor definido antes do aceite."}

    aceite = {
        "aceito": True,
        "data": agora(),
        "valor": float(valor),
        "origem": "cliente",
    }
    atualizado = atualizar_pedido_cliente(
        pedido_id,
        status="aguardando_pagamento",
        aceite=aceite,
        observacao="Cliente aceitou a proposta. O pedido aguarda pagamento.",
    )
    registrar_ciclo_pedido(
        pedido_id,
        etapa="aguardando_pagamento",
        status="aguardando_pagamento",
        detalhe="Aceite registrado pelo cliente.",
    )
    return {"ok": True, "pedido": atualizado}


def criar_pagamento_pedido(pedido_id):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return {"ok": False, "erro": "Pedido não encontrado."}

    if pedido.get("status") != "aguardando_pagamento":
        return {"ok": False, "erro": "O pedido ainda não está na etapa de pagamento."}

    proposta = pedido.get("proposta") or {}
    valor = proposta.get("valor")
    email = (pedido.get("email") or "").strip().lower()
    if valor is None or float(valor) <= 0:
        return {"ok": False, "erro": "A proposta não possui valor válido."}
    if not email:
        return {"ok": False, "erro": "O pedido precisa ter e-mail para gerar a cobrança Pix."}

    pagamento_existente = next(
        (
            p for p in obter_pagamentos(200)
            if p.get("pedido_id") == pedido_id
            and p.get("status") in {"aguardando_pagamento", "processando", "pago"}
        ),
        None,
    )
    if pagamento_existente:
        return {"ok": True, "pagamento": pagamento_existente, "ja_existente": True}

    referencia = "pedido-" + pedido_id[:40]
    resultado = criar_cobranca_pix(
        valor=float(valor),
        descricao=f"Evolia AI — {pedido.get('servico') or 'Serviço'}",
        referencia=referencia,
        email=email,
    )
    if resultado.get("status") not in {"criado", "ja_existente"}:
        return {"ok": False, "erro": resultado.get("erro") or resultado.get("detalhes") or "Não foi possível criar a cobrança.", "resultado": resultado}

    pagamento = resultado.get("pagamento") or {}
    pagamento_id = pagamento.get("id")
    atualizado = atualizar_pedido_cliente(
        pedido_id,
        pagamento_id=pagamento_id,
        observacao="Cobrança Pix criada para este pedido.",
    )
    if pagamento_id:
        from memory import atualizar_pagamento
        atualizar_pagamento(pagamento_id, pedido_id=pedido_id)

    return {"ok": True, "pedido": atualizado, "pagamento": pagamento, "ja_existente": resultado.get("status") == "ja_existente"}


def sincronizar_pedido_pagamento(pedido_id):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return {"ok": False, "erro": "Pedido não encontrado."}

    pagamento_id = pedido.get("pagamento_id")
    if not pagamento_id:
        return {"ok": True, "pedido": pedido, "status": pedido.get("status"), "pagamento": None}

    pagamento = obter_pagamento_por_id(pagamento_id)
    if not pagamento:
        return {"ok": False, "erro": "Pagamento vinculado não encontrado."}

    if pagamento.get("status") == "pago" and pedido.get("status") == "aguardando_pagamento":
        resultado = transicionar_pedido(
            pedido_id,
            "em_execucao",
            "Pagamento confirmado. O pedido entrou na etapa de execução.",
        )
        return {"ok": True, "pedido": resultado.get("pedido"), "status": "em_execucao", "pagamento": pagamento}

    return {"ok": True, "pedido": pedido, "status": pedido.get("status"), "pagamento": pagamento}


def registrar_entrega(pedido_id, texto, url=None):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return {"ok": False, "erro": "Pedido não encontrado."}

    if pedido.get("status") != "em_execucao":
        return {"ok": False, "erro": "O pedido precisa estar em execução antes da entrega."}

    texto = str(texto or "").strip()
    if not texto:
        return {"ok": False, "erro": "Informe o conteúdo da entrega."}

    entrega = {
        "texto": texto,
        "url": str(url or "").strip() or None,
        "entregue_em": agora(),
    }
    atualizado = atualizar_pedido_cliente(
        pedido_id,
        status="entregue",
        entrega=entrega,
        observacao="Entrega registrada pela operação.",
    )
    registrar_ciclo_pedido(
        pedido_id,
        etapa="entregue",
        status="entregue",
        detalhe="Entrega disponibilizada ao cliente.",
    )
    return {"ok": True, "pedido": atualizado}


def ciclo_pedido_resumo(pedido_id):
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return None
    proposta = pedido.get("proposta") or {}
    pagamento = obter_pagamento_por_id(pedido.get("pagamento_id")) if pedido.get("pagamento_id") else None
    return {
        "pedido_id": pedido_id,
        "status": pedido.get("status"),
        "etapa": (pedido.get("ciclo") or {}).get("etapa_atual") or pedido.get("status"),
        "proposta_pronta": bool(proposta.get("texto")),
        "proposta_publicada": pedido.get("status") in {"proposta_enviada", "aguardando_pagamento", "em_execucao", "entregue"},
        "aceite": pedido.get("aceite"),
        "pagamento": pagamento,
        "entrega": pedido.get("entrega"),
    }


def criar_pedido_de_venda_lead(lead, acao, feedback):
    """Converte uma venda confirmada no funil comercial em pedido operacional."""
    nome = lead.get("nome") or acao.get("alvo") or "Cliente"
    valor = float(feedback.get("receita") or 0)
    if valor <= 0:
        return {"ok": False, "erro": "A venda confirmada não possui valor de receita informado."}

    email = str(
        lead.get("email")
        or (acao.get("contexto") or {}).get("email")
        or ""
    ).strip().lower()

    # Não duplica pedidos para a mesma ação comercial.
    pedido_existente = next(
        (
            p for p in __import__("memory").carregar_memoria().get("pedidos_clientes", [])
            if (p.get("origem_lead_acao_id") == acao.get("id"))
        ),
        None,
    )
    if pedido_existente:
        return {"ok": True, "pedido": pedido_existente, "ja_existente": True}

    agora_data = agora()
    pedido = {
        "id": __import__("uuid").uuid4().hex,
        "token_publico": __import__("secrets").token_urlsafe(24),
        "criado_em": agora_data,
        "atualizado_em": agora_data,
        "nome": nome,
        "email": email,
        "whatsapp": str(lead.get("whatsapp") or (acao.get("contexto") or {}).get("whatsapp") or "").strip(),
        "instagram": str(lead.get("instagram") or "").strip(),
        "servico": lead.get("oferta") or (acao.get("contexto") or {}).get("oferta") or "Serviço contratado",
        "descricao": lead.get("problema") or "Venda confirmada no funil comercial da EVOLIA.",
        "modo_teste": False,
        "status": "aguardando_pagamento",
        "proposta": {
            "texto": "Venda confirmada no funil comercial.",
            "valor": valor,
            "prazo": None,
            "escopo": [lead.get("oferta") or "Serviço contratado"],
            "nao_incluido": [],
            "perguntas": [],
            "justificativa_preco": "Valor informado no feedback da venda.",
            "riscos": [],
            "confianca": "alta",
            "origem": "lead_comercial",
        },
        "aceite": {
            "aceito": True,
            "data": agora_data,
            "valor": valor,
            "origem": "lead_comercial",
        },
        "origem_lead_id": lead.get("id"),
        "origem_lead_acao_id": acao.get("id"),
        "historico": [
            {"data": agora_data, "status": "recebido", "observacao": "Venda confirmada no funil comercial."},
            {"data": agora_data, "status": "aguardando_pagamento", "observacao": "Pedido criado a partir de venda confirmada; pagamento é o próximo passo."},
        ],
        "ciclo": {
            "etapa_atual": "aguardando_pagamento",
            "status": "aguardando_pagamento",
            "ultima_atualizacao": agora_data,
            "historico": [],
        },
    }
    memoria = __import__("memory").carregar_memoria()
    memoria.setdefault("pedidos_clientes", []).append(pedido)
    __import__("memory").salvar_memoria(memoria)
    return {"ok": True, "pedido": pedido, "ja_existente": False}
