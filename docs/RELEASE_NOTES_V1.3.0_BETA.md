# CX Intelligence v1.3.0 — Beta validada

**Data:** 24/10/2026
**Estado:** beta publicada no branch `main`, com demonstração pública no Render e CI aprovado.
**Release estável anterior:** [v1.2.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.2.0). **Não afirmar tag `v1.3.0` nem GitHub Release 1.3 até que sejam publicadas.**

## Funcionalidades entregues

- **Séries semanais** de volume, CSAT positivo e resolução, com média de duração em horas, faixas Wilson 95% ilustrativas e indicação de semanas de borda.
- **Benchmark por canal e assunto**, com tamanho mínimo selecionável, CSAT/resolução e gap em pontos percentuais em relação ao recorte filtrado.
- **Recontato em 30 dias no conjunto sintético:** identificação de ticket em dia posterior com mesmo `customer_id`, com acompanhamento de 30 dias completos e exclusão dos registros censurados. A base inteira é consultada para buscar eventos posteriores, mesmo quando o ticket inicial está filtrado.
- **Exportações CSV**, testes unitários e documentação das definições e limites.

## Evidência de validação

| Verificação | Evidência |
| --- | --- |
| CI Python 3.10 / 3.12 / 3.14 | **Success** nas três versões |
| Suíte principal (Python 3.12, PostgreSQL de teste) | **96 testes aprovados** |
| Smoke tests da v1.0 executados novamente na pipeline | **2 aprovados** (subconjunto já incluído na suíte principal) |
| Execução CI da interface v1.3 | https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40096728693 |
| Execução CI do README v1.3 beta | https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40096873380 |
| Render (commit `b6c4540`) | Deploy em estado **Live** |
| Smoke test visual do navegador | Aba **Analytics v1.3** abriu, seções de tendência, segmentos e recontato renderizaram sem erros bloqueantes |
| URL pública | https://cx-intelligence-demo.onrender.com/ |

Na demonstração pública, a carga é de **4.000 tickets inteiramente sintéticos**; o servidor não inclui o CSV Kaggle, dados bancários reais ou acesso ao PostgreSQL local. As telas não demonstram validação com dados reais ou significância estatística.

## Critérios de aceite e próximos passos

- [x] Módulo analítico `src/advanced_cx.py` criado.
- [x] Testes de janela de 30/31 dias, censura, domínio, benchmarks e denominadores.
- [x] Nova aba Streamlit e exportações CSV.
- [x] CI nas três versões de Python e integração PostgreSQL em banco de teste.
- [x] Demo pública com dados exclusivamente sintéticos e teste de navegação.
- [ ] Conferência visual manual no smartphone e no Windows pelo responsável do projeto.
- [ ] Avaliação de métricas temporais específicas com dados externos que realmente contenham eventos de atendimento, com origem e licença adequadas.
- [ ] Decidir se a beta será promovida para tag/Release `v1.3.0`.

## Limitações

- Dados 100% sintéticos. Não projetar conclusões para empresas ou clientes reais.
- Recontato histórico *não é* a coluna-alvo de reincidência gerada aleatoriamente, *não é* FCR e *não é* churn.
- Eventos do mesmo dia são excluídos porque não há timestamps intradiários; o horizonte de observação não certifica completude de ingestão.
- Faixas Wilson assumem independência; tickets do mesmo cliente violam potencialmente a premissa. Não representam intervalos populacionais certificados.
- Benchmarks de segmentos são parte-versus-todo; não são testes de hipótese e não comprovam causalidade.
- Kaggle e histórico v1.1 PostgreSQL permanecem recursos do ambiente local, isolados do público.

Consulte as [regras detalhadas da v1.3](ADVANCED_CX_V1.3.md) e as [notas da Release estável anterior](RELEASE_NOTES_V1.2.0.md).
