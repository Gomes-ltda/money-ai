import json
import os
from datetime import datetime, timezone

try:
    import psycopg
except ImportError:
    psycopg = None


ARQUIVO_MEMORIA = "memory.json"
DATABASE_URL = os.getenv("DATABASE_URL")


def memoria_padrao():
    return {
        "eventos": [],
        "estrategias": [],
        "resultados": [],
        "ciclos": [],
        "testes": [],
        "tarefas": [],
        "aprendizados": [],
        "acoes_externas": [],
        "pagamentos": [],
        "pedidos_clientes": [],
        "leads": [],
        "financeiro": {
            "receita": 0,
            "custos": 0
        }
    }


def garantir_estrutura(memoria):
    padrao = memoria_padrao()

    if not isinstance(memoria, dict):
        memoria = padrao

    for chave, valor in padrao.items():
        if chave not in memoria:
            memoria[chave] = valor

    if not isinstance(memoria.get("financeiro"), dict):
        memoria["financeiro"] = {"receita": 0, "custos": 0}

    memoria["financeiro"].setdefault("receita", 0)
    memoria["financeiro"].setdefault("custos", 0)

    if not isinstance(memoria.get("acoes_externas"), list):
        memoria["acoes_externas"] = []

    if not isinstance(memoria.get("pagamentos"), list):
        memoria["pagamentos"] = []

    if not isinstance(memoria.get("pedidos_clientes"), list):
        memoria["pedidos_clientes"] = []

    if not isinstance(memoria.get("leads"), list):
        memoria["leads"] = []

    return memoria


def agora():
    return datetime.now(timezone.utc).isoformat()


def _usar_banco():
    return bool(DATABASE_URL and psycopg)


def _conectar():
    return psycopg.connect(DATABASE_URL, connect_timeout=10)


