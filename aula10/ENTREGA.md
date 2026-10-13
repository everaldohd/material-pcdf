# Entrega: Assistente de Gestão de Pessoas

**Aluno(s):**
**Até onde chegou:** ( ) Marco mínimo (Etapa 6)  ( ) Marco completo (Etapa 9)  ( ) Etapas 10–11
**Opcionais e bônus feitos:** (X) 🆕 A  ( ) 🆕 B  ( ) 🆕 C  ( ) Outro: ______

## Etapa 0: quem verifica cada regra?

| Regra | Tema | Quem verifica (função Python / agente / humano) | Por quê | Onde foi implementada (preencha na Etapa 11) |
|---|---|---|---|---|
| N1 | férias | função Python | É comparação de números | |
| N2 | férias | função Python | É cálculo matemático simples | |
| N3 | férias | função Python | É apenas uma consulta no calendário | |
| N4 | prazos | função Python | É cálculo matemático simples | |
| N5 | escala | função Python | É cálculo matemático simples | |
| N6 | abono | função Python | Verificações objeticas | |
| N7 | diária | função Python | É cálculo matemático simples; o agente Financeiro só explica | |
| N8 | aprovação | humano | É decisão da chefia; o código apenas decide se o pedido precisa da aprovação da chefia e impede autoaprovação | |
| N9 | saúde | função Python (guardrail) + agente | A regex de CID barra o dado de saúde antes de qualquer agente ler o texto. Quando o servidor pede licença de saúde sem citar CID, é preciso interpretar o texto: o agente reconhece o pedido e orienta a procurar a junta médica. | |
| N10 | dados | função Python (guardrail de saída) | Regex de CPF e CID no despacho antes de gravar: é determinística e, se errar, erra para o lado seguro. Limitação: informação de saúde sem código não tem padrão e a regex não pega.| |


## Etapa 11: os 12 casos

Compare **caminho e estado**, não o texto do despacho.

| Caso | Caminho percorrido | Resultado (bloqueado / pediu dados / triagem humana / indeferido / pausou na chefia / registrado + protocolo) | Bateu com o esperado? |
|---|---|---|---|
| C1_abono_simples | | | |
| C2_ferias_com_venda | | | |
| C3_dado_de_saude | | | |
| C4_fora_do_escopo | | | |
| C5_sem_matricula | | | |
| C6_conflito_de_escala | | | |
| C7_autoaprovacao | | | |
| C8_idempotencia | | | |
| C9_divergencia | | | |
| C10_zona_cinzenta | | | |
| C11_diaria_exterior | | | |
| C12_inicio_proibido | | | |

## O grafo

```mermaid
%% cole aqui a saída de: python etapa07_grafo.py --mermaid
```

## Etapa 4 (pronta): o que eu entendi

- Diferença entre a saída online e a offline:
- Por que a espera do retry dobra a cada tentativa:
- Por que o protocolo é um hash dos campos (e não um número sequencial):
- O que aconteceria sem o cache de feriados:

## Observabilidade (C2)

- Onde o tempo foi gasto:
- Tokens totais: ___

## Opcionais (preencha só os que fez)

- 🆕 A: votos e decisão do C9: (None..None, 04-01..04-10 vende=5, 03-25..04-03 vende=5), decisão com divergencia=True; tempo em paralelo 5,4 s, em sequência 5,7 s.
- 🆕 B: saída do `python etapa06_linear.py --governanca`:
- 🆕 C: caminho do C10 com a triagem humana (sim e não):

## Reflexão (até 3 linhas cada)

1. Quem decide o caminho no seu sistema: o LLM, o grafo, as regras ou um humano? Dê um exemplo de cada.
2. Se o guardrail de entrada falhar, o que ainda impede uma autoaprovação?
3. Por que o nó da chefia não pode gravar nada antes do `interrupt()`?
4. Qual dado veio do **MCP**, qual de **API externa** e qual de **tool local**? Por que essa divisão?
5. O que você mudaria para colocar este sistema em produção?
6. (Só se fez) 🆕 A: votar triplica o custo da extração. Em que pedidos vale a pena?
7. (Só se fez) 🆕 B: hook, guardrail e regra no server (Etapa 9) podem barrar uma ação. Qual a diferença de **onde** cada um atua?
8. (Só se fez) 🆕 C: o que muda quando o humano decide a **entrada** em vez da **saída**? Quem é consultado em cada pausa?

## De onde veio cada parte

| Arquivo / trecho | Exemplo das aulas em que me baseei | O que precisei adaptar |
|---|---|---|
| `etapa01_agente.py` | `ex10_function_tool.py` da aula 4 (tool que consulta tabela), `aula1/segundo_agente.py` (agente com tool) e `aula8/exemplos/02_agente_tool/main.py` (laço com duas perguntas) | A tool usa `servidor_publico()` em vez de um dicionário fixo e não devolve o salário. A docstring e as instruções dizem quando usar e quando não usar a tool, porque o exemplo da aula 1 manda usar sempre. O `print` dentro da tool substitui a leitura de `new_items` para mostrar quando ela roda. |
| `etapa02_extracao.py` | `aula2/agente_output2.py` (modelo Pydantic com Enum e `Field(description=...)`); para o 🆕 A, `aula7/exemplos/08_paralelismo/main.py` (fan-out/fan-in) e `aula3/agente_parada3.py` (`Runner.run` com `asyncio`) | O modelo passou de ocorrência policial para pedido de RH, com campos opcionais que ficam `null` quando o servidor não informa. Por causa do `llama3.1`, usei temperatura zero no extrator, instruções mais explícitas (matrícula, ano, data sem dia exato, diária no exterior) e mantive o `tipo` como primeiro campo, para o modelo decidir o tipo antes de preencher o resto. No 🆕 A, o paralelismo da aula 7 roda tarefas diferentes dentro de um grafo; aqui são três extratores da mesma tarefa em `asyncio.gather`, com instruções diferentes só no tratamento de pedido vago, e a votação pronta decide. |
| | | |


