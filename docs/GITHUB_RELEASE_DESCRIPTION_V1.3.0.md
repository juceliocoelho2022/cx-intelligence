# CX Intelligence v1.3.0 — Advanced Customer Experience Analytics

🚀 **Release oficial publicada em 24/10/2026.** Esta versão apresenta análises avançadas de Customer Experience e melhorias de responsividade da plataforma de portfólio.

## Novidades

- **Tendência semanal de CX:** visualização de volume de atendimentos, CSAT positivo, resolução e duração média em horas, com semanas de borda sinalizadas e intervalos Wilson 95% apenas ilustrativos.
- **Benchmark de canais e assuntos:** comparação descritiva por segmento, amostras mínimas configuráveis, diferenças em pontos percentuais de CSAT e exportação CSV.
- **Recontato em 30 dias nos tickets fictícios:** identifica tickets em datas posteriores do mesmo `customer_id`, exclui casos com janela de observação incompleta (censura à direita) e busca retornos na base sintética completa, mesmo fora dos filtros.
- **Experiência móvel:** cartões de KPI compactos, sidebar recolhida automaticamente e barra flutuante do Plotly oculta em telas estreitas.
- **Qualidade:** **98 testes pytest aprovados no CI (Python 3.12)**, jobs Python 3.10 e 3.14 aprovados, integração PostgreSQL de teste e **smoke test Chrome mobile (390 × 844 px)** passando nas três seções do novo painel e na troca entre Canal e Assunto.

✅ **CI da tag v1.3.0:** https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40106620236

🌐 **Demonstração pública:** https://cx-intelligence-demo.onrender.com/

📖 **Documentação:** https://github.com/juceliocoelho2022/cx-intelligence/blob/main/docs/ADVANCED_CX_V1.3.md

## Transparência sobre os dados

O CX Intelligence é um projeto independente de portfólio. O dashboard público utiliza **4.000 tickets totalmente sintéticos**; não contém dados de clientes reais, o CSV original Kaggle ou conexão ao PostgreSQL local. A análise de recontato, as faixas Wilson e os benchmarks são demonstrações metodológicas **sem validação com dados operacionais reais**. Recontato não é FCR, NPS nem churn.

**Tag:** `v1.3.0` · **Commit:** `1586b8e29f48625cdf987335fb6679d66f38b85d`
