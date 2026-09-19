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

        resultado = self.executor.executar(
            decisao
        )

        self.registrar(
            "EXECUTOR",
            f"Resultado: {resultado}"
        )

        return resultado

    def medir(self, resultado_execucao):

        self.registrar(
            "MEDIR",
            "Medindo o resultado da execução."
        )

        if not isinstance(
            resultado_execucao,
            dict
        ):

            return {
                "receita": 0,
                "custo": 0,
                "resultado": 0,
                "status": "erro"
            }

        receita = resultado_execucao.get(
            "receita",
            0
        )

        custo = resultado_execucao.get(
            "custo_real",
            resultado_execucao.get(
                "custo",
                0
            )
        )

        resultado = resultado_execucao.get(
            "resultado",
            receita - custo
        )

        return {
            "receita": receita,
            "custo": custo,
            "resultado": resultado,
            "status": resultado_execucao.get(
                "status"
            )
        }

    def aprender(
        self,
        estrategia,
        resultado_execucao,
        medicao
    ):

        self.registrar(
            "APRENDER",
            "Registrando o resultado para ciclos futuros."
        )

        if estrategia:

            registrar_resultado(
                estrategia,
                receita=medicao["receita"],
                custo=medicao["custo"],
                resultado=medicao["resultado"]
            )

        else:

            registrar_resultado(
                "Ciclo da Money AI",
                receita=medicao["receita"],
                custo=medicao["custo"],
                resultado=medicao["resultado"]
            )

        if estrategia:

            registrar_aprendizado(
                aprendizado=(
                    "O teste foi executado e seu resultado "
                    "foi registrado para comparação futura."
                ),
                estrategia=estrategia,
                evidencias=[
                    {
                        "status": resultado_execucao.get(
                            "status"
                        ),
                        "receita": medicao["receita"],
                        "custo": medicao["custo"],
                        "resultado": medicao["resultado"]
                    }
                ],
                impacto=(
                    "Aguardar resultados reais de novos "
                    "testes antes de alterar a estratégia."
                )
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

        estrategia = decisao.get(
            "estrategia"
        )

        if estrategia:

            registrar_estrategia(
                nome=estrategia,
                descricao=(
                    "Estratégia identificada pelo "
                    "Cérebro durante o ciclo."
                ),
                status="em_teste"
            )

        resultado_execucao = self.executar(
            decisao
        )

        resultado = self.medir(
            resultado_execucao
        )

        registrar_teste(
            estrategia=estrategia or "Nenhuma estratégia",
            plano=resultado_execucao,
            restricoes=resultado_execucao.get(
                "restricoes",
                {}
            )
            if isinstance(
                resultado_execucao,
                dict
            )
            else {},
            execucao=resultado_execucao,
            receita=resultado["receita"],
            custo=resultado["custo"],
            resultado=resultado["resultado"],
            status=resultado["status"],
            ciclo=self.ciclo
        )

        self.aprender(
            estrategia,
            resultado_execucao,
            resultado
        )

        registrar_ciclo(
            objetivo=self.objetivo,
            localizacao=self.localizacao,
            pesquisa=dados,
            analise=analise,
            decisao=decisao,
            execucao=resultado_execucao,
            medicao=resultado
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
