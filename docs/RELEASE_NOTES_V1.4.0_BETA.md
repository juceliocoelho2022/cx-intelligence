# CX Intelligence v1.4.0 — Beta | Executive BI Reports

**Data:** 24/10/2026
**Status:** Beta validada no CI; a última tag e GitHub Release oficial continuam sendo **v1.3.0**. Não anunciar v1.4.0 como release final.

## Funcionalidades
- KPI executivo com comparação de 7, 14 ou 30 dias civis adjacentes.
- Canal/assunto aplicados igualmente aos períodos atual e anterior.
- Variação relativa (%) somente em volume, diferenças em pontos percentuais para CSAT/resolução, diferenças em horas para duração.
- Explicitação de **insufficient_history**, **empty_baseline** e **empty_current**, sem percentual fabricado.
- Segmentos comparáveis apenas com amostra mínima em ambos os períodos.
- Exportação determinística de **Markdown e HTML independente**, pronto para abrir e imprimir.
- Sem incluir o Kaggle na demo pública, sem PDF gerado por serviço externo e sem dados de clientes reais.

## Evidências verificadas
- **120 testes pytest aprovados**, Python 3.12, com testes de PostgreSQL real no serviço de CI; Python 3.10 e 3.14 também aprovados.
- **Teste Chrome mobile 390 × 844 px:** módulo v1.4 visível, controles, comparação e dois formatos de exportação encontrados. O teste móvel v1.3 também permaneceu verde.
- **GitHub Actions (quatro jobs aprovados):** https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40109178661
- **Demo pública:** https://cx-intelligence-demo.onrender.com/ (deploy do último commit deve ser conferido como Live antes de anunciar).
- **Regra de negócios:** [BI_V1.4.md](BI_V1.4.md).

## Critérios e pendências
- [x] Contrato analítico e modelo de comparação.
- [x] Testes de fronteira de período, filtros, casos ausentes, determinismo e segurança da exportação HTML.
- [x] Relatórios markdown/HTML e nova aba no Streamlit.
- [x] CI Python 3.10/3.12/3.14, PostgreSQL e Chrome 390 px.
- [ ] Conferir o último deploy Render e apresentação no navegador público.
- [ ] Validar as exportações reais dos arquivos pelo navegador, além de verificar a presença dos botões.
- [ ] Inspecionar no Android físico e Windows caso seja desejado para a Release final.
- [ ] Promover para Git tag e GitHub Release v1.4.0 após aceite.

## Limitações
**Os números são inteiramente sintéticos.** Comparações são descritivas, não causais; a seleção de janelas não ajusta sazonalidade, mix ou dias úteis. A cobertura temporal deriva de datas extremas e não certifica completude da ingestão. Resolvidos não é FCR, CSAT não é NPS, e não há churn medido.

A tag estável v1.3.0 é independente das mudanças na branch main para esta beta.
