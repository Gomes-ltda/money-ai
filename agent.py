import time
from datetime import datetime


class MoneyAgent:

    def __init__(self):
        self.ativo = False
        self.ciclo = 0
        self.historico = []

    def registrar(self, tipo, mensagem):

        evento = {
            "data": datetime.utcnow().isoformat(),
            "tipo": tipo,
            "mensagem": mensagem
        }

        self.historico.append(evento)

        print(
            f"[{evento['tipo']}] "
            f"{evento['mensagem']}"
        )

    def observar(self):

        self.registrar(
            "OBSERVAR",
            "Iniciando análise do ambiente."
        )

        return {
            "objetivo": "Gerar receita",
            "status": "analisando"
        }

    def analisar(self, dados):

        self.registrar(
            "ANALISAR",
            f"Analisando situação: {dados}"
        )

        decisao = {
            "acao": "pesquisar_oportunidades",
            "motivo": (
                "Pesquisar atividades econômicas "
                "que possam gerar receita."
            )
        }

        return decisao

    def executar(self, decisao):

        self.registrar(
            "EXECUTAR",
            f"Executando: {decisao['acao']}"
        )

        resultado = {
            "status": "executado",
            "acao": decisao["acao"]
        }

        return resultado

    def aprender(self, resultado):

        self.registrar(
            "APRENDER",
            f"Resultado registrado: {resultado}"
        )

    def ciclo_agente(self):

        self.ciclo += 1

        self.registrar(
            "CICLO",
            f"Iniciando ciclo {self.ciclo}."
        )

        dados = self.observar()

        decisao = self.analisar(dados)

        resultado = self.executar(decisao)

        self.aprender(resultado)

        self.registrar(
            "CICLO",
            f"Ciclo {self.ciclo} concluído."
        )

    def iniciar(self, intervalo=60):

        self.ativo = True

        self.registrar(
            "SISTEMA",
            "Money AI iniciada."
        )

        while self.ativo:

            try:

                self.ciclo_agente()

                time.sleep(intervalo)

            except Exception as erro:

                self.registrar(
                    "ERRO",
                    str(erro)
                )

                time.sleep(intervalo)

    def parar(self):

        self.ativo = False

        self.registrar(
            "SISTEMA",
            "Money AI parada."
        )


if __name__ == "__main__":

    agente = MoneyAgent()

    agente.iniciar(intervalo=60)
