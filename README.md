# CX Intelligence | Customer Experience Analytics

![Capa conceitual do projeto CX Intelligence — Customer Experience Analytics](assets/cx-intelligence-cover.png)

> **Identidade visual conceitual.** Os indicadores exibidos na arte são ilustrativos e não correspondem às métricas calculadas pelo MVP.


![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-SQL-4169E1?logo=postgresql&logoColor=white) ![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-F7931E) ![Status](https://img.shields.io/badge/Status-v0.8-orange)

> **Dados de atendimento → indicadores CX → análise de risco → recomendações de negócio.**

Plataforma demonstrativa de Customer Experience Analytics aplicada ao setor financeiro, desenvolvida como **projeto independente de portfólio**. São utilizados apenas dados inteiramente sintéticos; não há vínculo oficial com o Banco Inter.

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

## Próximas entregas
`v0.2` UX e validação robusta → `v0.3` PostgreSQL + ETL + Docker → `v0.4` NLP avaliado → `v0.5` alvos temporais reais na simulação e calibração → `v1.0` CI, alertas auditáveis e demo online.

## Autor
[Jucelio Coelho](https://github.com/juceliocoelho2022) · Projeto educacional e técnico. Sem dados de clientes reais. Licença de reutilização ainda não definida.
