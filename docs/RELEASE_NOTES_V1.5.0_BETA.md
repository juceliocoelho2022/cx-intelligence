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

## Condições de aceite
- A suíte Python principal deve passar com Python 3.10, 3.12 e 3.14.
- O teste móvel Chrome 390 × 844 px verifica presença da aba, avaliação de metas, criação de uma ação fictícia, downloads reais JSON/Markdown e transição de estado com evento de auditoria correspondente.
- O Render precisa abrir a aba pública sem erro crítico; o serviço é gratuito e pode ter latência de inicialização.
- O teste remoto exploratório **identificou a nova aba e os componentes** com indicação explícita de que o plano só existe na sessão. A ferramenta remota não chegou a confirmar visualmente todos os campos nem inspecionar downloads; a verificação mais forte é a execução automatizada contra o Streamlit local no CI.
- Para promover a v1.5.0, também será necessária confirmação do usuário sobre a experiência, especialmente **mudança de estado** e conservação por exportação.

## Limitações e interpretação

**A versão é uma simulação 100% sintética, sem operações reais.** As metas são objetivos didáticos configuráveis, não SLAs. Ações marcadas como concluídas não demonstram efeito causal. Mudanças nos filtros alteram a visão corrente, enquanto cada ação mantém o escopo de origem, conforme a documentação de [regras v1.5](GOALS_V1.5.md).

O histórico de eventos é imutável pela API de atualização da sessão, mas não está em banco persistente, não é auditável fora da sessão e não substitui trilha de conformidade corporativa.
