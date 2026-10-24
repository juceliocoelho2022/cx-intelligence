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
- **Teste Chrome mobile 390 × 844 px:** módulo v1.4 e controles visíveis, downloads reais de **Markdown e HTML** executados e arquivos validados por nome e conteúdo. O teste móvel v1.3 também permaneceu verde.
- **GitHub Actions (quatro jobs aprovados):** https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40109631733
- **Demo pública:** https://cx-intelligence-demo.onrender.com/ — deploy do commit `5dc94c69b` confirmado **Live** no Render em 24/10/2026.
- **Regra de negócios:** [BI_V1.4.md](BI_V1.4.md).

## Aceite manual — exportação HTML no Windows

Captura de tela fornecida pelo responsável em 24/10/2026 mostra, lado a lado, o Streamlit local em `localhost:8503` na aba **Business Intelligence — Relatório Executivo Comparativo** e o arquivo exportado `cx_bi_v14_sintetico.html` aberto no navegador por caminho local (`file://`/arquivo em Downloads). O HTML renderiza título, aviso de dados sintéticos, períodos atual **06/10/2026–19/10/2026** e anterior **22/09/2026–05/10/2026**, tabela comparativa e seção de achados.

Valores da tela: **685 vs. 737** atendimentos (**−7,06%**), CSAT **62,19% vs. 62,01%** (**+0,18 pp**), resolução **87,45% vs. 87,38%** (**+0,07 pp**) e duração **10,89 h vs. 11,17 h** (**−0,28 h**).

**Evidência complementar — Markdown (24/10/2026):** segunda captura do responsável mostra o arquivo `cx_bi_v14_sintetico (1).md` aberto no VS Code, lado a lado com o mesmo relatório `cx_bi_v14_sintetico.html` aberto no navegador. São visíveis a tabela dos quatro indicadores, os achados descritivos, segmentos comparáveis, ações sugeridas e limitações. Portanto **ambos os formatos foram exportados e abertos com sucesso no Windows**.

**Escopo da evidência:** os arquivos abertos estão na pasta local `Downloads` e a origem dos downloads **não é identificável nessa captura**; a evidência demonstra leitura e integridade visual local, mas não prova o funcionamento das duas exportações **diretamente via Render público**. O CI já havia validado downloads de Markdown e HTML de ponta a ponta em Chrome headless de largura móvel. A inspeção externa do site público reportou anteriormente erros de importação JS/CSS no fluxo de download; a causa pontual não se reproduziu no CI. Recomenda-se confirmar os dois downloads no site público antes de promover a beta.

## Tentativa de aceite automatizado na URL pública — pendência identificada

Em 24/10/2026, um workflow temporário com Chrome mobile (390 × 844 px) tentou abrir **https://cx-intelligence-demo.onrender.com/** e baixar os dois relatórios diretamente do servidor público. A verificação não conseguiu alcançar os botões de exportação, pois a aplicação apresentou erros de carregamento de módulo JavaScript `Failed to fetch dynamically imported module` relativos ao componente Streamlit `static/js/Metric.DMz1h4un.js`.

