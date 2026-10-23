# Regras e alertas de anomalia — v0.5

## Objetivo
Identificar **aumentos incomuns de volume por assunto**, para encaminhar hipóteses de investigação à equipe de Customer Experience. Dados inteiramente sintéticos.

## Contrato
- Unidade: número de tickets por **semana ISO (segunda a domingo)** e por `topic`.
- Frequência: análise histórica, não monitoramento em tempo real.
- Semanas de borda incompletas (início ou fim do dataset) são excluídas.
- Lacunas de semanas no intervalo observado são contabilizadas com volume zero.
- Baseline: média dos **4 períodos completos imediatamente anteriores** do mesmo assunto; a semana atual não participa do cálculo.
- Elegibilidade: baseline >= 5 tickets.
- Alerta: volume atual >= 1,5 × baseline **e** crescimento absoluto >= 5 tickets.
- Severidade Alta: volume >= 2 × baseline; demais alertas elegíveis: Atenção.
- Variação: `100 × (volume / baseline - 1)`.
- Ação recomendada: investigar processo/canal/assunto com gestores; não presumir causa.
- Quando dados ou histórico são insuficientes, o módulo retorna lista vazia (não significa ausência de risco).

## Limitações importantes
A origem atual não registra cobertura de dias sem eventos. Portanto, a exclusão das semanas de borda usa o primeiro e o último evento observados como limites **aproximados**; não prova que houve coleta completa em cada dia. Um calendário de ingestão e SLO de completude são necessários antes de interpretar ausência de alertas como normalidade operacional.

Os limiares são heurísticos e não são métricas de significância estatística. Ainda não há previsão, sazonalidade, intervalos de confiança, redução de falsos positivos ou avaliação retroativa em dados independentes. A detecção não é causal.

## Testes
`python -m pytest -q`

Testes cobrem pico, borda parcial, baseline insuficiente, dataset vazio e parâmetros inválidos.

## Próximos incrementos
Validar cobertura e qualidade da ingestão; testar sazonalidade e mudanças estruturais; configurar thresholds por assunto; persistir alertas com versão de regra e política de deduplicação; medir alert precision/recall contra incidentes auditados.
