# CX Intelligence | Customer Experience Analytics

![Capa conceitual do projeto CX Intelligence — Customer Experience Analytics](assets/cx-intelligence-cover.png)

> **Identidade visual conceitual.** Os indicadores exibidos na arte são ilustrativos e não correspondem às métricas calculadas pelo MVP.


![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-SQL-4169E1?logo=postgresql&logoColor=white) ![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-F7931E) ![Status](https://img.shields.io/badge/Status-v1.5.0--stable-brightgreen)

> **Dados de atendimento → indicadores CX → análise de risco → recomendações de negócio.**

### 🌐 Acesse o projeto

**[Abrir demonstração online — CX Intelligence v1.5.0](https://cx-intelligence-demo.onrender.com/)** · **[Release oficial v1.5.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.5.0)** · **[Guia de execução local completa](docs/KAGGLE_INTEGRATION.md)**

A versão pública foi verificada em 24/10/2026: o Streamlit iniciou, respondeu `ok` no endpoint de saúde e exibiu o dashboard com **4.000 tickets exclusivamente sintéticos**. O deploy público **não contém o CSV original do Kaggle nem acessa o PostgreSQL local**. Os módulos PostgreSQL e Kaggle estão disponíveis para instalação local, com dados e limitações explicitados na documentação. O serviço gratuito pode demorar a abrir após inatividade.

Plataforma demonstrativa de Customer Experience Analytics aplicada ao setor financeiro, desenvolvida como **projeto independente de portfólio**. O dataset principal utiliza dados inteiramente sintéticos; a integração opcional Kaggle preserva fonte externa isolada e importa somente metadados operacionais. Não há vínculo oficial com o Banco Inter.

## Visão executiva
Uma instituição financeira fictícia precisa medir satisfação e resolução, investigar motivos e canais de atendimento e estimar propensão simulada à reincidência. O MVP fornece exploração com Streamlit e Plotly, preparação/qualidade em Python + pandas, consultas analíticas SQL para PostgreSQL e baseline de classificação com scikit-learn.

## Mapa da documentação
| Documento | Conteúdo |
| --- | --- |
| [Regras de negócio e requisitos](docs/BUSINESS_RULES.md) | Personas, RFs, RNs, critérios de aceitação e limites |
| [Arquitetura e decisões técnicas](docs/ARCHITECTURE.md) | Fluxo de dados, módulos, ADRs, segurança e evolução |
| [Dicionário de dados e KPIs](docs/DATA_DICTIONARY.md) | Campos, fórmulas, denominadores, unidades e ressalvas |
| [Governança, testes e roadmap](docs/GOVERNANCE_AND_ROADMAP.md) | LGPD, avaliação, riscos, qualidade e plano de versões |
| [PostgreSQL e ETL](docs/POSTGRES_ETL.md) | Docker Compose, carga idempotente e auditoria de execuções |
| [NLP experimental](docs/NLP.md) | Frases fictícias, TF-IDF, matriz de confusão e avaliação por F1 |
| [Alertas CX](docs/ANOMALIES.md) | Regras semanais, limiares, severidade e limitações |
| [Diagnóstico de segmentos](docs/ROOT_CAUSE_ANALYSIS.md) | Lacunas de CSAT e resolução, priorização e hipóteses de investigação |
| [Relatório executivo](docs/EXECUTIVE_REPORT.md) | Sumário gerencial, indicadores, descobertas e exportação Markdown |
| [Rastreabilidade analítica](docs/AUDITABILITY.md) | Verificações de consistência, SHA-256 e manifesto JSON |
| [Roteiro de demonstração](docs/PORTFOLIO_DEMO.md) | Pitch, evidências e checklist de aceite da release |
| [Histórico de eventos v1.1](docs/TICKET_HISTORY.md) | Eventos imutáveis, transições, idempotência e consultas por data |
| [Kaggle externo v1.2](docs/KAGGLE_INTEGRATION.md) | CSV externo, minimização de dados, validação e análise separada |
| [Notas de release v1.2](docs/RELEASE_NOTES_V1.2.0.md) | Evidências de CI, KPIs externos e checklist de aceite |
| [Analytics avançado v1.3](docs/ADVANCED_CX_V1.3.md) | Série semanal, faixas Wilson, benchmark e recontato com censura temporal |
| [Notas da Release oficial v1.3.0](docs/RELEASE_NOTES_V1.3.0.md) | 98 testes na suíte CI, Chrome móvel 390 px, melhorias de CX e checklist de publicação |
| [Histórico da beta v1.3](docs/RELEASE_NOTES_V1.3.0_BETA.md) | Testes e melhorias que antecederam o preparo da release |
| [BI e relatórios avançados v1.4](docs/BI_V1.4.md) | Comparação de períodos equivalentes, métricas e exportação executiva Markdown/HTML |
| [Metas de CX e planos de ação v1.5.0](docs/GOALS_V1.5.md) | Metas configuráveis, ações fictícias por sessão, JSON/Markdown, revisão de texto e recuperação de planos |
| [Performance v1.6 beta](docs/PERFORMANCE_V1.6.md) | Atualizações isoladas da aba Metas, cache de análises, contratos de invalidação e limites de autenticação/persistência |
| [Planos privados opcionais v1.6](docs/PRIVATE_PLANS_V1.6.md) | OIDC, PostgreSQL 16, Row-Level Security, controle de revisão e isolamento da demo pública |
| [Release oficial v1.5.0](docs/RELEASE_NOTES_V1.5.0.md) | Escopo, compatibilidade de planos beta, evidências de testes e ressalvas |
| [Release oficial v1.4.0](docs/RELEASE_NOTES_V1.4.0.md) | BI avançado, 120 testes e downloads públicos HTML/Markdown verificados |
| [Histórico da beta v1.4](docs/RELEASE_NOTES_V1.4.0_BETA.md) | Registro dos testes e incidentes corrigidos antes da publicação |

## Stack
`Python 3.10+` · `pandas` · `NumPy` · `scikit-learn` · `Streamlit` · `Plotly` · `SQL / PostgreSQL (scripts)` · `pytest`

## Execução (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.pipeline
python -m src.model
python -m pytest -q
streamlit run app.py
```

Abra `http://localhost:8501`. O CSV `data/cx_tickets.csv` é gerado na primeira execução.

## Escopo do MVP e interpretação
- Gerador determinístico com **4.000 tickets sintéticos** por padrão; resultados não descrevem clientes reais.
- CSAT positivo: % de avaliações simuladas 4 ou 5.
- Taxa de resolução: proporção de tickets marcados como resolvidos — **não é FCR**.
- Duração: medida em **horas**.
- Reincidência 30d: variável-alvo sintética — **não é churn observado**.
- Sentimento: rótulo sintético — **ainda não é NLP aplicado a conversas**.
- Predição: regressão logística com holdout temporal e métricas ROC-AUC / Average Precision, sem validade externa em operações reais.

## PostgreSQL opcional — v0.3

```powershell
docker compose up -d postgres
python -m src.database
$env:CX_DATA_SOURCE = 'postgres'
streamlit run app.py
```

Banco local em `127.0.0.1:5433`; a aplicação usa CSV por padrão. Veja [guia de ETL](docs/POSTGRES_ETL.md). O pipeline carrega apenas dados sintéticos e registra execuções bem-sucedidas.

## NLP experimental — v0.4

A aba **NLP experimental** analisa frases fictícias via TF-IDF e regressão logística e compara três baselines (Regressão Logística, Naive Bayes e LinearSVC). São **60 mensagens sintéticas**, com 18 no teste estratificado. São exibidos F1 macro, acurácia e erros. Trata-se de avaliação didática, não validação operacional; nenhuma inferência é aplicada aos tickets do CSV/SQL. Consulte [as limitações e regras de negócio](docs/NLP.md).

## Alertas de volume — v0.5

A aba **Alertas CX** apresenta picos de volume semanal por assunto usando uma média das quatro semanas completas anteriores, crescimento mínimo relativo de 50% e absoluto de cinco chamados. São regras **heurísticas e descritivas**, não um modelo preditivo nem uma afirmação causal. Veja [regras, ressalvas e critérios](docs/ANOMALIES.md).

## Diagnóstico CX — v0.6

A aba **Diagnóstico CX** compara segmentos de assunto × canal com a população filtrada e registra gaps de CSAT positivo e resolução em pontos percentuais, com limites mínimos de amostra e recomendações auditáveis. Resultados são descritivos e **não identificam causa raiz comprovada**. Consulte [regras de negócio](docs/ROOT_CAUSE_ANALYSIS.md).

## Relatórios executivos — v0.7

A aba **Relatório executivo** gera uma síntese reproduzível do recorte filtrado, com KPIs, achados, riscos heurísticos e recomendações de investigação. O relatório pode ser exportado em **Markdown** e não usa LLM ou dados reais. Veja [regras de negócio](docs/EXECUTIVE_REPORT.md).

## Rastreabilidade e qualidade — v0.8

A aba **Relatório executivo** agora também exporta um **manifesto JSON** com hash SHA-256 determinístico do recorte, checagens de consistência entre KPIs e relatório, origem declarada e tamanho da amostra. O hash não é uma assinatura nem um histórico de auditoria persistido. Consulte [as regras e limitações](docs/AUDITABILITY.md).

## Release de portfólio — v1.0 candidata

A versão candidata incluiu teste de integração sintética (pipeline → relatório → manifesto), roteiro de demonstração e CI para Python 3.10, 3.12 e 3.14. A publicação atual está na **v1.2.0**; os testes de integração PostgreSQL e o deploy público com dados sintéticos foram validados posteriormente.

Veja [roteiro e critérios de aceite](docs/PORTFOLIO_DEMO.md).

## Histórico de tickets — v1.1 (aceite local concluído)

O módulo opt-in `src/ticket_events.py` mantém um histórico **append-only** de transições simuladas de tickets, separado do snapshot `cx_tickets`. Ele suporta reabertura explícita, idempotência por chave de evento e consulta do estado em datas anteriores. A tabela histórica só será criada ao executar `init`; eventos de demonstração só serão inseridos ao executar `demo`.

```powershell
docker compose up -d postgres
python -m src.ticket_events init
python -m src.ticket_events demo
$env:CX_DATA_SOURCE = 'postgres'
streamlit run app.py
```

Aba **Histórico de tickets**: linha do tempo dos eventos registrados e fotografia temporal. Os horários da demo foram **inventados**; a tabela atual de tickets não contém informação suficiente para reconstruir mudanças anteriores. O status antigo `resolved` não é sincronizado pela nova tabela. Testes de banco/trigger no PostgreSQL 16 CI e verificação visual local de 12 eventos e do gráfico foram concluídos em 24/10/2026. Consulte [documentação detalhada](docs/TICKET_HISTORY.md).

## Dataset externo Kaggle — v1.2 (aceite local concluído)

Integração opcional com o [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset). **O CSV é baixado manualmente pelo usuário**, preservado fora do Git e lido apenas por uma lista explícita de campos operacionais. Nomes, e-mails e textos livres não são armazenados. Dados externos permanecem em tabelas PostgreSQL separadas; não alteram os KPIs do dataset sintético nem os modelos existentes.

```powershell
# Baixe e extraia o CSV do Kaggle em data/raw/customer_support_tickets.csv
python -m src.external_kaggle "data/raw/customer_support_tickets.csv"
docker compose up -d postgres
python -m src.external_kaggle "data/raw/customer_support_tickets.csv" --write
$env:CX_DATA_SOURCE = 'postgres'
streamlit run app.py
```

A aba **Kaggle externo** mostra contagens e taxas usando denominadores explícitos. A data de compra não é usada como data de atendimento, e a ausência de nota CSAT permanece nula. **Verifique a licença do dataset na fonte antes de republicá-lo.** Consulte [regras e limitações](docs/KAGGLE_INTEGRATION.md).

## Verificação de qualidade — v1.2 validada localmente

- **70 testes aprovados localmente** antes da inclusão dos testes com PostgreSQL real.
- **74 testes aprovados no GitHub Actions** com Python 3.10/3.12/3.14 e serviço PostgreSQL 16 `cx_test` isolado (execução verificada em 24/10/2026).
- `tests/test_postgres_integration.py` exige explicitamente `TEST_DATABASE_URL` com banco de nome `cx_test`. Sem essa variável, os quatro testes de integração são ignorados **localmente**, preservando o banco `cx_intelligence`.
- Importação local do Kaggle: **8.469 tickets**, **2.769 avaliados**, **39,3% CSAT positivo entre avaliados**, **32,7% status Closed**; reprocessamento sem alteração do CSV: **0 registros afetados**.
- **Verificação visual local concluída:** aba Kaggle externo com KPIs, gráficos de tipo/canal e tabela prioridade/status; aba Histórico de tickets com 12 eventos e gráfico de status. As capturas foram fornecidas em 24/10/2026.
- **Tag e release oficial v1.2.0 publicadas no GitHub**. A tag aponta para o commit validado `dee1676`. A demonstração pública no Render está `Live`, usa somente dados sintéticos e passou no smoke test de navegador em 24/10/2026. Redistribuição do CSV externo depende de revisão da licença do Kaggle.

GitHub Actions comprovado: [workflow com testes PostgreSQL reais](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40085653843). Veja [notas do aceite v1.2](docs/RELEASE_NOTES_V1.2.0.md).

## Analytics avançado — v1.3.0 (lançamento oficial)

**Lançamento oficial:** [CX Intelligence v1.3.0 no GitHub Releases](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.3.0) — 24/10/2026 · CI [aprovado](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40106620236) · demonstração pública [Live](https://cx-intelligence-demo.onrender.com/).

Nova aba **📐 Analytics v1.3** exclusivamente sobre os tickets sintéticos principais, com:

- **Tendência semanal de CSAT**, resolução e tempo em horas, com semanas de borda sinalizadas e faixas de Wilson 95% meramente ilustrativas (não garantem inferência populacional em tickets dependentes).
- **Benchmark por canal ou assunto**, com volume, participação, taxa de CSAT/resolução, média de horas e diferença em pontos percentuais versus todo o recorte filtrado. Comparação descritiva, não teste causal nem teste de significância.
- **Recontato encontrado nos tickets fictícios**, distinto do alvo sintético `repeat_contact_30d`: procura novo ticket do mesmo cliente em data posterior até 30 dias, usa a base inteira como horizonte para evitar falsos negativos nos filtros, **exclui tickets sem 30 dias completos de acompanhamento** e não conta contatos no mesmo dia por falta de timestamp.
- **Exportações CSV e testes unitários** para indicadores, prazos de 30/31 dias, censura, amostras mínimas e regras de domínio.

Os resultados **não são FCR, churn nem recontato real de clientes**; o gerador reutiliza IDs por construção. A demo no Render continua com **dados sintéticos, sem PostgreSQL da máquina do usuário e sem CSV Kaggle**. O código da v1.3.0 passou **98 testes da suíte principal no CI (Python 3.12, incluindo PostgreSQL)**, além de smoke test com Chrome no viewport móvel **390 × 844 px**, validando controles e layout. A **[GitHub Release v1.3.0 foi publicada em 24/10/2026](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.3.0)** com a tag apontando para o commit `1586b8e` aprovado no CI. A [v1.2.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.2.0) continua disponível no histórico de versões. Consulte [regras e limites](docs/ADVANCED_CX_V1.3.md) e [notas de lançamento v1.3.0](docs/RELEASE_NOTES_V1.3.0.md).

## Em desenvolvimento — v1.6 beta: Performance e isolamento

A nova etapa prioriza a resposta dos controles de Metas e Planos de Ação no Render, mantendo a **v1.5.0 como última Release oficial**.

- `st.fragment` isola as mudanças de estado e texto na aba Metas das análises das demais abas; editar uma ação não precisa refazer a página inteira.
- Resultados de **risco sintético, benchmark NLP e BI** usam `st.cache_data` com chaves dependentes dos dados e filtros. Não se armazenam ações no cache global.
- Novos testes cobrem hit/miss de cache, invalidação após alterar dados ou filtros e a sequência de criação, edição, atualização, exportação e importação no Chrome móvel.
- **Persistência e login opcionais estão implementados em módulo privado experimental:** OIDC nativo, banco PostgreSQL com RLS por proprietário, importação de ações existentes e prevenção de sobrescrita por revisões. O recurso é bloqueado na demo pública, depende de instalação privada e ainda exige teste com um provedor OIDC real antes de uso operacional. Nenhuma informação de cliente real deve ser inserida na demo.

Consulte [Performance v1.6](docs/PERFORMANCE_V1.6.md) e [Release estável v1.5.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.5.0).

## Metas e Planos de Ação — v1.5.0 (lançamento oficial)

A nova aba **🎯 Metas v1.5** demonstra um ciclo de acompanhamento CX a partir dos **tickets 100% sintéticos do conjunto principal**, sem dados de clientes reais e sem misturar o CSV Kaggle.

- Metas hipotéticas configuráveis para CSAT positivo, percentual de resolvidos e tempo médio em horas. As lacunas respeitam **pontos percentuais (pp)** e **horas**, e não inventam conclusões sem amostra suficiente ou janela de observação completa.
- **Planos de ação fictícios** vinculados a um indicador, uma hipótese, uma área responsável simulada, um recorte temporal e um prazo proposto, com fluxo `Planejada → Em andamento → Concluída`.
- As ações existem **somente na sessão aberta do Streamlit**. Não há persistência em banco, tarefas reais, envio de e-mails, aprovação de líderes nem alteração de indicadores causada por uma ação.
- Download de **JSON determinístico** e **Markdown** com histórico e avisos de limitações.
- **Restauração manual do JSON v1.5**, validada por esquema, origem sintética e histórico de ações, para recuperar uma sessão encerrada. A restauração substitui apenas as ações da sessão atual, não recalcula retroativamente dados exportados.
- **Correção do título/hipótese** de uma ação, preservando ID, recorte e estados; revisões textuais são registradas separadamente.
- CI com **179 testes Python aprovados** e Chrome mobile validando criação, edição, transição, downloads JSON/Markdown e reimportação de um export anterior ([evidência](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40123393537)).

**[v1.5.0 é a nova Release oficial](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.5.0)**. Os arquivos JSON da beta (`1.5.0-beta`) continuam aceitos para restauração; novos arquivos usam `schema_version: 1.5.0`. O suporte é estritamente sintético, com ações restritas à sessão. Consulte [notas de lançamento](docs/RELEASE_NOTES_V1.5.0.md), [regras v1.5](docs/GOALS_V1.5.md) e [histórico de aceite](docs/RELEASE_NOTES_V1.5.0_BETA.md).

## BI comparativo e relatórios executivos — v1.4.0 (lançamento oficial)

A nova aba **📑 BI v1.4** compara janelas civis consecutivas de **7, 14 ou 30 dias**. O início do período selecionado na barra lateral não modifica a duração do benchmark; o **dia final escolhido** define o fim da janela atual. Filtros por assunto/canal são aplicados igualmente a ambos os períodos, com acesso ao histórico completo para calcular a referência.

- Comparação de **atendimentos (% relativa ao período anterior), CSAT e resolução (pp) e tempo médio de atendimento (horas)**.
- Tratamento transparente de períodos sem histórico suficiente, sem dados de base ou sem tickets atuais. Nunca são produzidas variações com denominador zero.
- Benchmark por canal/assunto somente quando **ambos** os períodos atingem o tamanho mínimo de amostra configurado.
- **Relatórios Markdown e HTML autocontido**, sem serviços externos; o HTML pode ser impresso como PDF pelo navegador e escapa valores textuais.
- Testes determinísticos de datas, filtros, lacunas, resultados e escape de HTML. A suíte principal passou com **120 testes Python**, além de CI aprovado nas versões 3.10/3.12/3.14, integração PostgreSQL e **smoke test real de navegador móvel para a v1.4** (390 × 844 px). Consulte o [CI comprovado](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40109178661) e o [aceite da beta](docs/RELEASE_NOTES_V1.4.0_BETA.md).

**[GitHub Release v1.4.0 publicada em 24/10/2026](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.4.0)**, com tag apontando para o commit `ce9aa484` aprovado nos quatro jobs do CI e em produção no Render. A validação automatizada baixou os arquivos Markdown (**1.902 caracteres**) e HTML (**3.522 caracteres**) diretamente da URL pública ([evidência de CI](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40117915523)). A demo pública utiliza 4.000 tickets sintéticos, sem CSV Kaggle ou banco local. Consulte [contrato BI v1.4](docs/BI_V1.4.md) e [notas de lançamento](docs/RELEASE_NOTES_V1.4.0.md).

## Demonstração pública segura (Render)

**[Abrir o CX Intelligence v1.3.0](https://cx-intelligence-demo.onrender.com/)** — serviço gratuito criado em 24/10/2026 e confirmado `Live`. A aplicação usa `CX_PUBLIC_DEMO=true` e `CX_DATA_SOURCE=csv`, gerando **4.000 tickets sintéticos** no servidor. O smoke test verificou título, 10 abas, aviso de ambiente demonstrativo e métrica de tickets; o endpoint `/_stcore/health` respondeu `ok`.

A demonstração pública **não hospeda o CSV Kaggle nem acessa o PostgreSQL local**; esses recursos permanecem disponíveis no ambiente de desenvolvimento. Veja [limitações da demo](docs/PUBLIC_DEMO.md) e [GitHub Release oficial v1.2.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.2.0).

## Autor
[Jucelio Coelho](https://github.com/juceliocoelho2022) · Projeto educacional e técnico. Sem dados de clientes reais. Licença de reutilização ainda não definida.
