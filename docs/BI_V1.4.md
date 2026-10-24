# CX Intelligence v1.4 (beta) — Relatórios executivos avançados e BI

**Data:** 24/10/2026 · **Status:** desenvolvimento; a última Release oficial permanece [v1.3.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.3.0).

## Escopo da entrega

O novo módulo `src/bi_reports.py` adiciona **comparação executiva entre dois períodos civis consecutivos de mesma duração**, com exportação determinística de Markdown e **HTML autocontido para impressão**. A aba **📑 BI v1.4** está disponível no Streamlit, com comparação 7/14/30 dias, segmentação por canal/assunto e mínimo amostral ajustável.

**A fonte do módulo é exclusivamente o dataset sintético principal de 4.000 tickets, seja via CSV ou PostgreSQL.** O CSV externo Kaggle permanece isolado.

### Contrato de período

Para referência final `end` e janela `D`:

- **Atual:** datas inclusivas de `end - (D-1)` até `end`.
- **Anterior:** os `D` dias imediatamente anteriores ao início da janela atual.
- O fim corresponde à **data final do filtro lateral**. O início do filtro lateral **não altera o tamanho das janelas BI** — somente os filtros de `Canal` e `Assunto` são aplicados igualmente a ambos os períodos.
- Quando o início do período anterior antecede a **primeira data de todo o histórico**, a comparação é sinalizada **insufficient_history** e as variações ficam `N/A`. A presença de datas nas extremidades não certifica completude da ingestão.
- Quando não existem tickets no período anterior com os filtros selecionados, o estado é **empty_baseline**. Quando não há tickets atuais, **empty_current**. Nenhum percentual relativo é fabricado com denominador zero.
- Valores do período anterior aparecem no relatório detalhado somente quando os dois recortes são comparáveis. A UI mostra explicitamente por que a comparação não foi calculada.

### Indicadores e unidades

| KPI | Definição | Variação |
|---|---|---|
| Atendimentos | Contagem de tickets no período | **% relativa** ao anterior; `N/A` se anterior = 0 |
| CSAT positivo | Notas 4–5 sobre tickets fictícios no período | **pontos percentuais (pp)** |
| Resolvidos | `SUM(resolved) / tickets` | **pontos percentuais (pp)**; não é FCR |
| Tempo médio | Média da coluna `resolution_hours` | **horas (h)** de diferença |

Os resultados de KPI são arredondados para duas casas decimais. A diferença entre valores previamente arredondados pode diferir até centésimos de uma diferença calculada em precisão total; não há teste de significância.

### Segmentação e ausência de conclusão causal

Benchmark por **canal** ou **assunto**, incluindo apenas segmentos com **pelo menos N tickets nos dois períodos**. Segmentos são classificados pela mudança do CSAT de menor para maior, com volume, CSAT, resolução e duração comparativos.

Nenhum gap comprova causalidade, qualidade de um canal ou resultado de uma intervenção. O modelo é **descritivo** e não ajusta por sazonalidade, mix de tickets, múltiplos registros por cliente ou possíveis vieses do gerador de dados.

### Exportações

- **Markdown:** sumário de indicadores, comparabilidade, achados, segmentações, ações de investigação e limitações.
- **HTML:** um único arquivo com CSS embutido para leitura e impressão, sem JavaScript, bibliotecas online, requisições externas ou dados pessoais. Campos inseridos no HTML são escapados com `html.escape`.
- **PDF:** não é gerado automaticamente; o usuário pode abrir o HTML no navegador e usar **Imprimir → Salvar como PDF**.

A geração é determinística e não utiliza LLM. Não há envio automático de relatórios ou integração com Gmail/Slack.

## Validação e testes

`tests/test_bi_reports.py` cobre períodos de igual duração, limites observacionais, filtros uniformes, ausência de base, amostra mínima nos dois períodos, métricas/variações, exportação HTML segura, separadores Markdown e estabilidade ante reordenação.

Após atualização do GitHub:

```powershell
git pull origin main
python -m pytest -q
$env:CX_DATA_SOURCE = "postgres"  # opcional, não necessário na demo
streamlit run app.py
```

No celular, deslize a faixa de abas até **📑 BI v1.4**. Testes de CI e inspeção de interface deverão ser confirmados antes de marcar a v1.4 como Release estável.

## Limitações

- Demonstrativo 100% sintético; não mede satisfação de clientes reais.
- Dados usados para o cálculo não têm certificação de completude, amostragem ou cobertura operacional.
- A comparação não ajusta sazonalidade, feriados ou dias úteis; ambas as janelas têm a mesma duração civil.
- CSAT positivo não equivale a NPS, resolução não equivale a FCR; não há churn observado.
- Percentuais sobre bases pequenas podem oscilar muito. O mínimo por segmento é uma proteção operacional ilustrativa, não evidência de poder estatístico.
