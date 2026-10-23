-- KPIs de CX por tema; resolved representa fechamento, não FCR.
SELECT topic, COUNT(*) AS total_chamados,
 ROUND(100.0 * AVG(CASE WHEN csat >= 4 THEN 1.0 ELSE 0.0 END), 2) AS csat_pct,
 ROUND(100.0 * AVG(resolved),2) AS resolvidos_pct,
 ROUND(AVG(resolution_hours),2) AS tempo_medio_horas,
 ROUND(100.0 * AVG(repeat_contact_30d),2) AS reincidencia_simulada_pct
FROM cx_tickets GROUP BY topic ORDER BY total_chamados DESC;

-- Alertas: temas com crescimento de volume entre períodos de 7 dias.
WITH weekly AS (
 SELECT topic, DATE_TRUNC('week', date)::date AS semana, COUNT(*) AS volume
 FROM cx_tickets GROUP BY 1, 2
), trend AS (
 SELECT topic, semana, volume,
 LAG(volume) OVER (PARTITION BY topic ORDER BY semana) AS volume_anterior
 FROM weekly
)
SELECT topic, semana, volume, volume_anterior,
 ROUND(100.0*(volume-volume_anterior)/NULLIF(volume_anterior,0),1) AS variacao_pct
FROM trend WHERE volume_anterior IS NOT NULL ORDER BY semana DESC, variacao_pct DESC;
