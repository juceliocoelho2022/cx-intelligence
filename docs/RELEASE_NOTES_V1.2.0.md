# CX Intelligence — v1.2.0 | Aceite técnico e visual

**Data de preparação:** 24/10/2026
**Status:** aceite técnico e visual local concluído; tag e GitHub Release v1.2.0 publicadas; demonstração pública sintética em produção no Render, com smoke test bem-sucedido em 24/10/2026.
**Natureza:** projeto técnico independente de portfólio. Indicadores principais sintéticos; CSV Kaggle importado como fonte demonstrativa isolada.

## Incrementos desde v1.0

### v1.1 — Histórico temporal de tickets
- PostgreSQL `cx_ticket_events`: tabela append-only, chave única de evento, FK do ticket e trigger que rejeita `UPDATE`/`DELETE`.
- Escrita serializada por ticket, regras de transição, reabertura explícita e repetição idempotente por chave.
- Estado do ticket em instante histórico, sem inferir eventos não registrados a partir da tabela `cx_tickets`.
- Demonstração **opt-in** com transições e horários inventados, sempre identificados como sintéticos.
- Nova aba no dashboard **Histórico de tickets**, com consulta de estado individual e agregações históricas.
- Testes reais opcionais/CI em PostgreSQL 16 isolado: transições, histórico, chave estrangeira, immutabilidade e idempotência.

### v1.2 — Integração de dataset externo Kaggle
- Importador CSV `src/external_kaggle.py` com verificação de colunas, domínios, IDs e notas.
- Campo de ID externo transformado em hash SHA-256; nomes, e-mails, mensagens e demais campos excluídos da persistência.
- Tabelas independentes `cx_external_support_tickets` e `cx_external_import_runs`, UPSERT condicional e registro da carga.
- Aba **Kaggle externo** com volumes, status, canais, prioridades e CSAT positivo apenas para avaliações disponíveis.
- Exclusão explícita do dataset externo do ML original e dos KPIs da base sintética.
- Avisos Streamlit de `use_container_width` endereçados com `width="stretch"`.

## Evidências coletadas

No Windows, em 24/10/2026, o usuário reportou no console:

| Verificação | Resultado |
| --- | --- |
| Suíte local anterior aos novos testes de banco real | **70 passed in 7.35s** |
| CSV externo, registros validados | **8.469** |
| CSV externo, avaliações preenchidas | **2.769** |
| CSAT positivo, avaliações disponíveis | **39,3%** |
| Rótulo `Closed`, proporção de tickets externos | **32,7%** |
| Primeira carga no PostgreSQL local | **8.469** registros afetados |
| Reprocessamento do mesmo arquivo | **0** registros afetados |
| Streamlit inicializado | Porta **8502**; não equivale a validação visual |

SHA-256 do **dataset operacional sanitizado**:
`c09a1e0cd9046805c5eabff815373a95037b3a98266bdea80ceaf469f6f76741`.

O GitHub Actions com banco PostgreSQL isolado concluiu com sucesso nos jobs **Python 3.10, 3.12 e 3.14**:
https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40085653843

O log do job Python 3.12 registrou **74 testes aprovados**, incluindo testes reais de banco. As operações SQL negativas que geram mensagens `ERROR` nos logs do servidor são parte dos testes esperados de proteção do banco.

## Evidência adicional — histórico v1.1 validado localmente (24/10/2026)

O usuário confirmou via PowerShell e `psql` no PostgreSQL da aplicação:

| Verificação | Resultado observado |
| --- | --- |
| `cx_tickets`, total de tickets do dataset original | **4.000** |
| `cx_ticket_events`, eventos registrados | **12** |
| Tickets iniciais com eventos registrados | **T000001 a T000005 (5/5)** |
| `python -m src.database` reexecutado | **4.000 de entrada; 0 novos/alterados** |
| `python -m src.ticket_events demo` reexecutado | **0 tickets semeados; 0 eventos adicionados** |

Distribuição demonstrativa registrada: T000001 (OPEN → IN_PROGRESS → RESOLVED), T000002 (OPEN → IN_PROGRESS), T000003 (OPEN → IN_PROGRESS → RESOLVED), T000004 (OPEN → IN_PROGRESS) e T000005 (OPEN → IN_PROGRESS). **Os horários são fictícios**, não evidência de estados operacionais observados.

