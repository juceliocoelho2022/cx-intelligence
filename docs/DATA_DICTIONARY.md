# Dicionário de dados e métricas

Fonte: `src/pipeline.py`. Entidades são **fictícias**.

| Coluna | Tipo lógico | Definição / regra |
| --- | --- | --- |
| ticket_id | texto | ID único do chamado |
| customer_id | texto | ID pseudônimo sintético de cliente, repetível entre tickets |
| date | data | Data simulada do atendimento |
| channel | categoria | Chat, Telefone, App, Email |
| topic | categoria | Pix, Cartão, Conta, Empréstimo, Acesso ao app, Tarifas |
| resolution_hours | decimal | Duração simulada em **horas**, >= 0 |
| resolved | 0/1 | Chamado marcado como resolvido |
| sentiment | categoria | positivo, neutro, negativo — **rótulo sintético** |
| csat | inteiro | Nota simulada de 1 a 5 |
| previous_tickets | inteiro | Quantidade de tickets anteriores do cliente na ordenação por data/ID |
| repeat_contact_30d | 0/1 | **Alvo simulado**, não evento observado |

## Definições dos KPIs
Para conjunto filtrado de N tickets:
- **Volume:** N.
- **CSAT positivo:** `100 * count(csat >= 4) / count(csat validamente respondido)`. No MVP todos os tickets recebem nota sintética. Em operação real, diferenciar taxa de resposta.
- **Taxa de resolução:** `100 * sum(resolved) / N`; **não chamar de FCR**.
- **Tempo médio de resolução:** `avg(resolution_hours)` (em **horas**).
- **Taxa de reincidência sintética:** `100 * sum(repeat_contact_30d) / N`. Não equivale a churn.
- **Sentimento:** distribuição de rótulos artificiais; não é resultado de NLP.

## Regras para indicadores futuros
- **FCR:** exige vínculo entre contatos e identificação confiável do primeiro atendimento resolutivo.
- **NPS:** exige resposta de recomendação 0–10: `% promotores (9–10) - % detratores (0–6)`; não inferir NPS a partir de CSAT.
- **Reincidência observável 30d:** exige eventos posteriores, definição de mesmo problema/cliente e gestão de censura na borda temporal.
- **Churn:** exige definição de abandono e janela de atividade; `repeat_contact_30d` não é churn.

## Controles de qualidade
Unicidade de ticket_id; campos obrigatórios sem nulos; CSAT 1..5; duração >= 0; resolved e repeat_contact_30d binários. Próxima melhoria: validar domínios de canal/assunto/sentimento, tipos, datas, consistência entre estados e relatório de completude por coluna.
