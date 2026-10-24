# CX Intelligence v1.5.0 — Metas de CX e Planos de Ação

**Lançamento: 24/10/2026 · Versão estável**  
A última versão anterior foi a [v1.4.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.4.0).

## O que há de novo

A aba **🎯 Metas v1.5** transforma os indicadores descritivos da v1.4 em um *fluxo demonstrativo de acompanhamento* — sem alegar que foram realizadas intervenções, que SLAs foram atingidos ou que há causalidade.

- **Metas configuráveis**: CSAT positivo (referência ilustrativa de 70%), tickets resolvidos (90%) e teto de tempo médio (10h). Os alvos são exemplos, não benchmarks do setor financeiro.
- **Medição consistente**: janelas de 7, 14 ou 30 dias; diferenças para metas de CSAT e resolução em **pontos percentuais (pp)** e de tempo em **horas**. Recortes incompletos, amostras pequenas e ausência de dados são explicitados.
- **Plano de ação fictício**: ID sequencial, título, hipótese, área responsável simulada, prazo e contexto de filtros. Estados: `Planejada → Em andamento → Concluída`, com transições auditadas por eventos somente nesta sessão.
- **Edição de ações**: correção de título e hipótese sem perder ID, escopo, histórico de estados ou revisões anteriores.
- **Exportação JSON e Markdown** de metas, ações, hipóteses e ressalvas. JSON determinístico com validações de tamanho e segurança.
- **Recuperação de planos**: restauração manual de JSON previamente exportado, substituindo somente as ações da sessão. Metas são recalculadas a partir dos filtros atuais.
- **Compatibilidade entre versões**: arquivos JSON com `schema_version: "1.5.0-beta"` continuam aceitos; novas exportações utilizam `schema_version: "1.5.0"`. O Markdown indica v1.5.0.

## Evidências de qualidade

- Testes automatizados no **Python 3.10, 3.12 e 3.14** com PostgreSQL 16 na suíte de CI, incluindo validações de metas e limites de amostra, eventos, edição e importação de JSON.
- **Chrome mobile 390 × 844** executa criação de ação, transição de estado, revisão textual, exportação real de JSON/Markdown e restauração de um plano anterior.
- Aceite manual do responsável: ação `A0001` restaurada no Streamlit, título corrigido e estado `Planejada → Em andamento`, com eventos em 24/10/2026 e dados exportados em JSON e Markdown. O histórico permaneceu intacto.
- Para evidência detalhada de QA e resultados do Chrome: [Histórico de aceite v1.5 beta](RELEASE_NOTES_V1.5.0_BETA.md) e [regras v1.5](GOALS_V1.5.md).
- A implantação da v1.5 no Render deve ser comprovada como **Live** antes de considerar a distribuição pública concluída. Houve tentativas automatizadas diretas contra a URL pública que expiraram durante os longos *reruns* do Streamlit gratuito; o aceite funcional e dos arquivos é documentado no CI local e nos arquivos exportados manualmente.

## Privacidade e limites de interpretação

**Todos os números exibidos no painel público são derivados de 4.000 tickets 100% sintéticos.** A importação Kaggle de 8.469 tickets é **opcional, isolada e local**, sem presença na demonstração pública.

Os planos ficam somente no `st.session_state`; não existe persistência de planos em banco, credencial de usuário, distribuição de tarefas, alertas automáticos ou integrações com operações reais. Concluir uma ação no painel **não comprova efeito em CSAT, resolução ou satisfação**, e não substitui sistemas de workflow corporativos.

O upload do JSON substitui a lista de ações na sessão. Exporte primeiro qualquer plano que deseje conservar; não há sincronização com o servidor. O título de uma ação sobre Pix **não implica** que o recorte de origem tenha sido filtrado exclusivamente para Pix.

## Links

- [Demonstração pública no Render](https://cx-intelligence-demo.onrender.com/)
- [Código-fonte no GitHub](https://github.com/juceliocoelho2022/cx-intelligence)
- [Regras e limites da v1.5](https://github.com/juceliocoelho2022/cx-intelligence/blob/main/docs/GOALS_V1.5.md)
- [Aceite e incidentes durante a beta](https://github.com/juceliocoelho2022/cx-intelligence/blob/main/docs/RELEASE_NOTES_V1.5.0_BETA.md)

*Projeto independente de portfólio; sem vínculo oficial com instituições financeiras.*