def _inicializar_banco():
    if not _usar_banco():
        return False
    try:
        with _conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evolia_memory (
                        id INTEGER PRIMARY KEY,
                        data JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
        return True
    except Exception:
        return False


def _carregar_banco():
    if not _inicializar_banco():
        return None
    try:
        with _conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT data FROM evolia_memory WHERE id = 1")
                linha = cursor.fetchone()

        if linha:
            return garantir_estrutura(linha[0])

        if os.path.exists(ARQUIVO_MEMORIA):
            try:
                with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as arquivo:
                    memoria = garantir_estrutura(json.load(arquivo))
            except Exception:
                memoria = memoria_padrao()
        else:
            memoria = memoria_padrao()

        _salvar_banco(memoria)
        return memoria
    except Exception:
        return None


def _salvar_banco(memoria):
    if not _inicializar_banco():
        return False
    try:
        memoria = garantir_estrutura(memoria)
        with _conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO evolia_memory (id, data, updated_at)
                    VALUES (1, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()
                """, (json.dumps(memoria, ensure_ascii=False),))
        return True
    except Exception:
        return False


def carregar_memoria():
    memoria_banco = _carregar_banco()
    if memoria_banco is not None:
        return memoria_banco

    if not os.path.exists(ARQUIVO_MEMORIA):
        memoria = memoria_padrao()
        salvar_memoria(memoria)
        return memoria

    try:
        with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as arquivo:
            return garantir_estrutura(json.load(arquivo))
    except Exception:
        return memoria_padrao()


def salvar_memoria(memoria):
    memoria = garantir_estrutura(memoria)
    if _usar_banco() and _salvar_banco(memoria):
        return
    with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as arquivo:
        json.dump(memoria, arquivo, ensure_ascii=False, indent=4)


def registrar_evento(tipo, descricao):
    memoria = carregar_memoria()
    evento = {"data": agora(), "tipo": tipo, "descricao": descricao}
    memoria["eventos"].append(evento)
    salvar_memoria(memoria)
    return evento


def registrar_resultado(estrategia, receita=0, custo=0, resultado=None, acao=None, evidencias=None):
    memoria = carregar_memoria()
    if resultado is None:
        resultado = receita - custo
    registro = {
        "data": agora(), "estrategia": estrategia, "acao": acao,
        "receita": receita, "custo": custo, "resultado": resultado,
        "evidencias": evidencias or []
    }
    memoria["resultados"].append(registro)
    memoria["financeiro"]["receita"] += receita
    memoria["financeiro"]["custos"] += custo
    salvar_memoria(memoria)
    return registro


def registrar_estrategia(nome, descricao, status="em_teste"):
    memoria = carregar_memoria()
    estrategia = {"data": agora(), "nome": nome, "descricao": descricao, "status": status}
    memoria["estrategias"].append(estrategia)
    salvar_memoria(memoria)
    return estrategia


def registrar_ciclo(objetivo, localizacao=None, pesquisa=None, analise=None, decisao=None, execucao=None, medicao=None):
    memoria = carregar_memoria()
    ciclo = {
        "data": agora(), "objetivo": objetivo, "localizacao": localizacao,
        "pesquisa": pesquisa, "analise": analise, "decisao": decisao,
        "execucao": execucao, "medicao": medicao
    }
    memoria["ciclos"].append(ciclo)
    salvar_memoria(memoria)
    return ciclo


def registrar_teste(estrategia, plano=None, restricoes=None, execucao=None, receita=0, custo=0, resultado=None, status="em_andamento", ciclo=None):
    memoria = carregar_memoria()
    if resultado is None:
        resultado = receita - custo
    teste = {
        "data": agora(), "ciclo": ciclo, "estrategia": estrategia,
        "plano": plano or {}, "restricoes": restricoes or {}, "execucao": execucao or {},
        "financeiro": {"receita": receita, "custo": custo, "resultado": resultado},
        "status": status
    }
    memoria["testes"].append(teste)
    salvar_memoria(memoria)
    return teste


def registrar_tarefa(tarefa_id, descricao, acao, status="pendente", resultado=None, ciclo=None):
    memoria = carregar_memoria()
    tarefa = {
        "data": agora(), "id": tarefa_id, "descricao": descricao,
        "acao": acao, "status": status, "resultado": resultado, "ciclo": ciclo
    }
    memoria["tarefas"].append(tarefa)
    salvar_memoria(memoria)
    return tarefa


def atualizar_tarefa(tarefa_id, status, resultado=None):
    memoria = carregar_memoria()
    for tarefa in reversed(memoria["tarefas"]):
        if tarefa.get("id") == tarefa_id:
            tarefa["status"] = status
            if resultado is not None:
                tarefa["resultado"] = resultado
            tarefa["atualizada_em"] = agora()
            salvar_memoria(memoria)
            return tarefa
    return None


def registrar_aprendizado(aprendizado, estrategia=None, evidencias=None, impacto=None, acao=None, confianca=None, recomendacao=None):
    memoria = carregar_memoria()
    registro = {
        "data": agora(), "aprendizado": aprendizado, "estrategia": estrategia,
        "acao": acao, "evidencias": evidencias or [], "impacto": impacto,
        "confianca": confianca, "recomendacao": recomendacao
    }
    memoria["aprendizados"].append(registro)
    salvar_memoria(memoria)
    return registro


def registrar_lead(proveniencia, url, canal, nome=None, resumo=None, motivo_aderencia=None,
                   evidencia_publica=None, estrategia=None, nicho=None, problema=None,
                   oferta=None, confianca=None):
    memoria = carregar_memoria()
    leads = memoria.setdefault("leads", [])
    url = str(url or "").strip()
    canal = str(canal or "").strip().lower()
    if not url:
        return None

    for lead in reversed(leads):
        if lead.get("url") == url and lead.get("estrategia") == estrategia:
            lead["atualizado_em"] = agora()
            return lead

    lead = {
        "id": __import__("uuid").uuid4().hex,
        "criado_em": agora(),
        "atualizado_em": agora(),
        "status": "encontrado",
        "proveniencia": proveniencia,
        "url": url,
        "canal": canal,
        "nome": str(nome or "").strip(),
        "resumo": str(resumo or "").strip(),
        "motivo_aderencia": str(motivo_aderencia or "").strip(),
        "evidencia_publica": evidencia_publica or [],
        "estrategia": estrategia,
        "nicho": nicho,
        "problema": problema,
        "oferta": oferta,
        "confianca": confianca
    }
    leads.append(lead)
    salvar_memoria(memoria)
    return lead


def obter_leads(status=None, limite=50):
    leads = carregar_memoria().get("leads", [])
    if status:
        leads = [lead for lead in leads if lead.get("status") == status]
    return leads[-limite:]


def atualizar_lead(lead_id, status=None, **campos):
    memoria = carregar_memoria()
    for lead in reversed(memoria.get("leads", [])):
        if lead.get("id") == lead_id:
            if status is not None:
                lead["status"] = str(status).strip()
            for chave, valor in campos.items():
                if valor is not None:
                    lead[chave] = valor
            lead["atualizado_em"] = agora()
            salvar_memoria(memoria)
            return lead
    return None


def registrar_acao_externa(tipo, alvo=None, canal=None, mensagem=None, estrategia=None, contexto=None):
    memoria = carregar_memoria()
    acao = {
        "id": __import__("uuid").uuid4().hex,
        "data": agora(),
        "tipo": tipo,
        "alvo": alvo,
        "canal": canal,
        "mensagem": mensagem,
        "estrategia": estrategia,
        "contexto": contexto or {},
        "status": "aguardando_autorizacao",
        "autorizada_em": None,
        "executada_em": None,
        "resultado": None
    }
    memoria["acoes_externas"].append(acao)
    salvar_memoria(memoria)
    return acao


def atualizar_acao_externa(acao_id, status, resultado=None):
    memoria = carregar_memoria()
    for acao in reversed(memoria["acoes_externas"]):
        if acao.get("id") == acao_id:
            acao["status"] = status
            if status == "autorizada":
                acao["autorizada_em"] = agora()
            if status in {"executada", "falhou", "cancelada"}:
                acao["executada_em"] = agora()
            if resultado is not None:
                acao["resultado"] = resultado
            salvar_memoria(memoria)
            return acao
    return None


def registrar_feedback_acao_externa(acao_id, resposta=None, interesse=None, venda=False, receita=0, custo=0, observacao=None):
    memoria = carregar_memoria()
    for acao in reversed(memoria["acoes_externas"]):
        if acao.get("id") == acao_id:
            feedback = {"data": agora(), "resposta": resposta, "interesse": interesse, "venda": bool(venda), "receita": float(receita or 0), "custo": float(custo or 0), "observacao": observacao}
            feedbacks = acao.setdefault("feedback", [])
            if venda and any(bool(x.get("venda")) for x in feedbacks):
                return {"erro": "Esta ação já possui uma venda registrada."}
            feedbacks.append(feedback)
            salvar_memoria(memoria)
            if venda:
                registrar_resultado(
                    estrategia=acao.get("estrategia") or "estratégia sem nome",
                    receita=float(receita or 0),
                    custo=float(custo or 0),
                    resultado=float(receita or 0) - float(custo or 0),
                    acao="feedback_venda",
                    evidencias=[{"acao_externa_id": acao_id, "feedback": feedback}]
                )
                registrar_aprendizado("Ação externa gerou uma venda confirmada pelo usuário.", estrategia=acao.get("estrategia"), evidencias=[{"acao_externa_id": acao_id, "feedback": feedback}], impacto="venda_confirmada", acao="repetir_e_testar_variacoes", confianca="alta", recomendacao="avaliar estratégia com base na receita confirmada")
            elif interesse:
                registrar_aprendizado("Ação externa recebeu indicação de interesse registrada pelo usuário.", estrategia=acao.get("estrategia"), evidencias=[{"acao_externa_id": acao_id, "feedback": feedback}], impacto="interesse_confirmado", acao="acompanhar_conversao", confianca="media", recomendacao="aguardar confirmação de venda antes de contabilizar receita")
            return feedback
    return None



def validar_venda_para_cobranca(acao_id):
    memoria = carregar_memoria()
    for acao in reversed(memoria["acoes_externas"]):
        if acao.get("id") == acao_id:
            if acao.get("status") != "executada":
                return {"ok": False, "motivo": "A ação comercial ainda não foi executada."}
            feedbacks = acao.get("feedback", []) or []
            venda = next((x for x in reversed(feedbacks) if bool(x.get("venda"))), None)
            if not venda:
                return {"ok": False, "motivo": "A venda ainda não foi confirmada para esta ação."}
            return {
                "ok": True,
                "acao": acao,
                "feedback": venda,
                "venda_id": f"{acao_id}:venda"
            }
    return {"ok": False, "motivo": "Ação externa não encontrada."}




def registrar_pedido_cliente(nome, email=None, whatsapp=None, instagram=None, servico=None, descricao=None, modo_teste=True):
    import secrets
    import uuid
    memoria = carregar_memoria()
    pedido = {
        "id": uuid.uuid4().hex,
        "token_publico": secrets.token_urlsafe(24),
        "criado_em": agora(),
        "atualizado_em": agora(),
        "nome": str(nome or "").strip(),
        "email": str(email or "").strip().lower(),
        "whatsapp": str(whatsapp or "").strip(),
        "instagram": str(instagram or "").strip(),
        "servico": str(servico or "").strip(),
        "descricao": str(descricao or "").strip(),
        "modo_teste": bool(modo_teste),
        "status": "recebido",
        "proposta": None,
        "entrega": None,
        "historico": [{"data": agora(), "status": "recebido", "observacao": "Solicitação recebida pelo site."}]
    }
    memoria["pedidos_clientes"].append(pedido)
    salvar_memoria(memoria)
    return pedido


def obter_pedidos_clientes(limite=100):
    return carregar_memoria()["pedidos_clientes"][-limite:]


def obter_pedido_publico(token):
    token = str(token or "").strip()
    if not token:
        return None
    for pedido in reversed(carregar_memoria()["pedidos_clientes"]):
        if pedido.get("token_publico") == token:
            return pedido
    return None


def obter_pedido_cliente(pedido_id):
    for pedido in reversed(carregar_memoria()["pedidos_clientes"]):
        if pedido.get("id") == pedido_id:
            return pedido
    return None


def atualizar_pedido_cliente(pedido_id, status=None, proposta=None, entrega=None, observacao=None):
    memoria = carregar_memoria()
    for pedido in reversed(memoria["pedidos_clientes"]):
        if pedido.get("id") == pedido_id:
            if status is not None:
                pedido["status"] = str(status).strip()
            if proposta is not None:
                pedido["proposta"] = proposta
            if entrega is not None:
                pedido["entrega"] = entrega
            pedido["atualizado_em"] = agora()
            pedido.setdefault("historico", []).append({
                "data": agora(),
                "status": pedido.get("status"),
                "observacao": str(observacao or "").strip() or None
            })
            salvar_memoria(memoria)
            return pedido
    return None

def obter_pagamento_por_id(pagamento_id):
    memoria = carregar_memoria()
    for pagamento in reversed(memoria["pagamentos"]):
        if pagamento.get("id") == pagamento_id:
            return pagamento
    return None


def obter_pagamento_por_referencia(referencia):
    memoria = carregar_memoria()
    for pagamento in reversed(memoria["pagamentos"]):
        if pagamento.get("referencia") == referencia:
            return pagamento
    return None


def registrar_pagamento(pagamento):
    memoria = carregar_memoria()
    pagamentos = memoria["pagamentos"]
    pagamento_id = pagamento.get("id")
    if pagamento_id and any(x.get("id") == pagamento_id for x in pagamentos):
        return next(x for x in pagamentos if x.get("id") == pagamento_id)
    pagamentos.append(pagamento)
    salvar_memoria(memoria)
    return pagamento


def atualizar_pagamento(pagamento_id, **campos):
    memoria = carregar_memoria()
    for pagamento in reversed(memoria["pagamentos"]):
        if pagamento.get("id") == pagamento_id:
            pagamento.update({k: v for k, v in campos.items() if v is not None})
            pagamento["atualizado_em"] = agora()
            salvar_memoria(memoria)
            return pagamento
    return None


def obter_pagamentos(limite=50):
    return carregar_memoria()["pagamentos"][-limite:]


def obter_metricas_comerciais(limite=100):
    memoria = carregar_memoria()
    acoes = memoria["acoes_externas"][-limite:]
    metricas = {
        "acoes_preparadas": len(acoes),
        "autorizadas": 0,
        "executadas": 0,
        "falhas": 0,
        "respostas": 0,
        "interesses": 0,
        "vendas": 0,
        "receita_confirmada": 0,
        "custos_confirmados": 0
    }
    por_estrategia = {}
    for acao in acoes:
        status = acao.get("status")
        if status == "autorizada":
            metricas["autorizadas"] += 1
        elif status == "executada":
            metricas["executadas"] += 1
        elif status == "falhou":
            metricas["falhas"] += 1

        estrategia = acao.get("estrategia") or "estratégia sem nome"
        bloco = por_estrategia.setdefault(estrategia, {
            "acoes": 0, "executadas": 0, "respostas": 0,
            "interesses": 0, "vendas": 0, "receita_confirmada": 0,
            "custos_confirmados": 0
        })
        bloco["acoes"] += 1
        if status == "executada":
            bloco["executadas"] += 1

        for feedback in acao.get("feedback", []) or []:
            if feedback.get("resposta"):
                metricas["respostas"] += 1
                bloco["respostas"] += 1
            if feedback.get("interesse"):
                metricas["interesses"] += 1
                bloco["interesses"] += 1
            if feedback.get("venda"):
                metricas["vendas"] += 1
                bloco["vendas"] += 1
                receita = float(feedback.get("receita", 0) or 0)
                custo = float(feedback.get("custo", 0) or 0)
                metricas["receita_confirmada"] += receita
                metricas["custos_confirmados"] += custo
                bloco["receita_confirmada"] += receita
                bloco["custos_confirmados"] += custo

    metricas["por_estrategia"] = por_estrategia
    return metricas


def obter_acoes_externas(status=None, limite=20):
    memoria = carregar_memoria()
    acoes = memoria["acoes_externas"]
    if status:
        acoes = [acao for acao in acoes if acao.get("status") == status]
    return acoes[-limite:]


def obter_historico_estrategia(estrategia):
    memoria = carregar_memoria()
    return {
        "estrategia": estrategia,
        "resultados": [x for x in memoria["resultados"] if x.get("estrategia") == estrategia],
        "testes": [x for x in memoria["testes"] if x.get("estrategia") == estrategia],
        "aprendizados": [x for x in memoria["aprendizados"] if x.get("estrategia") == estrategia]
    }


def obter_ultimos_aprendizados(limite=10):
    return carregar_memoria()["aprendizados"][-limite:]


def avaliar_estrategias(limite_resultados=50):
    memoria = carregar_memoria()
    resultados = memoria["resultados"][-limite_resultados:]
    agrupadas = {}
    for item in resultados:
        nome = item.get("estrategia") or "estratégia_sem_nome"
        agrupadas.setdefault(nome, []).append(item)

    avaliadas = {}
    for nome, itens in agrupadas.items():
        receitas = [float(x.get("receita", 0) or 0) for x in itens]
        custos = [float(x.get("custo", 0) or 0) for x in itens]
        valores = [float(x.get("resultado", 0) or 0) for x in itens]
        positivos = sum(1 for x in valores if x > 0)
        negativos = sum(1 for x in valores if x < 0)
        zeros = sum(1 for x in valores if x == 0)
        consecutivos = 0
        for valor in reversed(valores):
            if valor <= 0:
                consecutivos += 1
            else:
                break
        total_receita, total_custo, total_resultado = sum(receitas), sum(custos), sum(valores)

        if positivos > 0 and total_resultado > 0:
            estado, recomendacao = "sinal_positivo", "continuar"
        elif len(itens) >= 3 and consecutivos >= 3:
            estado, recomendacao = "sinal_negativo", "modificar"
        elif len(itens) >= 2 and negativos > 0 and total_resultado < 0:
            estado, recomendacao = "sinal_negativo", "modificar"
        else:
            estado, recomendacao = "em_teste", "testar_mais"

        avaliadas[nome] = {
            "tentativas": len(itens), "receita_total": total_receita,
            "custo_total": total_custo, "resultado_total": total_resultado,
            "resultados_positivos": positivos, "resultados_negativos": negativos,
            "resultados_zero": zeros,
            "tentativas_consecutivas_sem_resultado_positivo": consecutivos,
            "ultimo_resultado": valores[-1], "estado": estado,
            "recomendacao": recomendacao
        }
    return avaliadas


def obter_contexto_estrategico(limite_resultados=10, limite_testes=10, limite_aprendizados=10):
    memoria = carregar_memoria()
    resultados, testes, aprendizados = (
        memoria["resultados"][-limite_resultados:],
        memoria["testes"][-limite_testes:],
        memoria["aprendizados"][-limite_aprendizados:]
    )
    estrategias = {}
    for item in resultados:
        nome = item.get("estrategia") or "estratégia_sem_nome"
        atual = estrategias.setdefault(nome, {
            "quantidade_resultados": 0, "receita_total": 0,
            "custo_total": 0, "resultado_total": 0, "ultimos_resultados": []
        })
        atual["quantidade_resultados"] += 1
        atual["receita_total"] += item.get("receita", 0) or 0
        atual["custo_total"] += item.get("custo", 0) or 0
        atual["resultado_total"] += item.get("resultado", 0) or 0
        atual["ultimos_resultados"].append({
            "data": item.get("data"), "resultado": item.get("resultado", 0),
            "acao": item.get("acao")
        })
        atual["ultimos_resultados"] = atual["ultimos_resultados"][-3:]
    return {
        "desempenho_por_estrategia": estrategias,
        "avaliacao_de_estrategias": avaliar_estrategias(),
        "testes_recentes": testes,
        "aprendizados_recentes": aprendizados
    }


def obter_resumo():
    memoria = carregar_memoria()
    receita = memoria["financeiro"]["receita"]
    custos = memoria["financeiro"]["custos"]
    return {
        "receita_total": receita, "custos_total": custos,
        "resultado_total": receita - custos,
        "eventos": len(memoria["eventos"]), "estrategias": len(memoria["estrategias"]),
        "resultados": len(memoria["resultados"]), "ciclos": len(memoria["ciclos"]),
        "testes": len(memoria["testes"]), "tarefas": len(memoria["tarefas"]),
        "aprendizados": len(memoria["aprendizados"]),
        "acoes_externas": len(memoria["acoes_externas"]),
        "acoes_externas_pendentes": len([x for x in memoria["acoes_externas"] if x.get("status") == "aguardando_autorizacao"])
    }
