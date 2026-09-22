from flask import Flask, request, jsonify, render_template_string
import os

from ai import analisar_oportunidade, analisar_pedido_cliente
from agent import executar_ciclo, executar_ciclo_pedido
from memory import obter_acoes_externas, atualizar_acao_externa, registrar_feedback_acao_externa, obter_metricas_comerciais
from external import iniciar_acao_autorizada, consultar_acao_externa
from pagamentos import criar_cobranca_pix, criar_order_pix_teste, validar_webhook, processar_webhook, sincronizar_pagamento
from pedido_fluxo import publicar_proposta, aceitar_proposta, criar_pagamento_pedido, sincronizar_pedido_pagamento, registrar_entrega, ciclo_pedido_resumo, transicionar_pedido
from memory import obter_pagamentos, atualizar_pagamento, validar_venda_para_cobranca, obter_pagamento_por_id, registrar_pedido_cliente, obter_pedidos_clientes, obter_pedido_publico, atualizar_pedido_cliente, registrar_reclamacao, obter_reclamacoes, atualizar_reclamacao


app = Flask(__name__)
APPROVAL_TOKEN = os.getenv("EVOLIA_APPROVAL_TOKEN", "").strip()
PANEL_PASSWORD = os.getenv("EVOLIA_PANEL_PASSWORD", "").strip()


