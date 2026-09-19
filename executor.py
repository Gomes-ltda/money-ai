def executar(self, decisao):

    self.registrar(
        "EXECUTAR",
        f"Enviando decisão ao Executor: {decisao.get('acao')}"
    )

    resultado = self.executor.executar(
        decisao
    )

    self.registrar(
        "EXECUTOR",
        f"Resultado: {resultado}"
    )

    return resultado
