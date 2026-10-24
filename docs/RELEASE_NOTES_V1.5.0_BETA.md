# CX Intelligence v1.5.0 — Notas da Beta

**Data:** 24 de outubro de 2026. **Status:** beta na `main`, **não** publicada como tag/release. Última [Release estável v1.4.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.4.0).

## Entregas
- Aba Streamlit **🎯 Metas v1.5**: valores atuais dos dados sintéticos, metas de referência ajustáveis, gaps em pontos percentuais ou horas.
- Proteção para janelas de observação incompletas, ausência de dados e limite mínimo de amostra.
- Registro de ações **propostas e fictícias**, com ID sequencial, indicador relacionado, hipótese, área simulada e prazo.
- Transições controladas de estado, com log temporal de eventos; nenhuma ação é executada em operação real.
- Persistência **restrita ao `st.session_state`** e exportação de snapshot `JSON` e `Markdown`.
- Exportação determinística, validação estrita de campos, limites de texto e escape de conteúdo HTML/Markdown.
- Nenhuma integração com tarefas externas, banco operacional, e-mails, APIs bancárias ou dados de clientes.

## Evidências verificadas em 24/10/2026

- **155 testes pytest aprovados** em Python 3.12, incluindo regras de metas, validação de campos, segurança da exportação e lifecycle dos eventos. Os jobs de Python 3.10 e 3.14 também passaram.
- **GitHub Actions com quatro jobs verdes:** https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40121019102
- **Chrome mobile 390 × 844 px:** abas das versões 1.3, 1.4 e 1.5 aprovadas; na v1.5, uma ação foi adicionada, arquivos JSON e Markdown foram efetivamente baixados e validados e a transição fictícia para **Em andamento** foi conferida em novo download JSON, com dois eventos imutáveis no payload.
- **Render Live:** versão beta da aba v1.5 publicada no commit `4442c2f5`, sem alterar a Git tag oficial v1.4.0.
- **Navegação externa read-only:** nova aba Metas v1.5 e aviso de armazenamento por sessão encontrados na URL pública; teste externo não concluiu inspeção visual detalhada nem downloads. O aceite dos arquivos é fundamentado no teste de navegador real do CI contra o servidor local.

## Nova validação de restauração e correção de texto (24/10/2026)

Os relatórios JSON/Markdown fornecidos pelo responsável registraram a primeira ação `A0001`, em estado **Planejada**, com prazo **07/11/2026**, hipotese de investigação da jornada Pix, CSAT observado **62,19%** e meta ilustrativa **70%**. O texto do título era repetitivo; os filtros originais incluíam todos os assuntos (não apenas Pix). **Esses dados são estritamente sintéticos e a ação não foi executada.**

Para permitir conservar e corrigir esse plano na interface, foram adicionados:

- **Importação explícita do JSON v1.5 exportado**: valida versão, origem sintética, IDs, recortes, limites textuais e cadeia de mudanças de estado; restaura somente ações, substituindo as ações da sessão corrente. Não reintroduz metas antigas nem grava banco.
- **Edição de título e hipótese**: mantém ID, escopo e eventos de status, com `edits` separado no JSON para registrar as revisões textuais.
- Sinalização visível de revisão para evitar exportar antes da atualização da interface.
- **179 testes da suíte pytest principal aprovados** no job Python 3.12; os jobs Python 3.10 e 3.14 também passaram.
- **Chrome mobile 390 × 844 px aprovado**, verificando criação, atualização de status, edição, log de revisão, download JSON/Markdown e recuperação a partir de um JSON anteriormente exportado.
- [GitHub Actions — quatro jobs aprovados](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40123393537)
- Deploy da interface atualizada confirmado **Live** no Render no commit `1348366d`. As mudanças posteriores em documentação/testes usam `[skip render]`.

**Limite de aceite:** a restauração do formato de arquivo foi validada em navegador automatizado contra servidor Streamlit local. Não equivale a teste manual de importação e edição no Android do responsável, nem a evidência de backend persistente. A v1.5 segue beta.

## Aceite complementar com plano A0001 e teste remoto (24/10/2026)

O responsável disponibilizou os arquivos `cx_metas_v15_sintetico.json` e `.md` da primeira ação fictícia `A0001`. Os arquivos confirmam status **Planejada**, prazo **07/11/2026**, hipótese sobre a jornada Pix, metas sintéticas de CSAT **70%** versus **62,19%** observado e recorte original que inclui **todos os assuntos**, não apenas Pix. O título repetitivo foi corrigido **em uma cópia de arquivo disponibilizada ao responsável**, preservando ID, prazo, hipótese, escopo, status e eventos; a revisão textual é declarada em `edits`. Essa cópia **não foi inserida no repositório**.

Tentou-se reproduzir o fluxo completo contra a **URL pública do Render**, com um job Chrome 390 × 844 px e ações de sessão isoladas:

- [Execução pública #40124122690](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40124122690): falha de *timeout* na renderização inicial do módulo após selecionar a aba Metas.
- [Execução pública #40124247815](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40124247815): o roteiro avançou até a etapa de correção do título, porém a confirmação visual não surgiu no limite de 45 segundos em uma atualização do Streamlit; a execução não chegou ao download posterior.

**Interpretação:** essas duas tentativas **não comprovam falha da lógica de restauração ou edição**, mas também **não comprovam aceite de ponta a ponta na instância pública**. A sequência de criar, mudar estado, editar, exportar e restaurar foi integralmente concluída no [CI local Chrome #40123393537](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40123393537) com quatro jobs verdes e 179 testes Python. A performance e os reruns completos no Render Free merecem otimização futura. O workflow público temporário foi retirado após o diagnóstico, e não houve dados reais nem persistência em servidor.

## Condições de aceite
- A suíte Python principal deve passar com Python 3.10, 3.12 e 3.14.
- O teste móvel Chrome 390 × 844 px verifica presença da aba, avaliação de metas, criação de uma ação fictícia, downloads reais JSON/Markdown e transição de estado com evento de auditoria correspondente.
- O Render precisa abrir a aba pública sem erro crítico; o serviço é gratuito e pode ter latência de inicialização.
- O teste remoto exploratório **identificou a nova aba e os componentes** com indicação explícita de que o plano só existe na sessão. A ferramenta remota não chegou a confirmar visualmente todos os campos nem inspecionar downloads; a verificação mais forte é a execução automatizada contra o Streamlit local no CI.
- Para promover a v1.5.0, também será necessária confirmação do usuário sobre a experiência, especialmente **mudança de estado** e conservação por exportação.

## Limitações e interpretação

**A versão é uma simulação 100% sintética, sem operações reais.** As metas são objetivos didáticos configuráveis, não SLAs. Ações marcadas como concluídas não demonstram efeito causal. Mudanças nos filtros alteram a visão corrente, enquanto cada ação mantém o escopo de origem, conforme a documentação de [regras v1.5](GOALS_V1.5.md).

O histórico de eventos é imutável pela API de atualização da sessão, mas não está em banco persistente, não é auditável fora da sessão e não substitui trilha de conformidade corporativa.