def validar_token():
    if not APPROVAL_TOKEN:
        return False
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip() == APPROVAL_TOKEN
    return False


ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Evolia AI</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 820px; margin: 0 auto; padding: 28px 18px 50px; color: #111; background: #fff; }
        .topo { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 28px; }
        .marca { font-size: 34px; font-weight: 700; margin: 0; }
        .status { display: inline-flex; align-items: center; gap: 8px; border: 1px solid #ccc; border-radius: 999px; padding: 8px 12px; font-size: 14px; }
        .ponto { width: 9px; height: 9px; border-radius: 50%; background: #222; }
        .subtitulo { color: #555; margin-top: 6px; }
        .painel-ciclo { border: 1px solid #d4d4d4; border-radius: 14px; padding: 22px; margin-bottom: 24px; }
        .painel-ciclo h2 { margin: 0 0 8px; }
        .objetivo-interno { color: #444; margin: 0 0 20px; }
        .etapas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 18px 0 22px; }
        .etapa { border: 1px solid #ddd; border-radius: 10px; padding: 13px; min-height: 66px; }
        .etapa strong { display: block; margin-bottom: 5px; }
        .etapa span { color: #666; font-size: 13px; }
        .botao-principal { width: 100%; padding: 14px 18px; border: 1px solid #111; border-radius: 9px; background: #111; color: #fff; font-size: 16px; cursor: pointer; }
        .botao-principal:disabled { opacity: .55; cursor: wait; }
        #resultado { white-space: pre-wrap; margin-top: 18px; line-height: 1.5; }
        .info { color: #666; font-size: 13px; margin-top: 12px; }
        input { width: 100%; padding: 10px; margin-top: 8px; box-sizing: border-box; }
        button { margin-top: 12px; padding: 12px 20px; cursor: pointer; }
        @media (max-width: 620px) { .topo { align-items: flex-start; flex-direction: column; } .etapas { grid-template-columns: 1fr 1fr; } }
        @media (max-width: 420px) { .etapas { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div id="loginPainel" style="max-width:420px;margin:80px auto;padding:25px;border:1px solid #ccc;border-radius:10px">
        <h1>Evolia AI</h1>
        <h2>Acesso restrito</h2>
        <p>Este painel é privado. Informe a senha/chave de acesso.</p>
        <input id="senhaPainel" type="password" placeholder="Senha do painel" autocomplete="current-password">
        <button onclick="entrarPainel()">Entrar</button>
        <div id="loginStatus" style="margin-top:12px"></div>
    </div>
    <div id="painel" style="display:none">
    <div class="topo">
        <div>
            <h1 class="marca">Evolia AI</h1>
            <div class="subtitulo">Painel de operação e acompanhamento</div>
        </div>
        <div class="status"><span class="ponto"></span><span id="statusGeral">Pronta</span></div>
    </div>

    <section class="painel-ciclo">
        <h2>Ciclo da Evolia</h2>
        <p class="objetivo-interno">
            A Evolia trabalha para identificar, testar e melhorar formas legítimas de geração de receita.
        </p>
        <div class="etapas">
            <div class="etapa"><strong>1. Observar</strong><span>Coleta contexto e sinais relevantes.</span></div>
            <div class="etapa"><strong>2. Pesquisar</strong><span>Busca oportunidades e informações atuais.</span></div>
            <div class="etapa"><strong>3. Analisar</strong><span>Compara viabilidade, esforço e retorno.</span></div>
            <div class="etapa"><strong>4. Decidir</strong><span>Seleciona o próximo experimento.</span></div>
            <div class="etapa"><strong>5. Executar</strong><span>Prepara ou executa ações autorizadas.</span></div>
            <div class="etapa"><strong>6. Aprender</strong><span>Registra resultados e ajusta o próximo ciclo.</span></div>
        </div>
        <button id="botaoCiclo" class="botao-principal" onclick="executarCiclo()">Iniciar ciclo da EVOLIA</button>
        <button id="botaoProspeccao" class="botao-principal" style="margin-top:10px;background:#fff;color:#111;border-color:#111" onclick="prospectarClientes()">Procurar clientes agora</button>
        <div class="info">O ciclo geral trabalha a estratégia. A prospecção usa o mesmo ciclo para procurar oportunidades de clientes e preparar abordagens para sua aprovação.</div>
        <div id="resultado"></div>
    </section>
    <hr>
    <h2>Ações externas pendentes</h2>
    <p>Estas ações foram preparadas pela Evolia e aguardam sua autorização.</p>
    <div id="statusAcao"></div>
    <input id="tokenAutorizacao" type="password" placeholder="Token de autorização">
    <button onclick="carregarAcoes()">Carregar ações</button>
    <div id="acoes"></div>
    <hr>
    <h2>Resultados comerciais</h2>
    <p>Use este painel para registrar o que aconteceu depois de uma abordagem executada.</p>
    <div id="historicoAcoes"></div>
    <hr>
    <h2>Pedidos de clientes</h2>
    <p>Cada solicitação entra no ciclo da EVOLIA. O sistema pesquisa, analisa e prepara a proposta; comunicação com o cliente continua dependendo da sua autorização.</p>
    <div id="pedidosClientes"></div>
<hr>
    <h2>Pagamentos</h2>
    <div id="pagamentos"></div>
    <button onclick="criarTestePix()">Criar teste Pix (sandbox)</button>
    <div id="testePix"></div>

    </div>
    <script>
        async function entrarPainel() {
            const senha = document.getElementById("senhaPainel").value;
            const status = document.getElementById("loginStatus");
            if (!senha.trim()) {
                status.textContent = "Informe a senha.";
                return;
            }
            status.textContent = "Verificando acesso...";
            try {
                const resposta = await fetch("/painel-login", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({senha: senha})
                });
                const dados = await resposta.json();
                if (!resposta.ok || !dados.token) {
                    status.textContent = dados.erro || "Senha inválida.";
                    return;
                }
                sessionStorage.setItem("evolia_token", dados.token);
                document.getElementById("loginPainel").style.display = "none";
                document.getElementById("painel").style.display = "block";
                document.getElementById("tokenAutorizacao").value = dados.token;
                iniciarAtualizacaoAutomatica();
            } catch (erro) {
                status.textContent = "Não foi possível verificar o acesso.";
            }
        }

        function sairPainel() {
            sessionStorage.removeItem("evolia_token");
            document.getElementById("painel").style.display = "none";
            document.getElementById("loginPainel").style.display = "block";
            document.getElementById("senhaPainel").value = "";
            document.getElementById("loginStatus").textContent = "";
        }

        function obterToken() {
            return document.getElementById("tokenAutorizacao").value.trim() || sessionStorage.getItem("evolia_token") || "";
        }

        function mostrarResultadoCiclo(dados) {
            const ciclo = dados.ciclo_memoria || {};
            const decisao = dados.decisao_ia?.decisao || dados.decisao || {};
            const medicao = dados.medicao || {};
            const aprendizado = ciclo.aprendizado || dados.decisao_ia?.aprendizado_esperado || "-";
            const proxima = ciclo.proxima_acao || decisao.proxima_acao_ciclo || dados.decisao_ia?.proximo_passo || "-";
            const estrategia = decisao.estrategia || "-";
            const acao = decisao.acao_executor || decisao.acao || "-";
            const resultado = Number(medicao.resultado || 0).toLocaleString("pt-BR", {style:"currency", currency:"BRL"});
            document.getElementById("resultado").innerHTML =
                "<div style='border:1px solid #ccc;border-radius:12px;padding:16px'>" +
                "<b>Estratégia:</b> " + estrategia + "<br>" +
                "<b>Ação executada:</b> " + acao + "<br>" +
                "<b>Resultado financeiro:</b> " + resultado + "<br><br>" +
                "<b>O que a EVOLIA aprendeu:</b><br>" + aprendizado + "<br><br>" +
                "<b>Próximo passo:</b><br>" + proxima +
                "</div>" +
                "<details style='margin-top:14px'><summary>Ver dados completos do ciclo</summary><pre style='white-space:pre-wrap;margin-top:10px'>" +
                JSON.stringify(dados, null, 2).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;") +
                "</pre></details>";
        }

        async function prospectarClientes() {
            const resultado = document.getElementById("resultado");
            const botao = document.getElementById("botaoProspeccao");
            const statusGeral = document.getElementById("statusGeral");
            const token = obterToken();
            if (!token) {
                resultado.textContent = "Token de autorização não encontrado. Entre novamente no painel.";
                statusGeral.textContent = "Acesso necessário";
                return;
            }
            resultado.textContent = "A EVOLIA está procurando oportunidades de clientes...";
            statusGeral.textContent = "Prospectando";
            botao.disabled = true;
            try {
                const resposta = await fetch("/ciclo", {
                    method: "POST",
                    headers: {"Content-Type": "application/json", "Authorization": "Bearer " + token},
                    body: JSON.stringify({
                        objetivo: "Encontrar potenciais clientes reais para os serviços da Evolia, identificar uma necessidade pública verificável, preparar uma abordagem comercial personalizada e não enviar nenhuma mensagem sem autorização."
                    })
                });
                const dados = await resposta.json();
                if (!resposta.ok) {
                    resultado.textContent = dados.erro || "Erro durante a prospecção.";
                    statusGeral.textContent = "Erro";
                    return;
                }
                mostrarResultadoCiclo(dados);
                statusGeral.textContent = "Prospecção concluída";
                carregarAcoes();
            } catch (erro) {
                resultado.textContent = "Erro de conexão com a Evolia.";
                statusGeral.textContent = "Erro";
            } finally {
                botao.disabled = false;
            }
        }

        async function executarCiclo() {
            const resultado = document.getElementById("resultado");
            const botao = document.getElementById("botaoCiclo");
            const statusGeral = document.getElementById("statusGeral");
            const token = obterToken();

            if (!token) {
                resultado.textContent = "Token de autorização não encontrado. Entre novamente no painel.";
                statusGeral.textContent = "Acesso necessário";
                return;
            }

            resultado.textContent = "Iniciando ciclo: observando, pesquisando e analisando...";
            statusGeral.textContent = "Executando";
            botao.disabled = true;

            try {
                const resposta = await fetch("/ciclo", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + token
                    },
                    body: JSON.stringify({})
                });

                const dados = await resposta.json();
                if (!resposta.ok) {
                    resultado.textContent = dados.erro || "Erro ao executar ciclo.";
                    statusGeral.textContent = "Erro";
                    return;
                }

                mostrarResultadoCiclo(dados);
                statusGeral.textContent = "Ciclo concluído";
            } catch (erro) {
                resultado.textContent = "Erro de conexão com a Evolia.";
                statusGeral.textContent = "Erro";
            } finally {
                botao.disabled = false;
            }
        }
        async function carregarAcoes() {
            const resultado = document.getElementById("acoes");
            const token = obterToken();
            if (!token) {
                resultado.innerHTML = "<p>Informe o token de autorização.</p>";
                return;
            }
            sessionStorage.setItem("evolia_token", token);
            const resposta = await fetch("/acoes-pendentes", {headers: {"Authorization": "Bearer " + token}});
            const dados = await resposta.json();
            if (!resposta.ok) {
                resultado.innerHTML = "<p>" + (dados.erro || "Token inválido.") + "</p>";
                return;
            }
            if (!dados.acoes || dados.acoes.length === 0) {
                resultado.innerHTML = "<p>Nenhuma ação aguardando autorização.</p>";
                return;
            }
            resultado.innerHTML = dados.acoes.map(acao =>
                "<div style='border:1px solid #ccc;padding:15px;margin:12px 0;border-radius:8px'>" +
                "<b>Alvo:</b> " + (acao.alvo || "-") + "<br>" +
                "<b>Canal:</b> " + (acao.canal || "-") +
                "<p><b>Mensagem:</b></p><pre style='white-space:pre-wrap'>" + (acao.mensagem || "") + "</pre>" +
                "<button onclick=" + JSON.stringify("decidirAcao('" + acao.id + "','autorizar')") + ">Autorizar</button> " +
                "<button onclick=" + JSON.stringify("decidirAcao('" + acao.id + "','recusar')") + ">Recusar</button></div>"
            ).join("");
        }
        async function decidirAcao(id, decisao) {
            const token = obterToken();
            const resposta = await fetch("/acoes/" + encodeURIComponent(id) + "/" + decisao, {method:"POST", headers: {"Authorization": "Bearer " + token}});
            const dados = await resposta.json();
            document.getElementById("statusAcao").textContent = dados.mensagem || JSON.stringify(dados);
            carregarAcoes();
        }
        async function carregarAcoesEmAndamento() {
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/acoes-em-andamento", {headers: {"Authorization": "Bearer " + token}});
                if (!resposta.ok) return;
                const dados = await resposta.json();
                const emAndamento = dados.acoes || [];
                if (emAndamento.length > 0) {
                    document.getElementById("statusAcao").textContent = "Há " + emAndamento.length + " ação(ões) externa(s) em execução. A Evolia está acompanhando o resultado.";
                }
            } catch (erro) {}
        }
        async function sincronizarPagamentosAutomaticamente() {
            const token = obterToken();
            if (!token) return;
            try {
                await fetch("/pagamentos/sincronizar-pendentes", {
                    method: "POST",
                    headers: {"Authorization": "Bearer " + token}
                });
            } catch (erro) {}
        }
        async function sincronizarPedidosAutomaticamente() {
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/pedidos-clientes", {headers: {"Authorization": "Bearer " + token}});
                const dados = await resposta.json();
                if (!resposta.ok) return;
                for (const pedido of (dados.pedidos || [])) {
                    if (pedido.status === "aguardando_pagamento" && pedido.pagamento_id) {
                        await fetch("/pedidos-clientes/"+encodeURIComponent(pedido.id)+"/sincronizar", {
                            method:"POST", headers:{"Authorization":"Bearer "+token}
                        });
                    }
                }
            } catch(e) {}
        }

        async function carregarReclamacoes() {
            const box=document.getElementById("reclamacoes"), token=obterToken(); if(!token)return;
            try{const resposta=await fetch("/reclamacoes",{headers:{"Authorization":"Bearer "+token}}); const dados=await resposta.json(); if(!resposta.ok)return;
                const itens=(dados.reclamacoes||[]).slice().reverse();
                if(!itens.length){box.innerHTML="<p>Nenhuma reclamação registrada.</p>";return;}
                box.innerHTML=itens.slice(0,20).map(r=>"<div style='border:1px solid #ccc;padding:16px;margin:12px 0;border-radius:10px'><b>"+escPedido(r.assunto||"Outro")+"</b> · "+escPedido(r.status||"aberta")+"<p><b>Cliente:</b> "+escPedido(r.nome||"-")+"<br><b>Pedido:</b> "+escPedido(r.pedido_id||"-")+"<br><b>Contato:</b> "+escPedido(r.contato||"-")+"</p><p style='white-space:pre-wrap'>"+escPedido(r.descricao||"")+"</p>"+(r.resposta?"<p><b>Resposta:</b> "+escPedido(r.resposta)+"</p>":"")+"<button onclick='resolverReclamacao("+JSON.stringify(r.id)+")'>Marcar como resolvida</button></div>").join("");
            }catch(e){}
        }
        async function resolverReclamacao(id){
            const token=obterToken(); if(!token)return; const resposta=prompt("Informe a resposta/resolução para o cliente:"); if(!resposta||!resposta.trim())return;
            const r=await fetch("/reclamacoes/"+encodeURIComponent(id),{method:"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"resolvida",resposta:resposta,resolucao:resposta})});
            const d=await r.json(); if(!r.ok){alert(d.erro||"Não foi possível atualizar a reclamação.");return;} carregarReclamacoes();
        }

        async function carregarPagamentos() {
            const resultado = document.getElementById("pagamentos");
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/pagamentos", {headers: {"Authorization": "Bearer " + token}});
                const dados = await resposta.json();
                if (!resposta.ok) {
                    resultado.innerHTML = "<p>" + (dados.erro || "Não foi possível carregar pagamentos.") + "</p>";
                    return;
                }
                const pagamentos = dados.pagamentos || [];
                if (!pagamentos.length) {
                    resultado.innerHTML = "<p>Nenhum pagamento registrado.</p>";
                    return;
                }
                resultado.innerHTML = pagamentos.slice().reverse().slice(0, 20).map(p => {
                    const valor = Number(p.valor || 0).toLocaleString("pt-BR", {style:"currency", currency:"BRL"});
                    return "<div style='border:1px solid #ccc;padding:15px;margin:12px 0;border-radius:8px'>" +
                        "<b>Status:</b> " + (p.status || "-") + "<br>" +
                        "<b>Valor:</b> " + valor + "<br>" +
                        "<b>Descrição:</b> " + (p.descricao || "-") + "<br>" +
                        "<b>Referência:</b> " + (p.referencia || "-") + "<br>" +
                        "<b>Comprador:</b> " + (p.email_comprador || "-") +
                        (p.ticket_url ? "<br><a href='" + p.ticket_url + "' target='_blank' rel='noopener'>Abrir cobrança</a>" : "") +
                        "</div>";
                }).join("");
            } catch (erro) {
                resultado.innerHTML = "<p>Erro ao carregar pagamentos.</p>";
            }
        }
        async function criarTestePix() {
            const resultado = document.getElementById("testePix");
            const token = obterToken();
            if (!token) {
                resultado.innerHTML = "<p>Informe o token de autorização primeiro.</p>";
                return;
            }
            resultado.textContent = "Criando order Pix de teste...";
            try {
                const resposta = await fetch("/pagamentos/teste-pix", {
                    method: "POST",
                    headers: {"Authorization": "Bearer " + token}
                });
                const dados = await resposta.json();
                if (!resposta.ok) {
                    resultado.innerHTML = "<p>" + (dados.erro || "Falha no teste.") + "</p>";
                    return;
                }
                const p = dados.pagamento || {};
                const qr = p.qr_code || "";
                resultado.innerHTML =
                    "<p><b>Teste criado:</b> " + (p.valor || 0).toLocaleString("pt-BR", {style:"currency",currency:"BRL"}) + "</p>" +
                    (p.ticket_url ? "<p><a href='" + p.ticket_url + "' target='_blank' rel='noopener'>Abrir instruções do Pix de teste</a></p>" : "") +
                    (qr ? "<p><b>Pix copia e cola:</b></p><textarea readonly style='width:100%;height:110px'>" + qr + "</textarea>" : "") +
                    "<p>Este teste usa o sandbox do Mercado Pago e não movimenta dinheiro real.</p>";
                carregarPagamentos();
            } catch (erro) {
                resultado.textContent = "Erro ao criar teste: " + erro;
            }
        }
        async function carregarHistorico() {
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/acoes-historico", {headers: {"Authorization": "Bearer " + token}});
                const dados = await resposta.json();
                if (!resposta.ok) return;
                const metricas = dados.metricas || {};
                document.getElementById("historicoAcoes").innerHTML =
                    "<p>Ações executadas: " + (metricas.executadas || 0) +
                    " | Respostas: " + (metricas.respostas || 0) +
                    " | Interesses: " + (metricas.interesses || 0) +
                    " | Vendas: " + (metricas.vendas || 0) +
                    " | Receita confirmada: " +
                    Number(metricas.receita_confirmada || 0).toLocaleString("pt-BR", {style:"currency", currency:"BRL"}) +
                    "</p>";
            } catch (erro) {}
        }
        function escPedido(x) {
            return String(x == null ? "" : x).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
        }
        const statusPedidoLabel = {
            "recebido":"Recebido",
            "em_analise":"Em análise",
            "proposta_preparada":"Proposta preparada pela EVOLIA",
            "proposta_enviada":"Proposta publicada",
            "aguardando_pagamento":"Aguardando pagamento",
            "em_execucao":"Em execução",
            "entregue":"Entregue",
            "cancelado":"Encerrado"
        };
        async function carregarPedidosClientes() {
            const box = document.getElementById("pedidosClientes");
            const token = obterToken();
            if (!token) return;
            try {
                const resposta = await fetch("/pedidos-clientes", {headers: {"Authorization": "Bearer " + token}});
                const dados = await resposta.json();
                if (!resposta.ok) return;
                const pedidos = (dados.pedidos || []).slice().reverse();
                if (!pedidos.length) { box.innerHTML = "<p>Nenhum pedido recebido ainda.</p>"; return; }

                const etapas = ["recebido","em_analise","proposta_preparada","proposta_enviada","aguardando_pagamento","em_execucao","entregue"];
                const labels = {
                    "recebido":"Recebido",
                    "em_analise":"Em análise",
                    "proposta_preparada":"Proposta preparada",
                    "proposta_enviada":"Proposta publicada",
                    "aguardando_pagamento":"Aguardando pagamento",
                    "em_execucao":"Em execução",
                    "entregue":"Entregue",
                    "cancelado":"Encerrado"
                };

                box.innerHTML = pedidos.slice(0,20).map(p => {
                    const prop = p.proposta || {};
                    const escopo = Array.isArray(prop.escopo) ? prop.escopo : [];
                    const perguntas = Array.isArray(prop.perguntas) ? prop.perguntas : [];
                    const valor = prop.valor != null ? "R$ " + Number(prop.valor).toLocaleString("pt-BR",{minimumFractionDigits:2}) : "A definir";
                    const status = p.status || "recebido";
                    const ciclo = p.ciclo || {};
                    const propPublicada = ["proposta_enviada","aguardando_pagamento","em_execucao","entregue"].includes(status);
                    const pagamento = p.pagamento_id ? "Pagamento vinculado" : "Sem pagamento";
                    let progress = "<div style='display:flex;gap:4px;flex-wrap:wrap;margin:12px 0'>" +
                        etapas.map(et => "<span style='padding:5px 8px;border-radius:999px;border:1px solid #ddd;font-size:11px;background:" +
                            (et===status ? "#111;color:#fff" : (etapas.indexOf(et)<etapas.indexOf(status) ? "#eee" : "#fff")) + "'>" + labels[et] + "</span>").join("") +
                        "</div>";

                    let botoes = "";
                    if (["recebido","em_analise"].includes(status)) {
                        botoes += "<button onclick='executarCicloPedido(\\\""+p.id+"\\\")'>Executar ciclo da EVOLIA</button>";
                    }
                    if (status === "proposta_preparada" && prop.texto) {
                        botoes += " <button onclick='publicarPropostaPedido(\\\""+p.id+"\\\")'>Autorizar e publicar proposta</button>";
                    }
                    if (status === "aguardando_pagamento") {
                        botoes += " <button onclick='sincronizarPedido(\\\""+p.id+"\\\")'>Sincronizar pagamento</button>";
                    }
                    if (status === "em_execucao") {
                        botoes += " <button onclick='registrarEntregaPedido(\\\""+p.id+"\\\")'>Registrar entrega</button>";
                    }

                    return "<div style='border:1px solid #ccc;padding:18px;margin:12px 0;border-radius:10px'>" +
                    "<div style='font-size:18px'><b>"+escPedido(p.nome)+"</b> · "+escPedido(labels[status] || status)+(p.modo_teste?" · TESTE":"")+"</div>" +
                    progress +
                    "<p><b>Serviço:</b> "+escPedido(p.servico)+"<br><b>Contato:</b> "+escPedido(p.email || p.whatsapp || p.instagram || "-")+
                    "<br><b>Pedido:</b> "+escPedido(p.descricao)+"</p>" +
                    "<p class='info'><b>Etapa atual:</b> "+escPedido(ciclo.etapa_atual || status)+" · <b>"+escPedido(pagamento)+"</b></p>" +
                    (prop.texto ? "<div style='background:#f6f6f6;border-radius:10px;padding:14px;margin-top:12px'>" +
                        "<b>Proposta gerada pela EVOLIA</b><p style='white-space:pre-wrap'>"+escPedido(prop.texto)+"</p>" +
                        "<p><b>Valor sugerido:</b> "+escPedido(valor)+"<br><b>Prazo:</b> "+escPedido(prop.prazo || "A definir")+"</p>" +
                        (escopo.length ? "<p><b>Escopo:</b><br>• "+escopo.map(escPedido).join("<br>• ")+"</p>" : "") +
                        (perguntas.length ? "<p><b>Pontos que ainda precisam de confirmação:</b><br>• "+perguntas.map(escPedido).join("<br>• ")+"</p>" : "") +
                        "</div>" : "<p style='color:#666'>A EVOLIA ainda não preparou uma proposta para este pedido.</p>") +
                    "<div style='margin-top:14px'>" + botoes +
                    " <a href='/pedido/"+encodeURIComponent(p.token_publico)+"' target='_blank'>Abrir página do cliente</a></div>" +
                    (status === "proposta_preparada" ? "<p class='info'>A proposta foi preparada. O próximo avanço exige sua autorização para publicação.</p>" : "") +
                    (status === "proposta_enviada" ? "<p class='info'>Aguardando o cliente aceitar a proposta.</p>" : "") +
                    (status === "aguardando_pagamento" ? "<p class='info'>O cliente aceitou. A cobrança pode ser gerada na página privada.</p>" : "") +
                    (status === "em_execucao" ? "<p class='info'>Pagamento confirmado. A execução do serviço é a etapa operacional atual.</p>" : "") +
                    "</div>";
                }).join("");
            } catch(e) {}
        }
        async function executarCicloPedido(id) {
            const token=obterToken();
            if (!token) return;
            const resposta=await fetch("/pedidos-clientes/"+encodeURIComponent(id)+"/ciclo",{method:"POST",headers:{"Authorization":"Bearer "+token}});
            const dados=await resposta.json();
            if(!resposta.ok){alert(dados.erro||"Não foi possível executar o ciclo do pedido.");return;}
            carregarPedidosClientes();
        }
        async function publicarPropostaPedido(id) {
            const token=obterToken();
            if (!token) return;
            if (!confirm("Publicar a proposta na página privada do cliente?")) return;
            const resposta=await fetch("/pedidos-clientes/"+encodeURIComponent(id)+"/publicar-proposta",{method:"POST",headers:{"Authorization":"Bearer "+token}});
            const dados=await resposta.json();
            if(!resposta.ok){alert(dados.erro||"Não foi possível publicar a proposta.");return;}
            carregarPedidosClientes();
        }
        async function sincronizarPedido(id) {
            const token = obterToken();
            if (!token) return;
            const resposta = await fetch("/pedidos-clientes/"+encodeURIComponent(id)+"/sincronizar", {
                method:"POST", headers:{"Authorization":"Bearer "+token}
            });
            const dados = await resposta.json();
            if (!resposta.ok) { alert(dados.erro || "Não foi possível sincronizar."); return; }
            carregarPedidosClientes();
        }

        async function registrarEntregaPedido(id) {
            const token = obterToken();
            if (!token) return;
            const texto = prompt("Descreva a entrega disponibilizada ao cliente:");
            if (!texto || !texto.trim()) return;
            const url = prompt("URL da entrega (opcional):") || "";
            const resposta = await fetch("/pedidos-clientes/"+encodeURIComponent(id)+"/entrega", {
                method:"POST",
                headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},
                body:JSON.stringify({texto:texto,url:url})
            });
            const dados = await resposta.json();
            if (!resposta.ok) { alert(dados.erro || "Não foi possível registrar a entrega."); return; }
            carregarPedidosClientes();
        }

        let intervaloAcoes = null;
        function iniciarAtualizacaoAutomatica() {
            if (intervaloAcoes) clearInterval(intervaloAcoes);
            if (obterToken()) {
                carregarAcoes();
                carregarPedidosClientes();
                sincronizarPedidosAutomaticamente();
                carregarAcoesEmAndamento();
                carregarHistorico();
                carregarReclamacoes();
                sincronizarPagamentosAutomaticamente();
                carregarPagamentos();
                intervaloAcoes = setInterval(() => {
                    if (obterToken()) {
                        carregarAcoes();
                        carregarPedidosClientes();
                        sincronizarPedidosAutomaticamente();
                        carregarAcoesEmAndamento();
                        carregarHistorico();
                        carregarReclamacoes();
                        sincronizarPagamentosAutomaticamente();
                        carregarPagamentos();
                    }
                }, 10000);
            }
        }
        window.addEventListener("load", function() {
            sessionStorage.removeItem("evolia_token");
            document.getElementById("loginPainel").style.display = "block";
            document.getElementById("painel").style.display = "none";
        });
        document.getElementById("tokenAutorizacao").addEventListener("change", iniciarAtualizacaoAutomatica);
    </script>
</body>
</html>
"""


PUBLIC_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Evolia AI — serviços digitais sob medida.">
<title>Evolia AI — Serviços digitais</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;color:#111;background:#f6f7f9;line-height:1.55}
.wrap{max-width:1100px;margin:auto;padding:0 20px}
header{background:#111;color:#fff;padding:18px 0}
header .wrap{display:flex;justify-content:space-between;align-items:center;gap:20px}
.logo{font-size:24px;font-weight:800}
.nav a{color:#fff;text-decoration:none;margin-left:18px;font-size:14px}
.hero{padding:78px 0 68px;background:#fff}
.eyebrow{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#666}
.hero h1{font-size:clamp(38px,6vw,64px);line-height:1.02;letter-spacing:-2px;margin:14px 0 20px;max-width:780px}
.hero p{font-size:19px;max-width:720px;color:#555;margin:0 0 24px}
.btn{display:inline-block;background:#111;color:#fff;text-decoration:none;padding:14px 21px;border-radius:10px;font-weight:700;border:0;cursor:pointer}
.btn.sec{background:#fff;color:#111;border:1px solid #ccc}
section{padding:64px 0}
h2{font-size:32px;letter-spacing:-.7px;margin:0 0 12px}
.section-intro{color:#666;max-width:700px;margin:0 0 28px}
.grid,.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.card,.step,.form-card{background:#fff;border:1px solid #e1e2e5;border-radius:18px;padding:25px;box-shadow:0 8px 30px rgba(0,0,0,.04)}
.card h3{margin-top:0;font-size:20px}
.card p,.step p{color:#666}
.price{font-size:14px;font-weight:700;margin-top:20px}
.form-card{max-width:760px}
label{display:block;font-weight:700;font-size:14px;margin:16px 0 7px}
input,textarea,select{width:100%;padding:13px;border:1px solid #ccc;border-radius:10px;font:inherit;background:#fff}
textarea{min-height:130px;resize:vertical}
.small{font-size:13px;color:#777}
.result{margin-top:16px;padding:16px;border-radius:12px;background:#f1f2f4}
.cta{background:#111;color:#fff;border-radius:22px;padding:36px}
.cta p{color:#ccc}
footer{background:#111;color:#aaa;padding:30px 0}
@media(max-width:760px){.grid,.steps{grid-template-columns:1fr}header .wrap{align-items:flex-start}.nav a{margin-left:10px}.hero{padding-top:58px}}
</style>
</head>
<body>
<header><div class="wrap"><div class="logo">Evolia AI</div><nav class="nav"><a href="#servicos">Serviços</a><a href="#como-funciona">Como funciona</a><a href="#solicitar">Solicitar</a><a href="#meus-pedidos">Meus pedidos</a></nav></div></header>
<main>
<section class="hero"><div class="wrap">
<div class="eyebrow">Serviços digitais sob medida</div>
<h1>Você explica o problema. A Evolia organiza a solução.</h1>
<p>Solicite um serviço, explique o que precisa e receba uma proposta antes da execução. Nesta fase, o site também pode ser usado para testes reais.</p>
<a class="btn" href="#solicitar">Solicitar orçamento</a>
</div></section>
<section id="servicos"><div class="wrap">
<h2>O que podemos fazer</h2>
<p class="section-intro">Serviços pensados para demandas práticas de comunicação, pesquisa e organização digital.</p>
<div class="grid">
<div class="card"><h3>Textos comerciais</h3><p>Mensagens de abordagem, propostas, respostas a clientes e roteiros de conversão.</p><div class="price">Sob orçamento</div></div>
<div class="card"><h3>Pesquisa e organização</h3><p>Levantamento de informações, organização de dados e síntese de conteúdo.</p><div class="price">Sob orçamento</div></div>
<div class="card"><h3>Solução sob medida</h3><p>Descreva uma necessidade específica e avaliamos o que pode ser entregue.</p><div class="price">Sob orçamento</div></div>
</div></div></section>
<section id="como-funciona"><div class="wrap">
<h2>Como funciona</h2>
<div class="steps">
<div class="step"><strong>1. Você solicita</strong><p>Explique o que precisa e informe um meio de contato.</p></div>
<div class="step"><strong>2. Avaliamos</strong><p>Organizamos o pedido e definimos escopo, prazo e preço.</p></div>
<div class="step"><strong>3. Entregamos</strong><p>Após a confirmação, o resultado fica disponível para você pelo próprio site.</p></div>
</div></div></section>
<section id="meus-pedidos"><div class="wrap"><div class="form-card"><h2>Meus pedidos</h2><p class="section-intro">Pedidos solicitados neste dispositivo ficam salvos aqui para acompanhamento.</p><div id="listaMeusPedidos"><p class="small">Nenhum pedido salvo neste dispositivo.</p></div></div></div></section><section id="solicitar"><div class="wrap">
<div class="form-card">
<h2>Solicitar orçamento</h2>
<p class="section-intro">Preencha o formulário. Ao enviar, você receberá um link privado para acompanhar o pedido.</p>
<form id="pedidoForm" onsubmit="enviarPedido(event)">
<label>Nome</label><input id="nome" required maxlength="100" placeholder="Seu nome ou empresa">
<label>E-mail</label><input id="email" type="email" maxlength="160" placeholder="voce@exemplo.com">
<label>WhatsApp</label><input id="whatsapp" maxlength="30" placeholder="(00) 00000-0000">
<label>Instagram (opcional)</label><input id="instagram" maxlength="80" placeholder="@seuusuario">
<label>O que você precisa?</label>
<select id="servico" required><option value="">Selecione</option><option>Textos comerciais</option><option>Pesquisa e organização</option><option>Solução sob medida</option><option>Outro</option></select>
<label>Descreva o pedido</label><textarea id="descricao" required maxlength="4000" placeholder="Explique o que você precisa e qual resultado espera."></textarea>
<p class="small">Não envie senhas, documentos sensíveis ou dados bancários pelo formulário.</p>
<button class="btn" type="submit">Enviar solicitação</button>
</form>
<div id="pedidoResultado"></div>
</div></div></section>
<section><div class="wrap"><div class="cta">
<h2>Quer testar a operação?</h2><p>Faça uma solicitação real e acompanhe o atendimento pelo link gerado após o envio.</p>
<a class="btn sec" href="#solicitar">Fazer um teste</a>
</div></div></section>
</main>
<footer><div class="wrap">Evolia AI · Serviços digitais</div></footer>
<script>
function carregarMeusPedidos(){const b=document.getElementById("listaMeusPedidos");if(!b)return;let p=[];try{p=JSON.parse(localStorage.getItem("evolia_pedidos")||"[]")}catch(e){};b.innerHTML=p.length?p.map(x=>"<div style=\"border:1px solid #ddd;border-radius:12px;padding:14px;margin:10px 0\"><strong>Pedido "+x.id+"</strong><p class=\"small\">Solicitado em "+new Date(x.criado_em).toLocaleString("pt-BR")+"</p><a class=\"btn\" href=\""+x.url+"\">Acompanhar pedido</a></div>").join(""):"<p class=\"small\">Nenhum pedido salvo neste dispositivo.</p>"}
async function enviarPedido(event){
 event.preventDefault();
 const box=document.getElementById("pedidoResultado");
 box.className="result"; box.textContent="Enviando solicitação...";
 const contato=(document.getElementById("email").value+" "+document.getElementById("whatsapp").value+" "+document.getElementById("instagram").value).trim();
 if(!contato){box.textContent="Informe pelo menos um meio de contato.";return;}
 try{
  const r=await fetch("/solicitar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
   nome:document.getElementById("nome").value,email:document.getElementById("email").value,
   whatsapp:document.getElementById("whatsapp").value,instagram:document.getElementById("instagram").value,
   servico:document.getElementById("servico").value,descricao:document.getElementById("descricao").value,modo_teste:true
  })});
  const d=await r.json();
  if(!r.ok){box.textContent=d.erro||"Não foi possível enviar o pedido.";return;}
  try{const pedidos=JSON.parse(localStorage.getItem("evolia_pedidos")||"[]"); pedidos.unshift({id:d.pedido_id,url:d.url_publica,criado_em:new Date().toISOString()}); localStorage.setItem("evolia_pedidos",JSON.stringify(pedidos.slice(0,20)));}catch(e){}
  carregarMeusPedidos();
  box.innerHTML="<strong>Pedido recebido.</strong><p><a href='"+d.url_publica+"'>Abrir acompanhamento do pedido</a></p><p class='small'>Pedido: "+d.pedido_id+"</p>";
  document.getElementById("pedidoForm").reset();
 }catch(e){box.textContent="Erro de conexão. Tente novamente.";}
}
carregarMeusPedidos();
</script>
</body>
</html>
"""



@app.route("/solicitar", methods=["POST"])
def solicitar():
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    email = str(dados.get("email", "")).strip()
    whatsapp = str(dados.get("whatsapp", "")).strip()
    instagram = str(dados.get("instagram", "")).strip()
    servico = str(dados.get("servico", "")).strip()
    descricao = str(dados.get("descricao", "")).strip()

    if not nome:
        return jsonify({"erro": "Informe seu nome ou empresa."}), 400
    if not servico:
        return jsonify({"erro": "Selecione um serviço."}), 400
    if not descricao:
        return jsonify({"erro": "Descreva o que você precisa."}), 400
    if not any([email, whatsapp, instagram]):
        return jsonify({"erro": "Informe pelo menos um meio de contato."}), 400
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        return jsonify({"erro": "Informe um e-mail válido."}), 400

    pedido = registrar_pedido_cliente(
        nome=nome, email=email, whatsapp=whatsapp, instagram=instagram,
        servico=servico, descricao=descricao, modo_teste=bool(dados.get("modo_teste", True))
    )

    # O pedido é registrado primeiro e a resposta é devolvida imediatamente.
    # O ciclo da EVOLIA continua pelo processamento operacional, sem bloquear o formulário do cliente.
    url_publica = request.host_url.rstrip("/") + "/pedido/" + pedido["token_publico"]
    return jsonify({
        "status": "recebido",
        "pedido_id": pedido["id"],
        "url_publica": url_publica,
        "ciclo": {
            "status": "pendente",
            "proposta_preparada": False
        }
    }), 201


@app.route("/pedido/<token>")
def pedido_publico(token):
    pedido = obter_pedido_publico(token)
    if not pedido:
        return "<!doctype html><html lang='pt-BR'><meta name='viewport' content='width=device-width,initial-scale=1'><body style='font-family:Arial;max-width:700px;margin:60px auto;padding:20px'><h1>Pedido não encontrado</h1><p>Verifique o link recebido.</p></body></html>", 404

    status = pedido.get("status", "recebido")
    labels = {
        "recebido":"Solicitação recebida",
        "em_analise":"Em análise",
        "proposta_preparada":"Proposta em preparação",
        "proposta_enviada":"Proposta disponível para sua decisão",
        "aguardando_pagamento":"Aguardando pagamento",
        "em_execucao":"Em execução",
        "entregue":"Entrega disponível",
        "cancelado":"Pedido encerrado"
    }
    proposta = pedido.get("proposta") or {}
    entrega = pedido.get("entrega") or {}
    proposta_publicada = status in {"proposta_enviada", "aguardando_pagamento", "em_execucao", "entregue"}

    nome_seguro = str(pedido.get("nome","")).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    servico_seguro = str(pedido.get("servico","")).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    texto = str(proposta.get("texto","")).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
    entrega_texto = str(entrega.get("texto","")).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    proposta_html = ""
    if proposta.get("texto") and proposta_publicada:
        valor = proposta.get("valor")
        valor_html = ("<p><strong>Valor:</strong> R$ " + str(valor) + "</p>") if valor is not None else ""
        prazo_html = ("<p><strong>Prazo:</strong> " + str(proposta.get("prazo")) + "</p>") if proposta.get("prazo") else ""
        proposta_html = "<div style='background:#f5f6f8;border-radius:14px;padding:18px;margin-top:20px'><h2>Proposta</h2><p>"+texto+"</p>"+valor_html+prazo_html+"</div>"

    acao_html = ""
    if status == "proposta_enviada":
        if proposta.get("valor") is not None:
            acao_html = """
            <div style='margin-top:20px;padding:18px;border:1px solid #ddd;border-radius:14px'>
              <h2>Decisão</h2>
              <p>Se a proposta estiver de acordo, você pode aceitá-la. O próximo passo será a cobrança.</p>
              <button onclick="aceitarProposta()" style='background:#111;color:#fff;border:0;border-radius:10px;padding:13px 18px;cursor:pointer'>Aceitar proposta</button>
              <div id='acaoStatus' style='margin-top:12px'></div>
            </div>"""
    elif status == "aguardando_pagamento":
        acao_html = """
        <div style='margin-top:20px;padding:18px;border:1px solid #ddd;border-radius:14px'>
          <h2>Pagamento</h2>
          <p>A proposta foi aceita. O pagamento é o próximo passo.</p>
          <button onclick="gerarPagamento()" style='background:#111;color:#fff;border:0;border-radius:10px;padding:13px 18px;cursor:pointer'>Gerar Pix</button>
          <div id='acaoStatus' style='margin-top:12px'></div>
        </div>"""
    elif status == "em_execucao":
        acao_html = "<div style='margin-top:20px;padding:18px;border-radius:14px;background:#f5f6f8'><strong>Pagamento confirmado.</strong><p>A EVOLIA está na etapa de execução.</p></div>"
    elif status == "entregue":
        acao_html = "<div style='margin-top:20px;padding:18px;border-radius:14px;background:#eef7f0'><strong>Entrega concluída.</strong></div>"

    entrega_html = ""
    if entrega.get("texto"):
        entrega_html = "<div style='background:#eef7f0;border-radius:14px;padding:18px;margin-top:20px'><h2>Entrega</h2><div style='white-space:pre-wrap'>"+entrega_texto+"</div>"
        if entrega.get("url"):
            entrega_html += "<p><a href='"+str(entrega.get("url"))+"' target='_blank' rel='noopener'>Abrir resultado</a></p>"
        entrega_html += "</div>"

    return """<!doctype html><html lang='pt-BR'><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Evolia AI — Pedido</title></head>
<body style='margin:0;background:#f5f6f8;font-family:Arial,sans-serif;color:#111'><main style='max-width:760px;margin:0 auto;padding:40px 20px'>
<div style='background:#111;color:#fff;border-radius:18px;padding:24px'><strong style='font-size:24px'>Evolia AI</strong><p style='margin-bottom:0'>Acompanhamento do pedido</p></div>
<div style='background:#fff;border:1px solid #ddd;border-radius:18px;padding:24px;margin-top:18px'>
<p style='color:#666'>Olá, """ + nome_seguro + """."</p>
<h1 style='font-size:30px'>""" + labels.get(status,status) + """</h1>
<p><strong>Serviço:</strong> """ + servico_seguro + """</p>
""" + proposta_html + acao_html + entrega_html + """
<div style='margin-top:24px;padding:18px;border:1px solid #ddd;border-radius:14px;background:#fff8f0'>
<strong>Problema com o pedido?</strong><p style='color:#666'>Se algo saiu diferente do esperado, você pode registrar uma reclamação diretamente por este link.</p>
<button onclick="abrirReclamacao()" style='background:#111;color:#fff;border:0;border-radius:10px;padding:12px 16px;cursor:pointer'>Registrar reclamação</button>
<div id='reclamacaoBox' style='display:none;margin-top:16px'><label>Assunto</label>
<select id='reclamacaoAssunto' style='width:100%;padding:12px;border:1px solid #ccc;border-radius:10px'><option>Atraso</option><option>Problema na entrega</option><option>Problema no serviço</option><option>Valor/cobrança</option><option>Outro</option></select>
<label style='display:block;margin:12px 0 7px'>Descreva o problema</label><textarea id='reclamacaoDescricao' maxlength='4000' style='width:100%;min-height:120px;padding:12px;border:1px solid #ccc;border-radius:10px' placeholder='Explique o que aconteceu.'></textarea>
<button onclick="enviarReclamacao()" style='margin-top:10px;background:#111;color:#fff;border:0;border-radius:10px;padding:12px 16px;cursor:pointer'>Enviar reclamação</button>
<div id='reclamacaoStatus' style='margin-top:12px'></div></div></div><p style='color:#777;font-size:13px;margin-top:28px'>Este link é privado. Não compartilhe.</p>
</div></main>
<script>
function abrirReclamacao(){document.getElementById('reclamacaoBox').style.display='block';}
async function enviarReclamacao(){
 const box=document.getElementById('reclamacaoStatus'); const descricao=document.getElementById('reclamacaoDescricao').value.trim();
 if(!descricao){box.textContent='Descreva o problema antes de enviar.';return;} box.textContent='Enviando reclamação...';
 try{
  const r=await fetch('/pedido/""" + token + """/reclamacao',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({assunto:document.getElementById('reclamacaoAssunto').value,descricao:descricao})});
  const d=await r.json(); if(!r.ok){box.textContent=d.erro||'Não foi possível registrar a reclamação.';return;}
  box.textContent='Reclamação registrada. Número: '+d.reclamacao_id; document.getElementById('reclamacaoDescricao').value='';
 }catch(e){box.textContent='Erro de conexão.';}
}
async function aceitarProposta(){
 const box=document.getElementById('acaoStatus'); box.textContent='Registrando aceite...';
 try{
  const r=await fetch('/pedido/""" + token + """/aceitar',{method:'POST',headers:{'Content-Type':'application/json'}});
  const d=await r.json(); if(!r.ok){box.textContent=d.erro||'Não foi possível registrar o aceite.';return;}
  location.reload();
 }catch(e){box.textContent='Erro de conexão.';}
}
async function gerarPagamento(){
 const box=document.getElementById('acaoStatus'); box.textContent='Gerando cobrança Pix...';
 try{
  const r=await fetch('/pedido/""" + token + """/pagamento',{method:'POST',headers:{'Content-Type':'application/json'}});
  const d=await r.json(); if(!r.ok){box.textContent=d.erro||'Não foi possível gerar a cobrança.';return;}
  const p=d.pagamento||{}; let html='<p>Cobrança criada.</p>';
  if(p.ticket_url) html+='<p><a href="'+p.ticket_url+'" target="_blank" rel="noopener">Abrir instruções do Pix</a></p>';
  if(p.qr_code) html+='<textarea readonly style="width:100%;height:100px">'+p.qr_code+'</textarea>';
  box.innerHTML=html;
 }catch(e){box.textContent='Erro de conexão.';}
}
</script></body></html>"""

@app.route("/pedido/<token>/reclamacao", methods=["POST"])
def criar_reclamacao_publica(token):
    pedido = obter_pedido_publico(token)
    if not pedido:
        return jsonify({"erro": "Pedido não encontrado."}), 404
    dados = request.get_json(silent=True) or {}
    assunto = str(dados.get("assunto") or "Outro").strip()
    descricao = str(dados.get("descricao") or "").strip()
    if not descricao:
        return jsonify({"erro": "Descreva o problema."}), 400
    reclamacao = registrar_reclamacao(
        pedido_id=pedido["id"], token_publico=token, nome=pedido.get("nome"),
        contato=pedido.get("email") or pedido.get("whatsapp") or pedido.get("instagram") or "",
        assunto=assunto, descricao=descricao
    )
    return jsonify({"status":"registrada","reclamacao_id":reclamacao["id"]}), 201

@app.route("/reclamacoes")
def listar_reclamacoes():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify({"reclamacoes": obter_reclamacoes()})

@app.route("/reclamacoes/<reclamacao_id>", methods=["POST"])
def resolver_reclamacao(reclamacao_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    dados = request.get_json(silent=True) or {}
    status = str(dados.get("status") or "").strip()
    if status not in {"em_analise","resolvida","encerrada"}:
        return jsonify({"erro": "Status de reclamação inválido."}), 400
    reclamacao = atualizar_reclamacao(reclamacao_id, status=status, resposta=dados.get("resposta"), resolucao=dados.get("resolucao"))
    if not reclamacao:
        return jsonify({"erro": "Reclamação não encontrada."}), 404
    return jsonify({"status":"atualizada","reclamacao":reclamacao})

@app.route("/pedidos-clientes")
def pedidos_clientes():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify({"pedidos": obter_pedidos_clientes()})


@app.route("/pedidos-clientes/<pedido_id>/ciclo", methods=["POST"])
def ciclo_pedido(pedido_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return jsonify({"erro": "Pedido não encontrado."}), 404
    resultado = executar_ciclo_pedido(pedido_id)
    if resultado.get("status") == "proposta_preparada":
        return jsonify(resultado), 200
    if resultado.get("status") == "aguardando_cerebro":
        return jsonify(resultado), 503
    return jsonify(resultado), 500


@app.route("/pedidos-clientes/<pedido_id>/publicar-proposta", methods=["POST"])
def publicar_proposta_pedido(pedido_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    resultado = publicar_proposta(pedido_id)
    return jsonify(resultado), (200 if resultado.get("ok") else 409)


@app.route("/pedidos-clientes/<pedido_id>/ciclo-resumo")
def resumo_ciclo_pedido(pedido_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    resumo = ciclo_pedido_resumo(pedido_id)
    if not resumo:
        return jsonify({"erro": "Pedido não encontrado."}), 404
    return jsonify(resumo)


@app.route("/pedido/<token>/aceitar", methods=["POST"])
def aceitar_pedido_publico(token):
    pedido = obter_pedido_publico(token)
    if not pedido:
        return jsonify({"erro": "Pedido não encontrado."}), 404
    resultado = aceitar_proposta(pedido.get("id"))
    return jsonify(resultado), (200 if resultado.get("ok") else 409)


@app.route("/pedido/<token>/pagamento", methods=["POST"])
def pagamento_pedido_publico(token):
    pedido = obter_pedido_publico(token)
    if not pedido:
        return jsonify({"erro": "Pedido não encontrado."}), 404
    resultado = criar_pagamento_pedido(pedido.get("id"))
    return jsonify(resultado), (200 if resultado.get("ok") else 409)


@app.route("/pedidos-clientes/<pedido_id>/sincronizar", methods=["POST"])
def sincronizar_pedido(pedido_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    resultado = sincronizar_pedido_pagamento(pedido_id)
    return jsonify(resultado), (200 if resultado.get("ok") else 409)


@app.route("/pedidos-clientes/<pedido_id>/entrega", methods=["POST"])
def entregar_pedido(pedido_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    dados = request.get_json(silent=True) or {}
    resultado = registrar_entrega(pedido_id, dados.get("texto"), dados.get("url"))
    return jsonify(resultado), (200 if resultado.get("ok") else 409)


@app.route("/pedidos-clientes/<pedido_id>/analisar", methods=["POST"])
def analisar_pedido(pedido_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    pedido = obter_pedido_cliente(pedido_id)
    if not pedido:
        return jsonify({"erro": "Pedido não encontrado."}), 404

    resultado = analisar_pedido_cliente(pedido)
    if resultado.get("status") != "sucesso":
        return jsonify(resultado), 503

    analise = resultado.get("analise") or {}
    proposta = {
        "texto": analise.get("proposta_cliente") or analise.get("resumo") or "",
        "valor": analise.get("valor_sugerido"),
        "prazo": analise.get("prazo_sugerido"),
        "escopo": analise.get("escopo") or [],
        "nao_incluido": analise.get("nao_incluido") or [],
        "perguntas": analise.get("perguntas") or [],
        "justificativa_preco": analise.get("justificativa_preco"),
        "riscos": analise.get("riscos") or [],
        "confianca": analise.get("confianca")
    }
    atualizado = atualizar_pedido_cliente(
        pedido_id,
        status="em_analise",
        proposta=proposta,
        observacao="Pedido analisado pela Evolia; proposta aguarda revisão/publicação."
    )
    return jsonify({
        "status": "analisado",
        "analise": analise,
        "pedido": atualizado,
        "fontes_utilizadas": resultado.get("fontes_utilizadas", [])
    }), 200

@app.route("/pedidos-clientes/<pedido_id>", methods=["POST"])
def atualizar_pedido(pedido_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    dados = request.get_json(silent=True) or {}
    if "status" in dados:
        return jsonify({
            "erro": "O status do pedido não é editável manualmente. Use o ciclo da EVOLIA ou a ação específica da etapa."
        }), 409
    proposta = dados.get("proposta")
    entrega = dados.get("entrega")
    pedido = atualizar_pedido_cliente(
        pedido_id,
        proposta=proposta if isinstance(proposta, dict) else None,
        entrega=entrega if isinstance(entrega, dict) else None,
        observacao=dados.get("observacao")
    )
    if not pedido:
        return jsonify({"erro": "Pedido não encontrado."}), 404
    return jsonify({"status": "atualizado", "pedido": pedido})


@app.route("/")
def home():
    return render_template_string(PUBLIC_HTML)


@app.route("/painel")
def painel():
    return render_template_string(ADMIN_HTML)


@app.route("/painel-login", methods=["POST"])
def painel_login():
    dados = request.get_json(silent=True) or {}
    senha = str(dados.get("senha", "")).strip()

    credencial = PANEL_PASSWORD or APPROVAL_TOKEN
    if not credencial:
        return jsonify({"erro": "Acesso do painel não configurado no servidor."}), 503

    if not senha or senha != credencial:
        return jsonify({"erro": "Senha inválida."}), 401

    return jsonify({"status": "autorizado", "token": APPROVAL_TOKEN})


@app.route("/painel-status")
def painel_status():
    if not validar_token():
        return jsonify({"erro": "Não autorizado."}), 401
    return jsonify({"status": "autorizado"})


@app.route("/health")
def health():
    return jsonify({"status": "online", "nome": "Evolia AI"})


@app.route("/acoes-em-andamento")
def acoes_em_andamento():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    acoes = obter_acoes_externas(status="executando", limite=50)
    resultados = [consultar_acao_externa(acao.get("id")) for acao in acoes]
    return jsonify({"acoes": resultados})


@app.route("/acoes-pendentes")
def acoes_pendentes():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    acoes = obter_acoes_externas(status="aguardando_autorizacao", limite=50)
    validas = [
        acao for acao in acoes
        if (acao.get("alvo") or "").strip()
        and (acao.get("mensagem") or "").strip()
        and ((acao.get("contexto") or {}).get("url_alvo") or "").startswith(("https://", "http://"))
    ]
    return jsonify({"acoes": validas[:20]})


@app.route("/acoes/<acao_id>/<decisao>", methods=["POST"])
def decidir_acao(acao_id, decisao):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    if decisao not in {"autorizar", "recusar"}:
        return jsonify({"erro": "Decisão inválida."}), 400
    acao = next((x for x in obter_acoes_externas(limite=100) if x.get("id") == acao_id), None)
    if not acao:
        return jsonify({"erro": "Ação não encontrada."}), 404
    if acao.get("status") != "aguardando_autorizacao":
        return jsonify({"erro": "Esta ação já foi processada."}), 409
    if decisao == "autorizar":
        contexto = acao.get("contexto") or {}
        if not (contexto.get("url_alvo") or "").startswith(("https://", "http://")):
            return jsonify({"erro": "Esta ação ainda não possui uma URL de destino válida. Ela não pode ser executada."}), 400

        atualizar_acao_externa(acao_id, "autorizada", {"origem": "interface_usuario"})
        execucao = iniciar_acao_autorizada(acao_id)

        if execucao.get("status") == "executando":
            return jsonify({"status": "executando", "mensagem": "Ação autorizada e execução externa iniciada.", "execucao": execucao})

        return jsonify({"status": execucao.get("status", "falhou"), "mensagem": "Ação autorizada, mas a execução não foi iniciada.", "execucao": execucao}), 502

    atualizar_acao_externa(acao_id, "cancelada", {"origem": "interface_usuario"})
    return jsonify({"status": "cancelada", "mensagem": "Ação recusada e cancelada."})


@app.route("/acoes-historico")
def acoes_historico():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    acoes = obter_acoes_externas(limite=100)
    concluidas = [x for x in acoes if x.get("status") in {"executada", "falhou", "cancelada"}]
    return jsonify({"acoes": concluidas[-30:], "metricas": obter_metricas_comerciais()})


@app.route("/acoes/<acao_id>/feedback", methods=["POST"])
def feedback_acao(acao_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    dados = request.get_json(silent=True) or {}
    interesse = dados.get("interesse")
    venda = bool(dados.get("venda", False))
    try:
        receita = float(dados.get("receita", 0) or 0)
        custo = float(dados.get("custo", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Receita e custo devem ser números."}), 400
    if receita < 0 or custo < 0:
        return jsonify({"erro": "Receita e custo não podem ser negativos."}), 400
    feedback = registrar_feedback_acao_externa(acao_id, resposta=str(dados.get("resposta", "")).strip() or None, interesse=str(interesse).strip() if interesse is not None else None, venda=venda, receita=receita, custo=custo, observacao=str(dados.get("observacao", "")).strip() or None)
    if feedback is None:
        return jsonify({"erro": "Ação externa não encontrada."}), 404
    if isinstance(feedback, dict) and feedback.get("erro"):
        return jsonify(feedback), 409
    return jsonify({"status": "registrado", "feedback": feedback})


@app.route("/acoes/<acao_id>/status")
def status_acao(acao_id):
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify(consultar_acao_externa(acao_id))


@app.route("/pagamentos/sincronizar-pendentes", methods=["POST"])
def pagamentos_sincronizar_pendentes():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    cron_token = os.getenv("EVOLIA_CRON_TOKEN", "").strip()
    if not validar_token() and (not cron_token or token != cron_token):
        return jsonify({"erro": "Não autorizado."}), 401

    pendentes = [p for p in obter_pagamentos(limite=200) if p.get("status") in {"aguardando_pagamento", "processando", "pendente"}]
    resultados = [sincronizar_pagamento(pagamento.get("id")) for pagamento in pendentes]
    return jsonify({"status": "sincronizado", "quantidade": len(resultados), "resultados": resultados})


@app.route("/pagamentos/<pagamento_id>/sincronizar", methods=["POST"])
def pagamento_sincronizar(pagamento_id):
    if not validar_token():
        return jsonify({"erro": "Não autorizado."}), 401
    resultado = sincronizar_pagamento(pagamento_id)
    if resultado.get("status") == "nao_encontrado":
        return jsonify(resultado), 404
    if resultado.get("status") == "indisponivel":
        return jsonify(resultado), 503
    return jsonify(resultado)


@app.route("/pagamentos/<pagamento_id>", methods=["GET"])
def pagamento_detalhe(pagamento_id):
    if not validar_token():
        return jsonify({"erro": "Não autorizado."}), 401
    pagamento = obter_pagamento_por_id(pagamento_id)
    if not pagamento:
        return jsonify({"erro": "Pagamento não encontrado."}), 404
    return jsonify({"pagamento": pagamento})


@app.route("/pagamentos", methods=["GET"])
def listar_pagamentos():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    return jsonify({"pagamentos": obter_pagamentos()})


@app.route("/pagamentos/pix", methods=["POST"])
def criar_pagamento_pix():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401

    dados = request.get_json(silent=True) or {}
    try:
        valor = float(dados.get("valor", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor inválido."}), 400

    if valor <= 0:
        return jsonify({"erro": "O valor deve ser maior que zero."}), 400

    email = str(dados.get("email", "")).strip()
    if not email:
        return jsonify({"erro": "Informe o e-mail do comprador para gerar a cobrança Pix."}), 400

    acao_id = str(dados.get("acao_id", "")).strip()
    if not acao_id:
        return jsonify({"erro": "Informe a ação comercial que originou esta cobrança."}), 400

    venda = validar_venda_para_cobranca(acao_id)
    if not venda.get("ok"):
        return jsonify({"erro": venda.get("motivo", "Venda não confirmada.")}), 409

    referencia = str(dados.get("referencia", "")).strip() or ("venda-" + acao_id[:32])
    resultado = criar_cobranca_pix(
        valor=valor,
        descricao=str(dados.get("descricao", "Serviço Evolia")).strip() or "Serviço Evolia",
        referencia=referencia,
        email=email,
        acao_id=acao_id
    )
    if resultado.get("status") == "criado":
        pagamento = resultado.get("pagamento") or {}
        estrategia = str(dados.get("estrategia", "")).strip() or None
        if estrategia and pagamento.get("id"):
            atualizar_pagamento(pagamento["id"], estrategia=estrategia)
            pagamento["estrategia"] = estrategia
    return jsonify(resultado), (200 if resultado.get("status") == "criado" else 400)


@app.route("/pagamentos/teste-pix", methods=["POST"])
def pagamento_teste_pix():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    resultado = criar_order_pix_teste()
    return jsonify(resultado), (200 if resultado.get("status") == "criado" else 400)


@app.route("/pagamentos/webhook", methods=["POST"])
def pagamentos_webhook():
    dados = request.get_json(silent=True) or {}
    data_id = request.args.get("data.id") or ((dados.get("data") or {}).get("id"))
    if not validar_webhook(request.headers, data_id):
        return jsonify({"erro": "Assinatura do webhook inválida."}), 401
    resultado = processar_webhook(dados, data_id)
    return jsonify(resultado), 200


@app.route("/ciclo-autonomo", methods=["POST"])
def ciclo_autonomo():
    """Executa um ciclo operacional sem depender do painel, protegido por token de automação."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    cron_token = os.getenv("EVOLIA_CRON_TOKEN", "").strip()
    if not cron_token or token != cron_token:
        return jsonify({"erro": "Não autorizado."}), 401

    dados = request.get_json(silent=True) or {}
    objetivo = str(dados.get("objetivo", "Gerar receita de forma legítima e sustentável: pesquisar mercado, validar oportunidades, preparar abordagens e acompanhar o funil comercial.")).strip()
    localizacao = str(dados.get("localizacao", "Brasil")).strip() or "Brasil"

    try:
        resultado = executar_ciclo(objetivo, localizacao)
        return jsonify(resultado)
    except Exception as erro:
        return jsonify({"status": "erro", "erro": str(erro)}), 500


@app.route("/ciclo", methods=["POST"])
def ciclo():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    dados = request.get_json(silent=True) or {}
    objetivo = str(dados.get("objetivo", "Gerar receita de forma legítima e sustentável")).strip() or "Gerar receita de forma legítima e sustentável"
    localizacao = str(dados.get("localizacao", "Brasil")).strip() or "Brasil"

    try:
        resultado = executar_ciclo(objetivo, localizacao)
        return jsonify(resultado)
    except Exception as erro:
        return jsonify({"status": "erro", "erro": str(erro)}), 500


@app.route("/analisar", methods=["POST"])
def analisar():
    if not validar_token():
        return jsonify({"erro": "Token de autorização inválido ou não configurado."}), 401
    dados = request.get_json(silent=True) or {}
    objetivo = str(dados.get("objetivo", "")).strip()
    localizacao = str(dados.get("localizacao", "")).strip()

    if not objetivo:
        return jsonify({"erro": "Informe um objetivo."}), 400
    if not localizacao:
        return jsonify({"erro": "Informe sua cidade e estado."}), 400

    try:
        resultado = analisar_oportunidade(objetivo, localizacao)
        return jsonify(resultado)
    except Exception as erro:
        return jsonify({"status": "erro", "erro": str(erro)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
