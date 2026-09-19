import time

from ai import analisar_oportunidade

from memory import (
    registrar_evento,
    registrar_resultado,
    registrar_estrategia,
    registrar_ciclo,
    registrar_teste,
    registrar_aprendizado
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

        registrar_evento(
            tipo,
            mensagem
        )

        print(
            f"[{tipo}] {mensagem}"
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

    def extrair_estrategia(self, analise):

        if not isinstance(analise, dict):
            return None

        estrategia = analise.get(
            "estrategia"
        )

        if estrategia:
            return estrategia

        texto = analise.get(
            "analise",
            ""
        )

        if not isinstance(texto, str):
            return None

        marcadores = [
            "Oportunidade 1:",
            "Oportunidade 1 -",
            "Estratégia:"
        ]

        for marcador in marcadores:

            if marcador.lower() in texto.lower():

                partes = texto.split(
                    marcador,
                    1
                )

                if len(partes) == 2:

                    estrategia = partes[1].split(
                        "\n",
                        1
                    )[0].strip()

                    if estrategia:
                        return estrategia[:200]

        return None

    def decidir(self, analise):

        self.registrar(
            "DECIDIR",
            "Definindo a próxima ação."
        )

        if not isinstance(analise, dict):

            return {
                "acao": "aguardar",
                "motivo": "Análise inválida.",
                "analise": analise
            }

        if analise.get("status") != "sucesso":

            return {
                "acao": "aguardar",
                "motivo": (
                    "Não foi possível concluir a análise."
                ),
                "analise": analise
            }

        estrategia = self.extrair_estrategia(
            analise
        )

        return {
            "acao": "testar_estrategia",
            "motivo": (
                "Estratégia identificada pelo Cérebro."
            ),
            "estrategia": estrategia,
            "analise": analise
        }

    def executar(self, decisao):

        self.registrar(
            "EXECUTAR",
            (
                "Enviando decisão ao Executor: "
                f"{decisao.get('acao')}"
            )
        )

        resultado = self.executor.execut
