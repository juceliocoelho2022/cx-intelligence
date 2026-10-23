# Relatórios executivos — v0.7

## Objetivo
Gerar um memo de negócio reproduzível, legível e exportável em Markdown, **sem APIs externas**. O relatório combina KPIs do recorte, assuntos prevalentes, segmentos que merecem investigação e alertas históricos.

## Regras de negócio
- RN-REP-01: filtros de período/assunto/canal aplicam-se aos KPIs e segmentos antes da agregação.
- RN-REP-02: para anomalias, o histórico mantém datas anteriores ao recorte, mas respeita assunto/canal; a exibição inclui somente semanas cujo **início** está dentro do período solicitado.
- RN-REP-03: nenhum relatório é produzido sem registros ou com falhas de validação.
- RN-REP-04: as fórmulas de CSAT, resolução, duração e reincidência são as mesmas do dashboard e usam denominadores explicitados na documentação de KPIs.
- RN-REP-05: a prioridade de segmentos segue as regras de `src/insights.py`; alertas seguem `src/anomalies.py`.
- RN-REP-06: achados e ações são **descritivos/heurísticos**; nunca afirmar causa ou relação causal validada.
- RN-REP-07: arquivos exportados incluem período, fonte, métricas e limites da inferência.
- RN-REP-08: o relatório usa apenas dados fictícios; não inserir textos pessoais reais sem avaliação de LGPD.

## Testes
`python -m pytest -q`. O relatório é determinístico para uma entrada idêntica; a interface apresenta prévia e botão de download .md.

## Limitações
O relatório não fornece inferência causal, significância estatística, dados do cliente real ou recomendação operacional automaticamente validada. PDF, agendamento e envio automático estão fora do escopo desta versão.
