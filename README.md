# CX Intelligence | Customer Experience Analytics

![Capa conceitual do projeto CX Intelligence — Customer Experience Analytics](assets/cx-intelligence-cover.png)

> **Identidade visual conceitual.** Os indicadores exibidos na arte são ilustrativos e não correspondem às métricas calculadas pelo MVP.


![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-SQL-4169E1?logo=postgresql&logoColor=white) ![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-F7931E) ![Status](https://img.shields.io/badge/Status-v1.2--dev-orange)

> **Dados de atendimento → indicadores CX → análise de risco → recomendações de negócio.**

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

A versão candidata inclui teste de integração sintética (pipeline → relatório → manifesto), roteiro de demonstração e pipeline de CI para Python 3.10, 3.12 e 3.14. **A aprovação da release depende de verificar Actions, execução visual e exportações na revisão publicada.** Não há deploy público confirmado.

Veja [roteiro e critérios de aceite](docs/PORTFOLIO_DEMO.md).

## Histórico de tickets — v1.1 (em validação)

O módulo opt-in `src/ticket_events.py` mantém um histórico **append-only** de transições simuladas de tickets, separado do snapshot `cx_tickets`. Ele suporta reabertura explícita, idempotência por chave de evento e consulta do estado em datas anteriores. A tabela histórica só será criada ao executar `init`; eventos de demonstração só serão inseridos ao executar `demo`.

```powershell
docker compose up -d postgres
python -m src.ticket_events init
python -m src.ticket_events demo
$env:CX_DATA_SOURCE = 'postgres'
streamlit run app.py
```

Aba **Histórico de tickets**: linha do tempo dos eventos registrados e fotografia temporal. Os horários da demo foram **inventados**; a tabela atual de tickets não contém informação suficiente para reconstruir mudanças anteriores. O status antigo `resolved` não é sincronizado pela nova tabela. Consulte [documentação detalhada](docs/TICKET_HISTORY.md). Testes de banco/trigger e validação visual em PostgreSQL ainda são pendentes nesta versão de desenvolvimento.

## Dataset externo Kaggle — v1.2 (em validação)

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

## Autor
[Jucelio Coelho](https://github.com/juceliocoelho2022) · Projeto educacional e técnico. Sem dados de clientes reais. Licença de reutilização ainda não definida.
