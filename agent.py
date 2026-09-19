import time
from datetime import datetime

from ai import analisar_oportunidade
from memory import (
    registrar_evento,
    registrar_resultado,
    registrar_estrategia
)
from executor import Executor


class MoneyAgent:

    def __init__(self, objetivo="Gerar receita"):

        self.ativo = False
        self.ciclo = 0
        self.objetivo = objetivo
        self.localizacao = "BR"
        self.executor = Executor()

    def registrar(self, tipo, mensagem):

        evento = {
            "data": datetime.utcnow().isoformat(),
            "tipo": tipo,
            "mensagem": mensagem
        }

        registrar_evento(
            tipo,
            mensagem
        )

        print(
            f"[{evento['tipo']}] "
            f"{evento['mensagem']}"
        )

    def observar(self):

        self.registrar(
            "OBSERVAR",
            "Coletando informações para o próximo ciclo."
        )

        return {
            "objetivo": self.objetivo,
            "localizacao": self.localizacao,
            "ciclo": self.ciclo
        }

    def analisar(self, dados):

        self.registrar(
            "ANALISAR",
            "Enviando informações ao Cérebro."
        )

        analise = analisar_oportunidade(
            dados["objetivo"],
            dados["localizacao"]
        )

        return analise

    def decidir(self, analise):

        self.registrar(
            "DECIDIR",
            "Definindo a próxima ação."
        )

        if analise.get("status") != "sucesso":

            return {
                "acao": "aguardar",
                "motivo": "Não foi possível concluir a análise.",
                "analise": analise
            }

        return {
            "acao": "testar_estrategia",
            "motivo": "Estratégia identificada pelo Cérebro.",
            "analise": analise
        }

    def executar(self, decisao):

        self.registrar(
            "EXECUTAR",
            f"Enviando decisão ao Executor: "
            f"{decisao.get('acao')}"
        )

        resultado = self.executor.executar(
            decisao
        )

        self.registrar(
            "EXECUTOR",
            f"Resultado: {resultado}"
        )

        return resultado

    def medir(self, resultado):

        self.registrar(
            "MEDIR",
            f"Resultado do ciclo: {resultado}"
        )

        medicao = {
            "receita": 0,
            "custo": 0,
            "resultado": 0,
            "status": resultado.get("status")
        }

        return medicao

    def aprender(self, resultado):

        self.registrar(
            "APRENDER",
            "Registrando o resultado para ciclos futuros."
        )

        registrar_resultado(
            "Ciclo da Money AI",
            receita=resultado.get("receita", 0),
            custo=resultado.get("custo", 0),
            resultado=resultado.get("resultado", 0)
        )

    def ciclo_agente(self):

        self.ciclo += 1

        self.registrar(
            "CICLO",
            f"Iniciando ciclo {self.ciclo}."
        )

        dados = self.observar()

        analise = self.analisar(
            dados
        )

        decisao = self.decidir(
            analise
        )

        resultado_execucao = self.executar(
            decisao
        )

        resultado = self.medir(
            resultado_execucao
        )

        self.aprender(
            resultado
        )

        self.registrar(
            "CICLO",
            f"Ciclo {self.ciclo} concluído."
        )

        return {
            "ciclo": self.ciclo,
            "observacao": dados,
            "analise": analise,
            "decisao": decisao,
            "execucao": resultado_execucao,
            "medicao": resultado
        }

    def iniciar(self, intervalo=60):

        self.ativo = True

        self.registrar(
            "SISTEMA",
            "Money AI iniciada."
        )

        while self.ativo:

            try:

                self.ciclo_agente()

                time.sleep(
                    intervalo
                )

            except Exception as erro:

                self.registrar(
                    "ERRO",
                    str(erro)
                )

                time.sleep(
                    intervalo
                )

    def parar(self):

        self.ativo = False

        self.registrar(
            "SISTEMA",
            "Money AI parada."
        )


if __name__ == "__main__":

    agente = MoneyAgent(
        objetivo="Encontrar uma oportunidade de negócio"
    )

    resultado = agente.ciclo_agente()

    print(resultado)
