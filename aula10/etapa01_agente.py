"""
ETAPA 1 -- Primeiro agente com tool local (15 min).

ESQUELETO: implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa e rode o arquivo.
  ETAPA 1.1 -- a tool consultar_servidor (SEM o salário)
  ETAPA 1.2 -- o agente AtendenteRH com a tool
  ETAPA 1.3 -- duas perguntas: uma que precisa da tool e uma que não precisa

REFERÊNCIAS NAS AULAS
  aula1/segundo_agente.py                            Agent + @function_tool + Runner.run_sync (o básico)
  exercicios_resolvidos/aula4/ex10_function_tool.py  tool que consulta uma TABELA e devolve JSON  <- o mais parecido
  aula8/exemplos/02_agente_tool/main.py              o agente decide quando chamar a tool (e quando não)

Rodar (a partir de aula10/):
    python etapa01_agente.py

Pronto quando: a tool é chamada só na primeira pergunta (o print dentro dela prova).
"""
import json

from agents import Agent, Runner, function_tool

from dados_rh import servidor_publico
from provedor import configurar

MODELO = configurar()  # LLM REAL: PROVEDOR no .env (openai ou ollama)


# ETAPA 1.1 -- a tool
#   - ponha um print("[tool] consultar_servidor", matricula) no começo, para provar quando ela roda;
#   - devolva json.dumps(servidor_publico(matricula), ensure_ascii=False). A consulta servidor_publico() (dados_rh.py)
#     já vem pronta: tira o salário (dado restrito, ver Etapas 5 e 9) e trata matrícula inexistente;
#   - capriche na DOCSTRING (com Args:): é o que o LLM lê para decidir chamar a tool. Esse é o ponto da etapa.
#   Referência: exercicios_resolvidos/aula4/ex10_function_tool.py (consultar_protocolo)
@function_tool
def consultar_servidor(matricula: str) -> str:
    """Consulta os dados funcionais de um servidor pela matrícula.

    Use para perguntas sobre uma pessoa específica: nome, cargo, equipe, saldo de
    férias, abonos restantes ou chefia. Não use para dúvidas gerais sobre férias,
    abono ou diária.

    Args:
        matricula: Matrícula com apenas dígitos, por exemplo, "1002".

    Returns:
        Dados do servidor em JSON, sem salário. Se não encontrado, retorna
        {"erro": "matrícula não encontrada"}.
    """
    print("[tool] consultar_servidor", matricula)
    return json.dumps(servidor_publico(matricula), ensure_ascii=False)


def criar_atendente() -> Agent:
    # ETAPA 1.2 -- o agente
    #   Agent(name="AtendenteRH", instructions=..., tools=[consultar_servidor])
    #   Instruções: atende servidores, responde em português e de forma breve, usa a tool quando a pergunta
    #   for sobre os dados de UM servidor, e não inventa saldo de cabeça.
    #   Referência: aula1/segundo_agente.py
    return Agent(
        name="AtendenteRH",
    instructions=(
        "Você é um atendente do RH que tira dúvidas de servidores públicos. "
        "Responda sempre em português, de forma breve e direta. "
        "Perguntas gerais sobre conceitos ou regras (o que é férias, abono, abono pecuniário, diária) "
        "você responde diretamente com o seu conhecimento, sem chamar nenhuma tool e sem pedir matrícula. "
        "Só quando a pergunta for sobre os dados de UM servidor específico (saldo de férias, abonos "
        "restantes, equipe, cargo ou chefia), chame a tool consultar_servidor com a matrícula e responda "
        "só com o que ela devolver. Nesse caso, se faltar a matrícula, peça; se a tool devolver erro, "
        "diga que não encontrou. Nunca informe dados de um servidor de cabeça."
    ),
        tools=[consultar_servidor],
    )


def main() -> None:
    # ETAPA 1.3 -- rode as duas perguntas com Runner.run_sync e imprima resultado.final_output
    #   1) "Quantos dias de férias a matrícula 1002 ainda tem?"   (precisa da tool)
    #   2) "O que é abono pecuniário?"                            (não precisa)
    #   Referência: aula8/exemplos/02_agente_tool/main.py
    atendente = criar_atendente()
    perguntas = [
        "Quantos dias de férias a matrícula 1002 ainda tem?",  # precisa da tool
        "O que é abono pecuniário?",                           # não precisa
    ]
    for pergunta in perguntas:
        print(f"\n[usuário] {pergunta}")
        resultado = Runner.run_sync(atendente, pergunta)
        print(f"[resposta] {resultado.final_output}")


if __name__ == "__main__":
    print(f"[modelo] {MODELO}")
    main()
