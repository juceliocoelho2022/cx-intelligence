# CX Intelligence v1.2 — Integração Kaggle (em validação)

## Dataset e licenciamento
Fonte alvo: **Customer Support Ticket Dataset**, autor suraj520:
https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset

Aproximadamente 8.469 tickets de suporte a produtos de tecnologia (não a clientes de banco). A página contém campos de nome, e-mail e descrições; o projeto **não importa nem armazena esses campos**. A licença de redistribuição não foi verificada de forma conclusiva: confirme-a no Kaggle antes de reutilizar/publicar os dados. Nunca faça commit do CSV original.

O arquivo CSV **não é baixado automaticamente**: é necessário acessar a página, aceitar os termos da fonte e baixar o arquivo por conta própria. Não exigimos credenciais no código.

## Primeiro uso (PowerShell, Windows)
1. Abra o link do dataset e baixe o arquivo CSV original, salvando-o em `data/raw/customer_support_tickets.csv` na pasta do projeto. Se necessário, crie `data/raw/`.
2. Com `(.venv)` ativado, execute:

```powershell
python -m src.external_kaggle "data/raw/customer_support_tickets.csv"
```

Isso executa apenas **pré-validação**, sem conectar ao PostgreSQL. Em seguida, inicie o banco:

```powershell
docker compose up -d postgres
python -m src.external_kaggle "data/raw/customer_support_tickets.csv" --write
```

Para acessar o dashboard:

```powershell
$env:CX_DATA_SOURCE = "postgres"
streamlit run app.py
```

Abra a aba **Kaggle externo**. O dashboard principal continua usando o dataset sintético original, sem juntar ou substituir métricas.

## Conferir integridade e idempotência
```powershell
docker compose exec postgres psql -U cx_user -d cx_intelligence -c "SELECT COUNT(*) FROM cx_external_support_tickets;"
docker compose exec postgres psql -U cx_user -d cx_intelligence -c "SELECT run_id, source_id, input_rows, affected_rows FROM cx_external_import_runs ORDER BY run_id DESC LIMIT 5;"
```

Execute novamente `--write` sem alterar o CSV: a contagem de linhas deve permanecer igual e a nova execução deve retornar `affected_rows=0`.

## Contrato e privacidade
A importação usa apenas:
- `Ticket ID`: convertido em SHA-256 do ID qualificado pela origem; o ID original **não é salvo**.
- `Ticket Type`, `Ticket Status`, `Ticket Priority`, `Ticket Channel`: valores categóricos com domínio validado.
- `Customer Satisfaction Rating`: nota inteira de 1 a 5 ou vazia (nula).

Descartados no processamento: nome, e-mail, idade, gênero, produtos, data de compra, assunto/descrição/resolução em texto livre e timestamps de resposta/resolução. A origem pode ter dados fictícios, mas também deve ser tratada com cuidado em matéria de privacidade e licença.

Tabela exclusiva: `cx_external_support_tickets`, chave composta `(source_id,ticket_hash)`, com UPSERT condicional. Execuções bem-sucedidas ficam em `cx_external_import_runs`; ambos são criados pelo importador `--write`.

## Indicadores permitidos
- **Total de tickets**: registros externos.
- **CSAT positivo**: notas 4–5 / **somente as avaliações disponíveis**. Registros sem nota não entram no denominador.
- **Status Closed**: proporção de tickets com rótulo `Closed`; não equivale a FCR.
- Volume por **tipo, canal, prioridade e status**, sem métricas temporais.

## Limitações metodológicas
- A data de compra **não é a data do atendimento** e portanto não é usada para tendência diária/semanal.
- Timestamps de resolução da fonte podem ser inconsistentes; este módulo não calcula TMA, duração de resolução, SLA ou tempo de primeira resposta.
- Não há cliente observado, histórico real de mudanças, reincidência 30d, churn, NPS nem rótulo NLP validado.
- Não misturar os resultados externos com os 4.000 tickets sintéticos do pipeline principal, nem treinar o modelo de reincidência com essa fonte sem um novo contrato de dados.
- SHA-256 determinístico do ID é uma pseudonimização, não anonimização certificada.
- A rotina atual é local e experimental, sem streaming, orquestração ou ingestão contínua; a fonte não prova origem empresarial ou representatividade.

## Testar
`python -m pytest -q`

Os testes com CSV de exemplo verificam domínio, minimização, estabilidade do hash, notas nulas e esquema SQL. A integração PostgreSQL real e renderização no navegador devem ser confirmadas localmente.
