import os
import requests

from memory import agora, atualizar_acao_externa, obter_acoes_externas, registrar_evento, registrar_aprendizado


TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY")
TINYFISH_PROFILE_ID = os.getenv("TINYFISH_PROFILE_ID", "").strip()
TINYFISH_USE_PROFILE = os.getenv("TINYFISH_USE_PROFILE", "false").strip().lower() == "true"

AGENT_URL = "https://agent.tinyfish.ai/v1/automation/run-async"
RUN_URL = "https://agent.tinyfish.ai/v1/runs"


def _validar_acao(acao):
    if acao.get("status") != "autorizada":
        return False, "A ação não está autorizada."

    if acao.get("tipo") != "abordagem_comercial":
        return False, "Tipo de ação externa não suportado."

    canal = (acao.get("canal") or "").strip().lower()
    contexto = acao.get("contexto") or {}
    url = (contexto.get("url_alvo") or "").strip()

    if canal not in {"instagram", "linkedin", "whatsapp", "email"}:
        return False, "Canal externo não suportado para execução automática."

    if not url.startswith(("https://", "http://")):
        return False, "A ação não possui uma URL de destino válida."

    if not acao.get("mensagem"):
        return False, "A ação não possui mensagem."

    return True, None


def _payload_automacao(acao):
    contexto = acao.get("contexto") or {}
    canal = (acao.get("canal") or "").strip().lower()
    url = contexto.get("url_alvo")
    mensagem = acao.get("mensagem")

    objetivo = (
        f"Execute uma única abordagem comercial no {canal} usando a página de destino "
        f"fornecida. Envie exatamente esta mensagem, sem alterá-la: {mensagem!r}. "
        "Não envie para nenhum outro destinatário. Não faça curtidas, comentários, "
        "publicações, compras, alterações de conta ou outras ações. Se o destinatário "
        "não puder ser identificado com segurança, não envie nada e informe a falha. "
        "Após a tentativa, retorne JSON com enviado (boolean), destino, canal e detalhe."
    )

    payload = {
        "url": url,
        "goal": objetivo,
        "browser_profile": "lite",
        "agent_config": {
            "max_duration_seconds": 180
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "enviado": {"type": "boolean"},
                "destino": {"type": "string"},
                "canal": {"type": "string"},
                "detalhe": {"type": "string"}
            },
            "required": ["enviado", "destino", "canal", "detalhe"]
        }
    }

    if TINYFISH_USE_PROFILE:
        payload["use_profile"] = True
        if TINYFISH_PROFILE_ID:
            payload["profile_id"] = TINYFISH_PROFILE_ID

    return payload