Esta evidência confirma a persistência e a idempotência do cenário de demonstração no banco local. A proteção contra UPDATE/DELETE, a chave estrangeira e a consulta histórica também passaram na suíte com PostgreSQL real no GitHub Actions. A visualização dos 12 eventos e do gráfico de status foi confirmada por captura de tela do dashboard.

## Aceite visual — comprovado em capturas de tela (24/10/2026)

O usuário apresentou o dashboard Streamlit em execução na porta local 8502, com fonte PostgreSQL. As telas mostraram:

- Aba **Histórico de tickets** com **12 eventos** e gráfico de estados históricos renderizado. Não foi evidenciada seleção individual de T000001 com data específica para checagem do texto de seu status.
- Aba **Kaggle externo** com os quatro indicadores: **8.469 tickets**, **2.769 avaliações**, **39,3% CSAT positivo somente entre avaliados** e **32,7% com status Closed**.
- Gráficos de volume por **tipo** e por **canal** renderizados, além da tabela de cruzamento de **prioridade × status**.
- Evidência de interface legível e de consulta do banco. Não são testes de usabilidade, responsividade de múltiplas resoluções ou segurança de produção.

Execução recente do GitHub Actions após as alterações de documentação, commit `16b6413`: [workflow bem-sucedido](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40089773056).

## Publicação oficial v1.2.0 e demonstração pública

- **Git tag `v1.2.0` confirmada**, apontando para o commit `dee1676f7d2b2a4be78803c8e338fe7b349e2f4a`.
- **GitHub Release pública:** https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.2.0 (publicada em 24/10/2026; descrição da Release ainda vazia no GitHub no momento desta verificação, consultar estas notas).
- **Render demo pública em estado `Live`:** https://cx-intelligence-demo.onrender.com/ (serviço `cx-intelligence-demo`, plano Free, modo `CX_PUBLIC_DEMO=true` e `CX_DATA_SOURCE=csv`).
- **HTTP health:** `/_stcore/health` retornou `ok`.
- **Smoke test no navegador:** página inicial carregada sem erros visíveis, painel CX Intelligence v1.2, **4.000 tickets exclusivamente sintéticos**, 10 abas presentes, avisos de privacidade e de ausência de banco e CSV Kaggle expostos.
- **Último GitHub Actions antes do registro do link:** CI aprovado para commit `dee1676`: https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40093057543

Nota: o snapshot da tag v1.2.0 preserva o código do momento de sua criação. Atualizações posteriores no README e nestas notas de documentação pertencem à branch principal e não modificam a tag já publicada.

## Escopo e limitações

- Kaggle alvo: https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset
- O dataset externo é de suporte técnico genérico, não representa operações bancárias nem clientes de instituição financeira.
- A licença do conjunto de dados deve ser confirmada na fonte antes de qualquer redistribuição.
- O CSV original **não** é incluído no repositório.
- O histórico v1.1 é demonstrativo: eventos históricos anteriores à sua coleta não podem ser reconstruídos da coluna `resolved`.
- Não há evidência de NPS, churn real, FCR, SLA ou sentimento inferido a partir dos tickets Kaggle.
- O hash SHA-256 facilita comparação de conteúdos, não autentica a procedência ou garante anonimização.
- **Há deploy público confirmado, com dados somente sintéticos:** https://cx-intelligence-demo.onrender.com/; a instância pública não contém os dados externos do Kaggle nem acessa o PostgreSQL local.

## Checklist para publicar v1.2.0

- [x] Importar CSV no PostgreSQL local e reprocessar idempotentemente.
- [x] Executar a suíte local de 70 testes antes da ampliação de cobertura.
- [x] Rodar testes de integração PostgreSQL no CI nas três versões de Python (execução acima).
- [x] Confirmar no navegador a nova aba **Kaggle externo**, métricas e visualizações.
- [x] Executar localmente `python -m src.ticket_events init`, `demo` e `demo` novamente; confirmar 12 eventos preexistentes nos cinco tickets e idempotência da demo.
- [x] Conferir visualmente a aba **Histórico de tickets**, total de eventos e gráfico.
- [x] Revalidar commit da branch principal após ajustes de CI e documentação (workflow do commit `16b6413` aprovado).
- [x] Verificar CI do commit de publicação do deploy `dee1676` (aprovado).
- [ ] Verificar CI de eventuais commits adicionais de documentação após a criação da tag.
- [x] Git tag `v1.2.0` e GitHub Release publicada.

O aceite técnico e visual local, a publicação da tag/Release e o smoke test do deploy público sintético estão concluídos. Uma revisão editorial da descrição da GitHub Release continua recomendada.
