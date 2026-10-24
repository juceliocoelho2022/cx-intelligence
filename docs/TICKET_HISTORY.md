# CX Intelligence v1.1 — Histórico de Eventos (Ticket Event History)

## Objetivo
Preservar uma trilha **append-only** de transições de tickets sintéticos, atendendo à observação sobre sobrescrita de status no UPSERT. O `cx_tickets` atual é um **snapshot**, enquanto `cx_ticket_events` guarda ocorrências registradas explicitamente.

## Regras de negócio
- **RN-EVT-01:** cada evento possui `event_key` único, `ticket_id`, `status`, `occurred_at` com fuso, `recorded_at` e `source`.
- **RN-EVT-02:** primeiro evento deve ser `OPEN`; transições válidas: `OPEN → IN_PROGRESS`, `OPEN → RESOLVED`, `IN_PROGRESS → RESOLVED`, `RESOLVED → IN_PROGRESS` (reabertura).
- **RN-EVT-03:** dois eventos consecutivos do mesmo ticket não podem ter a mesma hora ou ficar fora de ordem; o aplicativo trava a linha pai com `FOR UPDATE` para serializar escritas concorrentes por ticket.
- **RN-EVT-04:** `event_key` repetida com mesmo conteúdo = resultado `duplicate`, sem novo registro; mesma chave com conteúdo diferente = erro.
- **RN-EVT-05:** alterações ou exclusões de eventos são bloqueadas por trigger PostgreSQL. A tabela só permite inclusão de novos eventos.
- **RN-EVT-06:** `occurred_at` representa a hora declarada do evento; `recorded_at` representa o registro no banco, não são intercambiáveis.
- **RN-EVT-07:** estado em uma data = último evento com `occurred_at <= instante`; tickets sem histórico ficam fora do resultado, nunca recebem status presumido.
- **RN-EVT-08:** os eventos gerados pela demo têm `source=synthetic_demo` e horários **inventados para demonstração**; não são históricos reais.
- **RN-EVT-09:** o estado legado `cx_tickets.resolved` não é automaticamente sincronizado pelos eventos; não usar as duas fontes como métricas equivalentes.

## Execução (PowerShell)
Com Docker Desktop iniciado, `(.venv)` ativo e base sintética já carregada:

```powershell
docker compose up -d postgres
$env:CX_DATA_SOURCE = "postgres"
python -m src.ticket_events init
python -m src.ticket_events demo
python -m pytest -q
streamlit run app.py
```

A inicialização `init` **não gera eventos**. A ação `demo` cria um pequeno conjunto inventado (até 5 tickets já existentes, com horários fixos de exemplo às 09:00, 09:20 e, se marcado como resolvido, 10:15 UTC). O conjunto dos primeiros cinco tickets é fixo: executar `demo` outra vez **não cria novos eventos**.

## Consultas PostgreSQL
```powershell
docker compose exec postgres psql -U cx_user -d cx_intelligence -c "SELECT ticket_id,status,occurred_at,recorded_at,source FROM cx_ticket_events ORDER BY ticket_id,occurred_at;"
docker compose exec postgres psql -U cx_user -d cx_intelligence -c "SELECT event_key,COUNT(*) FROM cx_ticket_events GROUP BY event_key HAVING COUNT(*)>1;"
```

Consulta de estado em um ponto do tempo (exemplo UTC):

```sql
SELECT DISTINCT ON (ticket_id) ticket_id, status, occurred_at
FROM cx_ticket_events
WHERE occurred_at <= TIMESTAMPTZ '2026-08-02 23:59:59+00'
ORDER BY ticket_id, occurred_at DESC, event_key DESC;
```

## Garantias e limites
A imutabilidade no banco evita alteração acidental via SQL comum, mas não impede ações privilegiadas de administradores. O histórico só é confiável **a partir dos eventos de fato registrados**. Não é possível reconstruir mudanças anteriores da tabela de snapshot. A lógica atual não tem outbox, captura de mudança (CDC), filas, origem autenticada, multiusuário ou trilha de consentimento. O módulo não deve ser usado com clientes reais sem governança e medidas de segurança adicionais.

Testes em `tests/test_ticket_events.py` verificam regras de domínio e estrutura do esquema. A execução de inserts e triggers em um PostgreSQL real precisa de validação local adicional; testes unitários não a substituem.