def iniciar_acao_autorizada(acao_id):
    if not TINYFISH_API_KEY:
        return {"status": "erro", "erro": "TINYFISH_API_KEY não configurada."}

    acao = next((x for x in obter_acoes_externas(limite=100) if x.get("id") == acao_id), None)
    if not acao:
        return {"status": "erro", "erro": "Ação externa não encontrada."}

    valido, erro = _validar_acao(acao)
    if not valido:
        atualizar_acao_externa(acao_id, "falhou", {"erro": erro})
        return {"status": "falhou", "acao_id": acao_id, "erro": erro}

    if acao.get("status") != "autorizada":
        return {"status": "bloqueado", "acao_id": acao_id, "erro": "Ação precisa estar autorizada."}

    payload = _payload_automacao(acao)

    try:
        resposta = requests.post(
            AGENT_URL,
            headers={
                "X-API-Key": TINYFISH_API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        dados = resposta.json()
        if resposta.status_code >= 400:
            atualizar_acao_externa(acao_id, "falhou", {
                "fase": "criar_automacao",
                "http_status": resposta.status_code,
                "erro": dados
            })
            return {"status": "falhou", "acao_id": acao_id, "erro": dados}

        run_id = dados.get("run_id")
        if not run_id:
            atualizar_acao_externa(acao_id, "falhou", {
                "fase": "criar_automacao",
                "erro": "TinyFish não retornou run_id.",
                "resposta": dados
            })
            return {"status": "falhou", "acao_id": acao_id, "erro": "TinyFish não retornou run_id."}

        atualizar_acao_externa(acao_id, "executando", {
            "run_id": run_id,
            "iniciada_em": agora(),
            "provedor": "tinyfish"
        })
        registrar_evento("acao_externa_iniciada", f"Ação externa {acao_id} iniciada no TinyFish com run {run_id}.")

        return {
            "status": "executando",
            "acao_id": acao_id,
            "run_id": run_id
        }

    except Exception as erro:
        atualizar_acao_externa(acao_id, "falhou", {"fase": "criar_automacao", "erro": str(erro)})
        return {"status": "falhou", "acao_id": acao_id, "erro": str(erro)}


def consultar_acao_externa(acao_id):
    if not TINYFISH_API_KEY:
        return {"status": "erro", "erro": "TINYFISH_API_KEY não configurada."}

    acao = next((x for x in obter_acoes_externas(limite=100) if x.get("id") == acao_id), None)
    if not acao:
        return {"status": "erro", "erro": "Ação externa não encontrada."}

    resultado_anterior = acao.get("resultado") or {}
    run_id = resultado_anterior.get("run_id")
    if not run_id:
        return {"status": "erro", "erro": "A ação não possui run_id."}

    try:
        resposta = requests.get(
            f"{RUN_URL}/{run_id}",
            headers={"X-API-Key": TINYFISH_API_KEY},
            timeout=30
        )
        dados = resposta.json()
        if resposta.status_code >= 400:
            return {"status": "falhou", "acao_id": acao_id, "run_id": run_id, "erro": dados}

        status = dados.get("status")
        if status == "COMPLETED":
            resultado = dados.get("result") or {}
            enviado = bool(resultado.get("enviado")) if isinstance(resultado, dict) else False
            novo_status = "executada" if enviado else "falhou"
            ja_finalizada = acao.get("status") in {"executada", "falhou", "cancelada"}
            atualizar_acao_externa(acao_id, novo_status, {
                "run_id": run_id,
                "status_tinyfish": status,
                "resultado_tinyfish": resultado,
                "consultado_em": agora()
            })
            if not ja_finalizada:
                registrar_evento("acao_externa_finalizada", f"Ação externa {acao_id} terminou com status {novo_status}.")
            if novo_status == "executada" and not ja_finalizada:
                estrategia = acao.get("estrategia")
                registrar_aprendizado(
                    "A abordagem externa foi enviada com sucesso; conversão e receita ainda não foram confirmadas.",
                    estrategia=estrategia,
                    evidencias=[{"acao_externa_id": acao_id, "resultado": resultado}],
                    impacto="envio_confirmado_sem_receita_confirmada",
                    acao="aguardar_feedback",
                    confianca="alta",
                    recomendacao="não contabilizar receita até existir evidência de resposta, venda ou pagamento"
                )
            return {"status": novo_status, "acao_id": acao_id, "run_id": run_id, "resultado": resultado}

        if status in {"FAILED", "CANCELLED"}:
            atualizar_acao_externa(acao_id, "falhou", {
                "run_id": run_id,
                "status_tinyfish": status,
                "erro": dados.get("error"),
                "consultado_em": agora()
            })
            registrar_evento("acao_externa_finalizada", f"Ação externa {acao_id} terminou com status {status}.")
            return {"status": "falhou", "acao_id": acao_id, "run_id": run_id, "erro": dados.get("error")}

        return {
            "status": "executando",
            "acao_id": acao_id,
            "run_id": run_id,
            "status_tinyfish": status
        }

    except Exception as erro:
        return {"status": "erro", "acao_id": acao_id, "run_id": run_id, "erro": str(erro)}
