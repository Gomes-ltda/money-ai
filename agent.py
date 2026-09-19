import re
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

        # 1. Se o Cérebro já entregar a estratégia
        # estruturada, usamos diretamente.
        estrategia = analise.get(
            "estrategia"
        )

        if estrategia:
            return estrategia.strip()

        texto = analise.get(
            "analise",
            ""
        )

        if not isinstance(texto, str):
            return None

        # -------------------------------------------------
        # 2. Procurar a decisão explícita do Cérebro.
        #
        # Exemplo:
        #
        # "A Money AI deve selecionar a Oportunidade 2
        # (Automação de Soluções com IA para PMEs)..."
        # -------------------------------------------------

        padroes_selecao = [

            r"selecionar\s+a\s+Oportunidade\s*(\d+)",
            r"selecionar\s+a\s+oportunidade\s*(\d+)",

            r"escolher\s+a\s+Oportunidade\s*(\d+)",
            r"escolher\s+a\s+oportunidade\s*(\d+)",

            r"escolhida\s+a\s+Oportunidade\s*(\d+)",
            r"escolhida\s+a\s+oportunidade\s*(\d+)",

            r"escolhendo\s+a\s+Oportunidade\s*(\d+)",
            r"escolhendo\s+a\s+oportunidade\s*(\d+)",

            r"selecionada\s+a\s+Oportunidade\s*(\d+)",
            r"selecionada\s+a\s+oportunidade\s*(\d+)"
        ]

        numero_oportunidade = None

        for padrao in padroes_selecao:

            encontrado = re.search(
                padrao,
                texto,
                re.IGNORECASE
            )

            if encontrado:

                numero_oportunidade = int(
                    encontrado.group(1)
                )

                break

        # -------------------------------------------------
        # 3. Se encontrou a oportunidade escolhida,
        # procurar o título correspondente.
        # -------------------------------------------------

        if numero_oportunidade is not None:

            padrao_oportunidade = (
                rf"Oportunidade\s*"
                rf"{numero_oportunidade}"
                rf"\s*[:\-–—]\s*(.+)"
            )

            encontrado = re.search(
                padrao_oportunidade,
                texto,
                re.IGNORECASE
            )

            if encontrado:

                estrategia = encontrado.group(
                    1
                ).strip()

                estrategia = estrategia.split(
                    "\n",
                    1
                )[0].strip()

                estrategia = estrategia.rstrip(
                    "."
                )

                if estrategia:

                    return estrategia[:200]

        # -------------------------------------------------
        # 4. Tentar pegar diretamente o nome que aparece
        # entre parênteses na decisão.
        #
        # Exemplo:
        # Oportunidade 2
        # (Automação de Soluções com IA para PMEs)
        # -------------------------------------------------

        if numero_oportunidade is not None:

            padrao_parenteses = (
                rf"Oportunidade\s*"
                rf"{numero_oportunidade}"
                rf"\s*\(([^)]+)\)"
            )

            encontrado = re.search(
                padrao_parenteses,
                texto,
                re.IGNORECASE
            )

            if encontrado:

                estrategia = encontrado.group(
                    1
                ).strip()

                if estrategia:

                    return estrategia[:200]

        # -------------------------------------------------
        # 5. Se houver uma estratégia estruturada em texto,
        # tentar identificá-la.
        # -------------------------------------------------

        padroes_estrategia = [
            r"Estratégia\s*:\s*(.+)",
            r"Estrategia\s*:\s*(.+)"
        ]

        for padrao in padroes_estrategia:

            encontrado = re.search(
                padrao,
                texto,
                re.IGNORECASE
            )

            if encontrado:

                estrategia = encontrado.group(
                    1
                ).strip()

                estrategia = estrategia.split(
                    "\n",
                    1
                )[0].strip()

                estrategia = estrategia.rstrip(
                    "."
                )

                if estrategia:

                    return estrategia[:200]

        # -------------------------------------------------
        # 6. Último recurso:
        # procurar Oportunidade 1.
        #
        # Isso só acontece se o Cérebro não tiver informado
        # explicitamente uma escolha.
        # -------------------------------------------------

        padrao_primeira = (
            r"Oportunidade\s*1\s*[:\-–—]\s*(.+)"
        )

        encontrado = re.search(
            padrao_primeira,
            texto,
            re.IGNORECASE
        )

        if encontrado:

            estrategia = encontrado.group(
                1
            ).strip()

            estrategia = estrategia.split(
                "\n",
                1
            )[0].strip()

            estrategia = estrategia.rstrip(
                "."
            )

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

        if not estrategia:

            return {
                "acao": "aguardar",
                "motivo": (
                    "O Cérebro não informou uma "
                    "estratégia identificável."
                ),
                "analise": analise
            }

        return {
            "acao": "testar_estrategia",
            "motivo": (
                "Estratégia selecionada pelo Cérebro."
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

        nome_estrategia = (
            estrategia
            if estrategia
            else "Ciclo da Money AI"
        )

        registrar_resultado(
            nome_estrategia,
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
                    "Estratégia selecionada pelo "
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
            estrategia=(
                estrategia
                or "Nenhuma estratégia"
            ),
            plano=resultado_execucao,
            restricoes=(
                resultado_execucao.get(
                    "restricoes",
                    {}
                )
                if isinstance(
                    resultado_execucao,
                    dict
                )
                else {}
            ),
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
        objetivo=(
            "Encontrar uma oportunidade de negócio"
        )
    )

    resultado = agente.ciclo_agente()

    print(resultado)
