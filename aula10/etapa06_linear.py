"""
ETAPA 6 -- O sistema inteiro como um FLUXO LINEAR em Python puro (sem LangGraph) ⇒ Marco mínimo.

ESQUELETO:
  ETAPA 6.3 -- analisar(): o Coordenador junta os pareceres (com os limites da Etapa 4.7)
  ETAPA 6.4 -- processar(): guardrails -> extração -> MCP -> feriados -> regras -> coordenador -> redator
               -> protocolo -> MCP (registrar)
  🆕 B.4    -- (OPCIONAL, bônus) testar_governanca(): os dois testes de bloqueio do --governanca

REFERÊNCIAS NAS AULAS
  aula6/exemplos/01_fluxo_linear/main.py     o fluxo linear: funciona, mas sem decisão nem volta (por isso a Etapa 7)
  aula4/ex03_agente_as_tool.py               o Coordenador com especialistas como tools
  aula7/exemplos/02_agentes_especializados/main.py   cada especialista imprime o que fez: dá para saber quem fez o quê

Rodar:
    python etapa06_linear.py                 # C1, C2, C6 e C11
    python etapa06_linear.py --governanca    # 🆕 B (opcional): os dois testes de bloqueio

Pronto quando: C1, C2 e C11 são gravados com protocolo, C6 vira indeferimento com sugestão de datas, e você sabe dizer
qual agente escreveu cada parte. (Opcional) no --governanca: a tool restrita NÃO executa e o C2 para no orçamento.
"""
import json
import os
import sys

from agents import RunHooks

import etapa06_agentes as agentes
from etapa05_cliente_mcp import chamar_mcp
from dados.casos import CASOS
from etapa02_extracao import extrair
from etapa04_ferramentas import gerar_protocolo, rodar_com_limites_sync
from etapa10_governanca import Governanca, LimiteExcedido
from etapa03_guardrails import encontrar_dado_sensivel, nota_escopo, LIMIAR, MENSAGENS
from provedor import configurar
from etapa06_regras import precisa_chefia, resumo_periodo, violacoes_objetivas

MODELO = configurar()


def analisar(pedido: dict, servidor: dict, periodo: dict, violacoes: list[str], hooks: RunHooks | None = None) -> str:
    # ETAPA 6.3 -- monte um texto com o pedido, o servidor (matrícula e equipe), o período e as violações objetivas,
    #   e rode criar_coordenador(hooks) com rodar_com_limites_sync(..., hooks=hooks). Devolva final_output.
    entrada = (
        f"Pedido da matrícula {servidor['matricula']} (equipe {servidor['equipe']}): tipo={pedido['tipo']}, "
        f"período de {pedido['data_inicio']} a {pedido['data_fim']}, "
        f"dias vendidos={pedido.get('dias_vendidos', 0)}, destino={pedido.get('destino')} "
        f"(tipo de destino: {pedido.get('tipo_destino')}).\n"
        f"Período: {periodo['dias_corridos']} dias corridos, {periodo['dias_uteis']} dias úteis, "
        f"retorno em {periodo['retorno']}, feriados no período: {periodo['feriados_no_periodo'] or 'nenhum'}.\n"
        f"Violações objetivas apuradas pelo sistema: {'; '.join(violacoes) if violacoes else 'nenhuma'}."
    )
    resultado = rodar_com_limites_sync(agentes.criar_coordenador(hooks), entrada, hooks=hooks)
    consultados = [item.raw_item.name for item in resultado.new_items if item.type == "tool_call_item"]
    print(f"      consultou: {', '.join(consultados) or 'nenhum especialista'}")
    # for item in resultado.new_items:
    #     if item.type == "tool_call_output_item":
    #         print(f"      -> {str(item.output)[:400]}")
    return resultado.final_output

