# Requisitos e regras de negócio (BRD)

## 1. Visão e atores
**Objetivo:** auxiliar analistas de CX e gestores a investigar atendimento, satisfação e reincidência em uma fintech fictícia. **Atores:** analista de dados (prepara e valida), especialista CX (investiga temas), gestor CX (prioriza iniciativas) e engenharia de dados (evolui a ingestão).

## 2. Requisitos funcionais

| ID | Requisito | Critério de aceitação | Estado |
| --- | --- | --- | --- |
| RF-01 | Gerar tickets sintéticos reprodutíveis | Mesmo seed e tamanho produzem dados equivalentes | MVP |
| RF-02 | Validar atributos essenciais | Ausência de campos, nulos, duplicidade de ticket e faixas inválidas são detectados | MVP parcial |
| RF-03 | Filtrar dados por canal e assunto | KPIs e gráficos respeitam filtros selecionados | MVP |
| RF-04 | Exibir indicadores CX | Contagem, satisfação positiva, resolução, duração média e reincidência | MVP |
| RF-05 | Consultar dados via SQL | DDL e consultas de análise disponíveis | Scripts |
| RF-06 | Estimar propensão a novo contato | Baseline supervisionado e métricas em holdout temporal | MVP experimental |
| RF-07 | Inferir sentimentos em texto | Classificador avaliado contra rótulos anotados | Planejado |
| RF-08 | Detectar anomalias e alertar | Regras/limiares versionados com evidência | Planejado |
| RF-09 | Registrar execução de ETL e qualidade | Logs, checkpoints e relatório por lote | Planejado |

## 3. Regras de negócio
- **RN-01 — Identificação:** cada ticket possui `ticket_id` único; o cliente tem identificador sintético `customer_id`; um cliente pode ter múltiplos tickets.
- **RN-02 — Escalas:** `csat` é inteiro de 1 a 5; `csat >= 4` indica satisfação positiva **entre tickets com nota disponível**.
- **RN-03 — Resolução:** `resolved=1` significa chamado marcado como resolvido; não é sinônimo de resolução no primeiro contato (FCR).
- **RN-04 — Duração:** `resolution_hours` é uma duração não negativa **em horas**. Nunca reportar em minutos sem multiplicar por 60.
- **RN-05 — Taxa de resolução:** chamados resolvidos / tickets elegíveis; reportar denominador.
- **RN-06 — Reincidência:** `repeat_contact_30d` no MVP é alvo **gerado probabilisticamente**, sem observação do futuro real; não rotular como churn, evasão ou FCR.
- **RN-07 — Sentimento:** `sentiment` no MVP é categoria sintética; não afirmar que houve análise de conversas reais por NLP.
- **RN-08 — Segmentação:** filtros aplicam-se aos registros antes da agregação; apresentar contagem para evitar interpretações sobre segmentos pequenos.
- **RN-09 — Proteção:** nenhum dado pessoal real pode ser inserido, publicado, exportado ou enviado a modelo externo sem base legal e controles específicos.
- **RN-10 — Explicabilidade:** modelo retorna score estimado, nunca decisão automática sobre conta, crédito, cobrança ou tratamento discriminatório.
- **RN-11 — Rastreamento:** entradas do modelo devem corresponder à informação disponível no instante da previsão; treinar com atributos posteriores causaria vazamento.
- **RN-12 — Desvios:** qualquer anomalia futura deve incluir período, comparação, amostra, gravidade e origem do limiar.

## 4. Requisitos não funcionais
- Reprodutibilidade por seed e dependências explicitadas.
- Código modular, testes automatizados e execução documentada.
- Mensagens de erro acionáveis para falhas de integridade.
- Privacidade por padrão: dados fictícios, sem tokens ou credenciais no Git.
- Métricas auditáveis com fórmulas e denominadores descritos.
- Performance, acessibilidade e monitoramento definidos antes da produção.

## 5. Fora de escopo do MVP
Integração com Salesforce/Genesys, LLM/agentes, ingestão de dados reais, inferência causal, alertas em tempo real, decisões automatizadas e ambiente de produção.
