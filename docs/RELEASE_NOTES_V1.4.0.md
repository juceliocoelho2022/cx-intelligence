# CX Intelligence v1.4.0 — Executive BI Reports

**24 de outubro de 2026** · Relatórios Executivos Avançados e Business Intelligence.

## Novidades

- **Comparação entre períodos consecutivos de 7, 14 ou 30 dias:** volume de atendimentos, satisfação CSAT positiva, percentual de tickets resolvidos e tempo médio de atendimento.
- **Métricas com unidades corretas:** volume muda em percentual relativo (%); satisfação e resolução mudam em **pontos percentuais (pp)**; duração muda em **horas**.
- **Limitações de série explicitadas:** sem comparação quando o histórico anterior não cobre toda a janela ou não há tickets suficientes para os dois recortes. Não são inventadas taxas relativas com denominador zero.
- **Comparações por canal ou assunto:** mínimo de observações exigido nos dois períodos, com tabelas e gráfico de CSAT comparativo.
- **Relatórios executivos Markdown e HTML:** exportação determinística com resumo, indicadores, hipóteses de investigação e limitações. O HTML é autocontido, acessível no navegador e pode ser impresso em PDF pelo usuário. Não é gerado PDF remotamente.
- **Interface responsiva e estável:** navegação e exportação testadas no Chrome com viewport 390 × 844 px; `streamlit==1.65.0` fixado para builds reproduzíveis, compatível com Python 3.10, 3.12 e 3.14.

## Engenharia e evidências de qualidade

- **120 testes da suíte Python principal aprovados** no CI com PostgreSQL 16 e Python 3.12; os jobs Python 3.10 e 3.14 também passaram.
- Testes de janela temporal, ausência de histórico, segmentação, determinismo, exportações, escapatória de HTML e domínio.
- **Navegador Chrome mobile:** testes de v1.3 e v1.4 passaram; arquivos Markdown e HTML foram baixados e validados contra um servidor Streamlit local na execução do GitHub Actions.
- **Aceite manual Windows:** os dois relatórios foram exportados e abertos no VS Code/navegador, exibindo conteúdo analítico.
- **Aceite remoto em produção:** GitHub Actions acessou `https://cx-intelligence-demo.onrender.com/`, baixou e verificou os dois arquivos diretamente do Render:
  - Markdown: **1.902 caracteres**.
  - HTML: **3.522 caracteres**.
  - Execução: https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40117915523 (rerun de teste público concluído com sucesso).
- Logs de erro de importação dinâmica do JavaScript foram identificados durante deploys sucessivos; após a estabilização do servidor, a navegação pública e os downloads passaram. Isso não prova uma única causa para as falhas anteriores.

## Limites das análises

Todos os indicadores demonstrados no servidor público são derivados de **4.000 tickets 100% sintéticos**. A importação Kaggle com **8.469 tickets** é isolada e executada localmente, não no servidor de demonstração. Não são utilizados dados de clientes bancários reais.

As comparações são **descritivas**, sem ajuste sazonal ou validação causal. O CSAT positivo não é NPS, tickets resolvidos não equivalem a FCR, e nenhuma métrica representa churn real. A data observada não certifica cobertura perfeita dos registros.

## Acessos

- Aplicação pública: https://cx-intelligence-demo.onrender.com/
- Código: https://github.com/juceliocoelho2022/cx-intelligence
- Documento técnico detalhado: https://github.com/juceliocoelho2022/cx-intelligence/blob/main/docs/BI_V1.4.md
- Histórico de validação da beta: https://github.com/juceliocoelho2022/cx-intelligence/blob/main/docs/RELEASE_NOTES_V1.4.0_BETA.md

**Nota:** o serviço usa o plano gratuito do Render e pode levar algum tempo para retomar após períodos de inatividade. A tag de release é imutável em relação às atualizações posteriores da branch `main`.
