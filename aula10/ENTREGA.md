# Entrega: Assistente de Gestão de Pessoas

**Aluno(s):**
**Até onde chegou:** (X) Marco mínimo (Etapa 6)  ( ) Marco completo (Etapa 9)  ( ) Etapas 10–11
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
---
config:
  flowchart:
    curve: linear
---
graph TD;
        __start__([<p>__start__</p>]):::first
        receber(receber)
        proteger_entrada(proteger_entrada)
        recusar(recusar)
        extrair(extrair)
        pedir_dados(pedir_dados)
        identificar_servidor(identificar_servidor)
        calcular_periodo(calcular_periodo)
        normas(normas)
        escala(escala)
        financeiro(financeiro)
        consolidar(consolidar)
        redigir_despacho(redigir_despacho)
        validar(validar)
        aprovacao_chefia(aprovacao_chefia)
        registrar(registrar)
        __end__([<p>__end__</p>]):::last
        __start__ --> receber;
        aprovacao_chefia -. &nbsp;redigir&nbsp; .-> redigir_despacho;
        aprovacao_chefia -.-> registrar;
        calcular_periodo --> escala;
        calcular_periodo --> financeiro;
        calcular_periodo --> normas;
        consolidar --> redigir_despacho;
        escala --> consolidar;
        extrair -. &nbsp;ok&nbsp; .-> identificar_servidor;
        extrair -. &nbsp;incompleto&nbsp; .-> pedir_dados;
        financeiro --> consolidar;
        identificar_servidor -. &nbsp;ok&nbsp; .-> calcular_periodo;
        identificar_servidor -. &nbsp;nao_encontrado&nbsp; .-> pedir_dados;
        normas --> consolidar;
        proteger_entrada -. &nbsp;ok&nbsp; .-> extrair;
        proteger_entrada -. &nbsp;bloqueado&nbsp; .-> recusar;
        receber --> proteger_entrada;
        redigir_despacho --> validar;
        validar -. &nbsp;chefia&nbsp; .-> aprovacao_chefia;
        validar -. &nbsp;redigir&nbsp; .-> redigir_despacho;
        validar -.-> registrar;
        pedir_dados --> __end__;
        recusar --> __end__;
        registrar --> __end__;
        classDef default fill:#f2f0ff,line-height:1.2
        classDef first fill-opacity:0
        classDef last fill:#bfb6fc
