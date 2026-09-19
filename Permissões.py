import json
import os


ARQUIVO_PERMISSOES = "permissions.json"


PERMISSOES_PADRAO = {
    "pesquisar": True,
    "analisar": True,
    "criar_conteudo": True,
    "publicar": False,
    "enviar_mensagens": False,
    "gastar_dinheiro": False,
    "criar_contas": False,
    "movimentar_dinheiro": False
}


def carregar_permissoes():

    if not os.path.exists(ARQUIVO_PERMISSOES):

        salvar_permissoes(PERMISSOES_PADRAO.copy())

        return PERMISSOES_PADRAO.copy()

    try:

        with open(
            ARQUIVO_PERMISSOES,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)

    except Exception:

        return PERMISSOES_PADRAO.copy()


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

    return permissoes.get(
        acao,
        False
    )


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
