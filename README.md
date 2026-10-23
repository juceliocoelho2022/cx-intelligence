# CX Intelligence — Customer Experience Analytics

Projeto de portfólio independente, inspirado nas competências da posição **Data Analyst I — CX Data**. **Não é um projeto oficial do Banco Inter, nem utiliza dados de clientes reais.**

## Problema de negócio
Um banco digital fictício precisa analisar tendências de atendimento, satisfação e recorrência e priorizar investigações sobre fricções na jornada.

## Entregas do MVP
- Dataset determinístico e **100% sintético**, gerado com NumPy e pandas;
- Pipeline com verificações de integridade (IDs, nulos, domínios e faixas);
- Indicadores de CX, volume e segmentação por canal/assunto;
- Consultas SQL PostgreSQL com CTEs e funções de janela;
- Dashboard Streamlit com filtros e exportação;
- Classificador Logistic Regression com holdout temporal, ROC-AUC e Average Precision;
- Testes automatizados com pytest.

## Requisitos
Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
pip install -r requirements.txt
python -m src.pipeline
python -m src.model
python -m pytest -q
streamlit run app.py
```

O arquivo `data/cx_tickets.csv` é criado automaticamente no primeiro uso. Execute os comandos na raiz do repositório.

## Métricas e ressalvas
- **CSAT positivo (proxy):** % de notas 4 ou 5, entre os registros simulados.
- **Resolved rate:** % de tickets marcados como resolvidos. **Não é FCR**, pois não existe informação suficiente para aferir resolução no primeiro contato.
- **Reincidência em 30 dias:** campo-alvo sintético para fins de aprendizagem. Não foi derivado de eventos longitudinais observados.
- **Sentimento:** rótulo sintético; não há modelo NLP real no MVP.
- **ROC-AUC e Average Precision:** reportadas em holdout temporal. Não comprovam desempenho em clientes reais.
- `previous_tickets` usa apenas histórico anterior do cliente na ordenação por data e ticket, para evitar vazamento temporal direto.

## SQL
O diretório `sql/` contém `schema.sql` e `analysis.sql`. É possível carregar o CSV em PostgreSQL com `\copy cx_tickets FROM 'data/cx_tickets.csv' WITH (FORMAT csv, HEADER true)` no psql, a partir de uma máquina na qual o arquivo esteja acessível.

## Próxima evolução
1. Criar eventos reais de simulação para derivar reincidência observável em 30 dias, com censura dos registros recentes;
2. Treinar baseline com validação rolling-window, matriz de confusão e calibração de probabilidades;
3. Construir pipeline NLP com textos fictícios e avaliação manual de classificação de sentimento;
4. Criar alertas estatísticos de anomalias e análise de causa raiz;
5. Adicionar Docker Compose e PostgreSQL como armazenamento de produção demonstrativa;
6. Documentar governança, mascaramento, retenção, LGPD e monitoramento de drift.

## Regras de negócio
- Um ticket possui identificador único e pertence a um cliente fictício.
- CSAT varia de 1 a 5; notas 4–5 são consideradas positivas para o KPI.
- O dashboard mostra apenas dados sintéticos e separa indicadores descritivos de predição.
- Scores preditivos representam probabilidade estimada **apenas dentro da simulação**.
- O projeto não deve importar ou divulgar informações pessoais reais ou atribuir resultados à empresa citada na vaga.

## Stack
Python, pandas, NumPy, scikit-learn, Streamlit, Plotly, PostgreSQL SQL (scripts), pytest, Git.
