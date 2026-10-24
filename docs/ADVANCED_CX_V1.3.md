# CX Intelligence v1.3 (beta) — Analytics avançado de Customer Experience

**Status:** desenvolvimento e validação da v1.3. A GitHub Release oficial anterior continua sendo **v1.2.0**. Todas as análises novas usam exclusivamente os **tickets gerados sinteticamente pelo projeto**; não há análise longitudinal do CSV Kaggle.

## 1. Série semanal de CSAT e resolução

**Fontes:** colunas `ticket_id`, `date`, `csat`, `resolved` e `resolution_hours` da fonte sintética principal.

- Semana: segunda-feira (semana civil/ISO). O gráfico só apresenta semanas com tickets encontrados; **ausência de pontos não comprova ausência de atendimentos**.
- **CSAT positivo:** `100 * COUNT(csat >= 4) / COUNT(ticket_id)`. Na base sintética, todas as linhas têm avaliação; não aplicar essa regra a um CSV com notas ausentes sem novo denominador.
- **Resolvidos:** `100 * SUM(resolved) / COUNT(ticket_id)`; não é FCR.
- **Tempo médio de resolução (horas):** `AVG(resolution_hours)`, independente do estado `resolved` do ticket no gerador atual. Não é SLA nem tempo até primeira resposta.
- **Intervalo Wilson 95%:** fórmula de Wilson para proporções binárias aplicada aos resultados fictícios. É ilustrativa: pressupõe observações independentes, o que pode ser violado por tickets do mesmo cliente. Não é estimativa validada de desempenho populacional.
- Semanas na borda do intervalo **são sinalizadas** quando o conjunto de registros não alcança do primeiro ao último dia dessa semana; não certificamos completude diária.

## 2. Benchmark por canal ou assunto

O usuário escolhe a dimensão `channel` ou `topic` e um mínimo de 10–150 tickets por segmento. Cada grupo apresenta:

`tickets`, `sample_share_pct`, `csat_pct`, `ci_lower_pct`, `ci_upper_pct`, `resolved_pct`, `avg_resolution_h`, `baseline_csat_pct` e `csat_gap_pp`.

A referência é o **recorte atual já filtrado**, que **inclui os próprios grupos**; portanto é uma comparação descritiva **parte-versus-todo**, não um grupo de controle independente. Gap calculado em **pontos percentuais**. Intervalos de cada grupo não são testes de significância dos gaps, e nenhuma diferença demonstra causalidade.

## 3. Recontato encontrado no histórico sintético de 30 dias

Essa análise é deliberadamente **diferente** do campo `repeat_contact_30d` empregado pelo protótipo de risco.

**Definição do evento:** um ticket posterior do **mesmo `customer_id`**, registrado em **dia estritamente posterior** ao ticket inicial e em até 30 dias civis. Sem timestamps intradiários, dois tickets no mesmo dia **não** constituem recontato nesta definição.

**Janela completa (censura à direita):** apenas tickets cuja data seja até `max(date do universo) - 30 dias` entram no denominador; os demais são identificados como **sem 30 dias completos de observação**. Um ticket com retorno observado antes de completar essa janela ainda assim fica de fora, evitando tratamento assimétrico dos dados mais recentes.

**Filtro de coorte e horizonte:** o filtro por período/canal/assunto seleciona tickets **iniciais** elegíveis. Os tickets subsequentes são procurados em **todo o conjunto de tickets sintéticos**, inclusive fora do período ou do canal filtrado. Isso evita falsos negativos criados pelos filtros visuais.

```text
coorte = tickets selecionados nos filtros
última_data = max(data em toda a base sintética)
corte = última_data - 30 dias
elegíveis = coorte onde data <= corte
recontato_30d_pct = 100 * elegíveis com ticket posterior / total elegível
```

Os resultados apresentam quantidade na coorte, elegíveis, censurados, casos com recontato, taxa global e segmentação por canal/assunto, com mínimo amostral e faixas Wilson ilustrativas.

**Exemplo fictício:**
- Ticket A em 01/08; outro ticket do mesmo cliente em 31/08 → recontato contado se a janela completa puder ser observada.
- Ticket B em 01/08; outro em 01/09 → não contado (31 dias).
- Tickets no mesmo dia → não contados por falta de hora.
- Ticket com apenas 12 dias entre sua data e `max(date)` → **censurado**, nunca classificado como "sem recontato".

**Atenção metodológica:**
- Isso representa apenas **repetição registrada dentro do dataset sintético**, não retorno comprovado de clientes bancários.
- Não se confunde com FCR, churn, NPS, nem com o alvo de reincidência artificial do modelo.
- No gerador fictício, IDs de clientes reaparecem por desenho; a taxa calculada não representa estimativa de mercado.
- A última data do dataset é um **limite observacional**, não certificação de que todos os tickets foram coletados.
- O cálculo por calendário civil pode perder recontato no mesmo dia, e não distingue múltiplos assuntos ou contatos pelo mesmo problema.
- As faixas Wilson não ajustam dependência entre registros nem amostragem e não são generalizáveis.

## Uso na aplicação

```powershell
git pull origin main
python -m pytest -q
$env:CX_DATA_SOURCE = "postgres"  # opcional: csv é o padrão e funciona online
streamlit run app.py
```

Selecione **📐 Analytics v1.3**. Use os filtros da barra lateral para refinar o recorte. Todos os resultados tabulares podem ser exportados como CSV, sem exportar mensagens ou dados pessoais reais.

## Testes e aceite

`tests/test_advanced_cx.py` verifica:
- Intervalos Wilson, amostras vazias e domínio inválido;
- Agregação por semana ISO, semana de borda e denominadores;
- Benchmark por canal e assunto, limiar amostral e referência filtrada;
- Recontato em exatamente 30 dias e rejeição de 31 dias;
- Exclusão de contatos no mesmo dia;
- Censura de coortes recentes, inclusive quando já há evento futuro na janela parcial;
- Busca de retorno no universo completo sem perder contatos fora dos filtros;
- Separação explícita do alvo sintético `repeat_contact_30d` e verificação de estabilidade diante de ordenação das linhas.

**Checklist visual:** verificar a nova aba no Streamlit, faixas semanais, tabelas, exportações CSV e comportamento ao selecionar períodos curtos. Antes de publicar uma Release v1.3.0, confirmar CI nas três versões do Python e a demonstração pública com dados sintéticos.
