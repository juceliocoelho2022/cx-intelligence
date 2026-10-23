# CX Intelligence | Customer Experience Analytics

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-SQL-4169E1?logo=postgresql&logoColor=white) ![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-F7931E) ![Status](https://img.shields.io/badge/Status-MVP-orange)

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

## Próximas entregas
`v0.2` UX e validação robusta → `v0.3` PostgreSQL + ETL + Docker → `v0.4` NLP avaliado → `v0.5` alvos temporais reais na simulação e calibração → `v1.0` CI, alertas auditáveis e demo online.

## Autor
[Jucelio Coelho](https://github.com/juceliocoelho2022) · Projeto educacional e técnico. Sem dados de clientes reais. Licença de reutilização ainda não definida.