def processar(texto: str, hooks: RunHooks | None = None) -> dict:
    # ETAPA 6.4 -- encadeie, imprimindo cada passo ("[1/9] guardrails", ...):
    #   1. encontrar_dado_sensivel / nota_escopo >= LIMIAR  -> devolva {"resultado": "bloqueado", "mensagem": ...}
    #   2. pedido = extrair(texto).model_dump(mode="json")  -> sem matrícula ou datas: {"resultado": "pedir_dados"}
    #   3. servidor = chamar_mcp("consultar_servidor", ...) -> não encontrado: {"resultado": "pedir_dados"}
    #   4. periodo = resumo_periodo(...)                     (API de feriados, Etapa 4)
    #   5. escala = chamar_mcp("consultar_escala", ...); violacoes = violacoes_objetivas(...)
    #   6. parecer = analisar(...)
    #   7. despacho = rodar_com_limites_sync(agentes.criar_redator(), <fatos + parecer + violações>).final_output
    #   8. protocolo = gerar_protocolo(...)
    #   9. chamar_mcp("registrar_decisao", {..., "decisao": "indeferido" se houver violação senão "deferido",
    #        "aprovador": "pendente_chefia" se precisa_chefia(...) senão "sistema", "token": os.getenv("TOKEN_REGISTRO")})
    #      (a aprovação de verdade da chefia entra na Etapa 8; aqui só marcamos que ela será necessária)
    #   Devolva {"resultado": ..., "protocolo": ..., "despacho": ..., "parecer": ...}.
    print("[1/9] guardrails")
    achado = encontrar_dado_sensivel(texto)
    if achado:
        return {"resultado": "bloqueado", "mensagem": MENSAGENS[achado]}
    nota, _ = nota_escopo(texto)
    if nota >= LIMIAR:
        return {"resultado": "bloqueado", "mensagem": MENSAGENS["fora_do_escopo"]}

    pedido = extrair(texto).model_dump(mode="json")
    tipo, matricula, inicio, fim = pedido["tipo"], pedido["matricula"], pedido["data_inicio"], pedido["data_fim"]
    print(f"[2/9] extração: {tipo} {matricula} {inicio}..{fim}")
    if tipo == "licenca_saude":
        return {"resultado": "bloqueado", "mensagem": MENSAGENS["cid"]}
    if tipo == "outro" or not (matricula and inicio and fim):
        return {"resultado": "pedir_dados", "mensagem": "Informe a matrícula, o tipo do pedido e as datas exatas."}

    servidor = chamar_mcp("consultar_servidor", {"matricula": matricula})
    if "erro" in servidor:
        print(f"[3/9] servidor: {servidor['erro']}")
        return {"resultado": "pedir_dados", "mensagem": f"Matrícula {matricula} não encontrada."}
    print(f"[3/9] servidor: {servidor['nome']} ({servidor['equipe']})")

    periodo = resumo_periodo(inicio, fim)
    print(f"[4/9] período: {periodo['dias_uteis']} dia(s) útil(eis), retorno {periodo['retorno']} "
          f"(fonte: {periodo['fonte_feriados']})")

    escala = chamar_mcp("consultar_escala", {"equipe": servidor["equipe"], "inicio": inicio, "fim": fim})
    violacoes = violacoes_objetivas(pedido, servidor, periodo, escala)
    print(f"[5/9] violações: {violacoes or 'nenhuma'}")

    print("[6/9] coordenador")
    parecer = analisar(pedido, servidor, periodo, violacoes, hooks)

    def br(data: str) -> str:
        return f"{data[8:]}/{data[5:7]}/{data[:4]}"

    print("[7/9] redator")
    decisao = "indeferido" if violacoes else "deferido"
    fatos = (
        f"Decisão: {decisao}.\n"
        f"Pedido: {tipo} da matrícula {matricula}, de {br(inicio)} a {br(fim)}, dias vendidos: {pedido['dias_vendidos']}, "
        f"destino: {pedido['destino']}.\n"
        f"Violações objetivas: {'; '.join(violacoes) if violacoes else 'nenhuma'}.\n"
        f"Parecer dos especialistas: {parecer}"
    )
    despacho = rodar_com_limites_sync(agentes.criar_redator(), fatos).final_output

    protocolo = gerar_protocolo(matricula, tipo, inicio, fim)
    print(f"[8/9] protocolo {protocolo}")

    resposta = chamar_mcp("registrar_decisao", {
        "protocolo": protocolo, "matricula": matricula, "tipo": tipo, "inicio": inicio, "fim": fim,
        "decisao": decisao,
        "aprovador": "pendente_chefia" if precisa_chefia(pedido, violacoes) else "sistema",
        "despacho": despacho, "token": os.getenv("TOKEN_REGISTRO", ""),
    })
    print(f"[9/9] registrar: {resposta}")
    if not resposta.get("sucesso"):
        resultado = "negado_pelo_server"
    else:
        resultado = "duplicado" if resposta.get("duplicado") else "registrado"
    return {"resultado": resultado, "protocolo": protocolo, "despacho": despacho, "parecer": parecer}


def testar_governanca() -> None:
    # 🆕 B.4 (opcional) -- dois testes, cada um tratando LimiteExcedido e imprimindo o motivo:
    #   a) coordenador = agentes.criar_coordenador(hooks=Governanca(), tools_extras=[agentes.consultar_remuneracao])
    #      pergunte "Qual o salário da matrícula 1002?" -> deve ser BARRADO e o print da tool NÃO pode aparecer.
    #   b) processar(CASOS["C2_ferias_com_venda"]["pedido"], hooks=Governanca(max_tools=1))
    #      -> deve parar ANTES do segundo especialista.
    print("a) Coordenador com uma tool que não é dele")
    governanca = Governanca()
    coordenador = agentes.criar_coordenador(hooks=governanca, tools_extras=[agentes.consultar_remuneracao])
    try:
        resultado = rodar_com_limites_sync(coordenador, "Qual o salário da matrícula 1002?", hooks=governanca)
        print(f"   NÃO foi barrado: {resultado.final_output}")
    except LimiteExcedido as erro:
        print(f"   barrado: {erro}")

    print("\nb) C2 com MAX_TOOLS = 1")
    try:
        resultado = processar(CASOS["C2_ferias_com_venda"]["pedido"], hooks=Governanca(max_tools=1))
        print(f"   NÃO foi barrado: {resultado.get('resultado')}")
    except LimiteExcedido as erro:
        print(f"   barrado: {erro}")

if __name__ == "__main__":
    print(f"[modelo] {MODELO}")
    if "--governanca" in sys.argv:
        testar_governanca()
    else:
        for nome in ("C1_abono_simples", "C2_ferias_com_venda", "C6_conflito_de_escala", "C11_diaria_exterior"):
            print(f"\n=============== {nome}")
            print(json.dumps(processar(CASOS[nome]["pedido"]), ensure_ascii=False, indent=2))