- Primeira tentativa: [GitHub Actions #40110708357](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40110708357) — a interface ainda carregava quando a asserção inicial terminou.
- Nova tentativa com espera de **110 segundos** por `4.000` tickets: [GitHub Actions #40110968806](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40110968806) — erro de importação dinâmica do módulo `Metric` foi capturado no snapshot acessível do navegador antes de chegar à aba BI.

**Diagnóstico ainda não conclusivo:** podem estar envolvidos indisponibilidade momentânea de chunks JS, mudanças de deploy/cache ou falhas de rede. Não foi demonstrado que o endpoint de download em si esteja defeituoso, pois a execução falhou **antes da interação com os botões**. O teste equivalente em um servidor Streamlit local com o mesmo código, em GitHub Actions, **conseguiu efetivamente baixar os arquivos HTML e Markdown**. O usuário também confirmou ambos abrindo no Windows.

**Ação pendente antes da v1.4.0 estável:** reproduzir e resolver a falha intermitente de importação no Render (ou obter confirmação dos downloads do site público depois de estabilizar o serviço), sem atribuir causa não comprovada.

## Nova validação pública e estabilização de dependência

Em 24/10/2026, foi realizada outra sessão real de navegação na demo do Render, sem promover alterações durante o teste. O navegador carregou **4.000 tickets sintéticos**, os cinco KPIs principais, a aba `📑 BI v1.4`, os quatro indicadores comparativos (685/737 atendimentos; 62,19%/62,01% CSAT; 87,45%/87,38% resolvidos; 10,89 h/11,17 h), o gráfico/tabela por canal e os botões para baixar Markdown/HTML **sem erros visíveis de módulos JS**.

Os dois botões de download foram clicados, **mas a ferramenta de navegação não consegue inspecionar os bytes dos arquivos**, e não exibiu confirmação visual de conclusão. Por isso **a exportação remota permanece sem evidência de sucesso**, diferentemente dos downloads já testados no GitHub Actions contra o servidor local e do aceite manual Windows.

O arquivo `/static/js/Metric.DMz1h4un.js` pôde ser obtido da URL pública em uma requisição posterior à falha. Essa constatação mostra que o recurso estava disponível naquele momento, **sem provar por que a importação falhou antes**. O Render estava realizando vários deploys automáticos em sequência durante o diagnóstico, mas o vínculo causal não foi estabelecido.

**Mitigação adotada:** `requirements.txt` passou a fixar `streamlit==1.66.1`, a versão vista nos logs do Render Live, para manter o conjunto de arquivos JavaScript consistente entre builds reproduzidos. A versão foi fixada para previsibilidade, **não como correção comprovada do erro transitório**. São recomendáveis a verificação dos downloads no Render após um deploy estável e o acompanhamento de novos erros.

## Correção de deploy e compatibilidade — 24/10/2026

Após inspeção dos logs do Render, foi encontrada uma regressão temporária na instalação do Streamlit: uma edição do `requirements.txt` deixou `streamlit` em uma linha de comentário, causando `No module named streamlit` no startup do serviço. O requisito foi restaurado. Uma tentativa de fixar a versão 1.66.1 também revelou incompatibilidade com o job Python 3.10 do CI; a versão foi alterada para **`streamlit==1.65.0`**, disponível nas três versões Python testadas.

- **Deploy de recuperação:** commit `edac582`, confirmado **Live** no Render em 24/10/2026.
- **CI de compatibilidade:** commit `ced507b`, **quatro jobs aprovados** (Python 3.10/3.12/3.14 e Chrome mobile) após ajustar o smoke test para reconhecer `aria-expanded=false` como barra lateral recolhida no Streamlit 1.65.
- Alterações de teste/documentação após essa recuperação devem utilizar `[skip render]` na mensagem de commit para evitar reconstruções desnecessárias durante a validação da URL pública. Consulte [Render — skipping an auto-deploy](https://render.com/docs/deploys#skipping-an-auto-deploy).

Um smoke test público independente está sendo conduzido apenas depois da estabilização do deploy, conferindo downloads efetivos de `.md` e `.html`. **Não anunciar sucesso de download público sem artefatos inspecionados**.

## Critérios e pendências
- [x] Contrato analítico e modelo de comparação.
- [x] Testes de fronteira de período, filtros, casos ausentes, determinismo e segurança da exportação HTML.
- [x] Relatórios markdown/HTML e nova aba no Streamlit.
- [x] CI Python 3.10/3.12/3.14, PostgreSQL e Chrome 390 px.
- [x] Confirmar último deploy Render como **Live** e a aba v1.4 visível no navegador público (desktop).
- [x] Validar downloads reais Markdown/HTML no navegador Chrome automatizado em CI, incluindo conteúdo dos arquivos.
- [x] Validar download, abertura e renderização do relatório HTML no navegador local Windows.
- [x] Validar abertura e conteúdo do Markdown exportado no VS Code local, além do HTML já verificado no Windows.
- [ ] Confirmar os downloads **via Render público** após investigar o erro de importação dinâmica JS observado em testes remotos. Atualmente a execução falha antes dos botões.
- [ ] Inspecionar a aba BI v1.4 no Android físico, caso desejado para a Release final.
- [ ] Promover para Git tag e GitHub Release v1.4.0 após aceite.

## Limitações
**Os números são inteiramente sintéticos.** Comparações são descritivas, não causais; a seleção de janelas não ajusta sazonalidade, mix ou dias úteis. A cobertura temporal deriva de datas extremas e não certifica completude da ingestão. Resolvidos não é FCR, CSAT não é NPS, e não há churn medido.

A tag estável v1.3.0 é independente das mudanças na branch main para esta beta.
