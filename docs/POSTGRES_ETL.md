# PostgreSQL + ETL — v0.3

A fonte padrão permanece o CSV sintético. O banco local é uma camada de persistência opcional.

## Subir a infraestrutura (Docker Desktop)
```powershell
docker compose up -d postgres
docker compose ps
```

PostgreSQL 16 fica disponível apenas em `127.0.0.1:5433`. O volume `cx_pg_data` preserva os registros entre reinicializações. A senha de exemplo **é somente para uso local**; substitua `POSTGRES_PASSWORD` antes de ambientes compartilhados e configure `DATABASE_URL` correspondente.

## Gerar, carregar e verificar
```powershell
python -m pip install -r requirements.txt
python -m src.pipeline
python -m src.database
docker compose exec postgres psql -U cx_user -d cx_intelligence -c "SELECT COUNT(*) FROM cx_tickets;"
docker compose exec postgres psql -U cx_user -d cx_intelligence -c "SELECT run_id,input_count,affected_count,started_at FROM cx_etl_runs ORDER BY run_id DESC LIMIT 5;"
```

## Critérios de aceitação
- Primeira carga: cria/atualiza até 4.000 linhas a partir do CSV padrão.
- Reexecução com mesmos dados: nenhuma linha precisa ser alterada (affected_count = 0).
- IDs duplicados, notas fora da faixa, nulos e duração negativa são barrados antes da conexão.
- A carga e seu registro de auditoria são uma única transação.
- Falha de conexão deve produzir erro explícito; não esconder problemas retornando dados fictícios.

## Dashboard
A seleção de fonte pode ser configurada com `CX_DATA_SOURCE=postgres` após carregar a base. Quando ausente, o modo CSV segue funcionando normalmente. O indicador de origem aparece na interface.

## Limites
Sem orquestrador ou agendamento, sem ingestão de sistema externo e sem DDL migrations versionadas (próxima evolução). A trilha de auditoria cobre execuções bem-sucedidas; falhas anteriores à transação não permanecem no banco. Ainda são dados 100% sintéticos.