```

## Etapa 4 (pronta): o que eu entendi

- Diferença entre a saída online e a offline: offline, a BrasilAPI e a API de câmbio falham 3 vezes cada (`[retry]`); os feriados vêm do arquivo local em 1,5 s (a soma das esperas) e a cotação fica `None`. Online não há retry: feriados da `brasilapi` em 0,1 s e cotação real (5,0165). As contas de datas e o protocolo são iguais. Notei 14 feriados online contra 13 no arquivo: a API traz a segunda de Carnaval (08/02/2027), que a cópia local não tem.
- Por que a espera do retry dobra a cada tentativa: porque uma falha costuma ser serviço sobrecarregado ou fora do ar por instantes. Esperar 0,5 s e depois 1 s (backoff exponencial) dá tempo de ele se recuperar e evita que os clientes insistam todos ao mesmo tempo e piorem o problema. Com 3 tentativas, o custo máximo é 1,5 s antes de cair no plano B.
- Por que o protocolo é um hash dos campos (e não um número sequencial): porque o mesmo pedido (matrícula, tipo e datas) gera sempre o mesmo protocolo: C1 e C8 deram `ae788d33`. Assim o server reconhece um pedido repetido e não grava duas vezes (idempotência). Um número sequencial daria um protocolo novo a cada envio e dependeria de um contador guardado em algum lugar.
- O que aconteceria sem o cache de feriados: `dias_uteis()` pergunta dia por dia se a data é feriado, então um único pedido faria dezenas de chamadas à BrasilAPI. Ficaria lento, arriscaria bloqueio por excesso de requisições e, com a API fora do ar, cada consulta custaria 1,5 s de tentativas antes de usar o arquivo local.

## Etapa 5 (MCP Server do RH): o que eu vi

- Quantas tools o MCP Inspector listou: 6 (`consultar_servidor`, `consultar_escala`, `consultar_normas`, `tabela_diarias`, `consultar_remuneracao` e `registrar_decisao`). No WSL o comando do roteiro deu `inspector: not found`; funcionou com `npx -y -p @modelcontextprotocol/inspector mcp-inspector python etapa05_mcp_rh.py`.
- Por que toda tool do server devolve um dict, e não uma lista: uma tool MCP que devolve lista manda cada item como um conteúdo separado, e quem chama não distingue "lista com 1 regra" de "1 dict". Com um dict sempre (ex.: `{"tema": ..., "regras": [...]}`), o `chamar_mcp` lê o primeiro conteúdo como JSON e o formato é o mesmo em todas as tools.
- O que acontece ao gravar o mesmo protocolo duas vezes: nada é gravado de novo. O server lê os registros antes de gravar e, se o protocolo já existe, devolve sucesso com `"duplicado": true`; a 2ª gravação do `teste001` veio assim e o arquivo ficou com um único registro. O token errado ainda é aceito nesta etapa: isso só muda na Etapa 9.2.
- O agente com o server (`--agente`, `llama3.1`): "Sim, a equipe Cartório tem alguém de férias entre 12 e 26/07/2027, trata-se do servidor público com matrícula 1006."

## Etapa 6 (especialistas e fluxo linear, Marco mínimo): o que eu vi

| Caso | Resultado | Protocolo | Valor calculado pelo Financeiro |
|---|---|---|---|
| `C1_abono_simples` | registrado (deferido, sem chefia) | `ae788d33` | não consultado: abono não tem valor a calcular |
| `C2_ferias_com_venda` | registrado (deferido; aprovador `pendente_chefia`) | `b7b6f485` | R$ 3.166,67 (10 x 9500 / 30) |
| `C6_conflito_de_escala` | registrado (indeferido pela N5) | `6f1b47d7` | sem valor (0 dias vendidos); o Financeiro foi consultado sem necessidade |
| `C11_diaria_exterior` | registrado (deferido; aprovador `pendente_chefia`) | `ec67dba1` | USD 1.120,00 (3,5 x 320); em reais "a calcular" (cotação indisponível) |

- A tabela da Etapa 0 bateu com o `etapa06_regras.py`? Quase: N1 a N6 têm um `if` em `violacoes_objetivas()` e a N8 está em `precisa_chefia()`, como na minha tabela. Sobrou a N7: marquei função Python, mas ela não está no arquivo; quem calcula a diária é o agente Financeiro (no C11, 3,5 x USD 320). N9 e N10 também não estão ali: ficam nos guardrails.
- Quais especialistas o Coordenador consultou no C1, e por que não todos: Normas e Escala. O Financeiro não foi chamado porque abono não tem valor a calcular. Na primeira versão das instruções o `llama3.1` consultou só o Normas; passou a acertar quando troquei as regras com "se" por uma tabela por tipo de pedido. No C6 ele ainda chamou o Financeiro sem necessidade.
- Diferença entre `as_tool` e handoff: com `as_tool` o Coordenador chama o especialista, recebe a resposta e continua no controle: pode consultar outros e juntar os pareceres num só. No handoff a conversa é transferida e quem responde no fim é o especialista. Aqui é preciso combinar três pareceres, então `as_tool` é o que serve.
- Quem decide: no C6 o primeiro parecer do Coordenador terminou com "o pedido de férias é aprovado", e o sistema indeferiu, porque a decisão vem de `violacoes_objetivas()` (N5), não do agente. O agente explica; o código decide.

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
| `etapa03_guardrails.py` | `aula2/agente_guardrail.py` (classificador com nota de 0 a 1, `LIMIAR` e `@input_guardrail`) e `exercicios_resolvidos/aula4/ex11_guardrails.py` (regex num guardrail, sem LLM) | O exemplo tem um guardrail só; aqui são dois, e o motivo vai no `output_info` (`dado_sensivel:cpf`, `fora_do_escopo`) para o `main` escolher a mensagem. O classificador mede escopo e tentativa de mudar as regras, não tópico proibido, e ganhou uma faixa média para a zona cinzenta (C10 = 0,50). Por causa do `llama3.1`, usei temperatura zero e precisei corrigir dois falsos positivos (C1 e C2 com 0,80): deixei explícito que a nota não mede clareza, pus um exemplo de abono e disse que vender dias faz parte do pedido de férias. |
| `etapa05_mcp_rh.py` e `etapa05_cliente_mcp.py` | `aula6/desafio2/mcp_unidades.py` (MCP Server que lê um CSV), `aula3/agente_retry3.py` (idempotência) e `aula5/exemplos/04_agente_mcp/agente.py` (`MCPServerStdio` + `mcp_servers`) | As cinco tools de leitura devolvem as consultas prontas de `dados_rh.py`, sempre como um dict, e o trabalho ficou nas docstrings (o que a tool faz, formato das datas, o que volta). A `registrar_decisao` olha se o protocolo já existe antes de gravar e devolve `duplicado` em vez de erro. No agente, usei `sys.executable` no lugar de `"python"`, para o server rodar no `.venv`, e avisei nas instruções o formato AAAA-MM-DD das datas, por causa do `llama3.1`. |
| `etapa06_agentes.py` e `etapa06_linear.py` | `aula4/ex03_agente_as_tool.py` (Coordenador com especialistas como tools), `aula7/exemplos/02_agentes_especializados/main.py` (uma responsabilidade por agente), `aula7/agentes.py` (`ModelSettings(temperature=0)`) e `aula6/exemplos/01_fluxo_linear/main.py` (fluxo linear) | Cada especialista recebeu só as suas tools e instruções que dizem também o que ele NÃO faz. Por causa do `llama3.1`, as instruções do Coordenador viraram passos numerados com uma tabela de quem consultar por tipo de pedido e um passo final de consolidação das respostas; antes ele consultava só o Normas ou descartava o que recebia. Corrigi o Escala (contava o próprio pedido ou um feriado como afastamento) e o Financeiro (calculava diária em pedido de férias e chamava a tool sem a matrícula). No `analisar()`, a matrícula e a equipe foram para a primeira frase do texto, porque o Coordenador não as repassava. No `processar()`, a decisão e o aprovador vêm do código (`violacoes_objetivas` e `precisa_chefia`), e as datas chegam ao Redator já em DD/MM/AAAA. |
| | | |


