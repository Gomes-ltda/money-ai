import json
import os


ARQUIVO_PERMISSOES = "permissions.json"


PERMISSOES_PADRAO = {
    # Ações internas autônomas
    "pesquisar": True,
    "analisar": True,
    "criar_oferta": True,
    "criar_proposta": True,
    "criar_conteudo": True,
    "testar_estrategia": True,
    "registrar_resultado": True,
    "criar_tarefa": True,

    # Ações externas que continuam bloqueadas
    "publicar": False,
    "enviar_mensagens": False,
    "gastar_dinheiro": False,
    "criar_contas": False,
    "movimentar_dinheiro": False
}


def carregar_permissoes():
    permissoes = PERMISSOES_PADRAO.copy()

    if not os.path.exists(ARQUIVO_PERMISSOES):
        salvar_permissoes(permissoes)
        return permissoes

    try:
        with open(
            ARQUIVO_PERMISSOES,
            "r",
            encoding="utf-8"
        ) as arquivo:
            existentes = json.load(arquivo)

        alterou = False

        for acao, valor_padrao in PERMISSOES_PADRAO.items():
            if acao not in existentes:
                existentes[acao] = valor_padrao
                alterou = True

        if alterou:
            salvar_permissoes(existentes)

        return existentes

    except Exception:
        return permissoes


def salvar_permissoes(permissoes):
    with open(
        ARQUIVO_PERMISSOES,
        "w",
        encoding="utf-8"
    ) as arquivo:
        json.dump(
            permissoes,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def pode_executar(acao):
    permissoes = carregar_permissoes()
    return permissoes.get(acao, False)


def solicitar_permissao(acao):
    permissoes = carregar_permissoes()

    if acao not in permissoes:
        return {
            "permitido": False,
            "motivo": "Ação não cadastrada."
        }

    if permissoes[acao]:
        return {
            "permitido": True,
            "motivo": "Ação autorizada."
        }

    return {
        "permitido": False,
        "motivo": "Ação exige autorização do usuário."
    }


def alterar_permissao(acao, permitido):
    permissoes = carregar_permissoes()

    permissoes[acao] = bool(permitido)

    salvar_permissoes(permissoes)

    return permissoes
