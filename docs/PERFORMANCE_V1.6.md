# CX Intelligence v1.6 (beta) — Performance, isolamento e evolução segura

**Status:** beta incremental na branch `main`. A última Release oficial e imutável continua sendo [v1.5.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.5.0).

## Problema observado e objetivos

Nos testes da v1.5, o Streamlit no Render Free às vezes demorou a atualizar a interface após ações do usuário. O script executava novamente blocos analíticos de todas as abas, inclusive treinamento do baseline de reincidência e três modelos NLP, mesmo quando só se corrigia o título de uma ação.

O objetivo da v1.6 beta é **reduzir trabalho repetido por clique sem alterar os indicadores**. Não afirmar ganhos de tempo exatos sem medições reproduzíveis nas mesmas condições de infraestrutura.

## Otimizações implementadas

1. **Fragmento da aba Metas v1.5:** `@st.fragment` isola atualizações de campos, estado, importação e exportação de planos. O formulário e a tabela pertencem ao fragmento; revisões de título e transições chamam `st.rerun(scope="fragment")`, evitando refazer os gráficos das outras abas.
2. **Baseline de risco em cache:** `risk_snapshot(df)` usa `st.cache_data(max_entries=3)`. Entrada é o DataFrame completo; mudança de dados invalida o cache. A função não mantém o estimador em seu valor de retorno, apenas métricas e resultados previstos.
3. **Comparação NLP em cache:** `nlp_model_comparison()` evita treinar três classificadores repetidamente a cada clique. Fonte são as mesmas frases 100% fictícias.
4. **BI em cache:** `bi_snapshot(df, end_date, window_days, dimension, topics, channels, min_sample)` é usado nas abas BI e Metas. Todos os filtros, data final, janela e dados são parte da chave. Retornos de `st.cache_data` são cópias, protegendo a entrada contra mutação por outra chamada.
5. **Sem cache de planos:** `v15_actions` continua exclusivamente em `st.session_state`. O cache não guarda ações, arquivos importados, hipóteses do usuário ou tokens.

### Critérios de aceitação

- `tests/test_performance_v16.py`: verificações funcionais de acerto/erro de cache (contagem de chamadas) sem limites artificiais de tempo que falham sob sobrecarga do CI.
- Suíte Python 3.10, 3.12 e 3.14 verde.
- Navegação Chrome mobile 390 × 844: abas anteriores, metas, ação criada e corrigida, transição `Planejada → Em andamento`, download de JSON/Markdown e reimportação completos.
- Render publica nova implementação sem erro de inicialização; tempos de rerun públicos são *best effort* e não equivalem a SLA.

## Evidências da primeira implementação (24/10/2026)

- [GitHub Actions #40127773810](https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40127773810): quatro jobs verdes para o commit `5446ab1b`, com **186 testes Python** na suíte principal (Python 3.12) e os jobs Python 3.10 e 3.14 também aprovados.
- Chrome 390 × 844 executou **criar → exportar JSON/Markdown → mudar estado → editar título → reexportar → restaurar arquivo anterior**.
- A instrumentação `CX_V16_TEST_DIAGNOSTICS=true`, habilitada somente no job Chrome do CI, contou os reruns completos do script; a asserção passou exigindo **zero reruns completos adicionais** durante essas ações. Este é um teste do **isolamento** do fragmento, não uma medição de latência na rede pública.
- As funções de cache têm testes de **hit/miss, invalidação por dados e filtros, cópias independentes e rejeição de parâmetros mutáveis**. Não há cache global de `v15_actions`.
- Deploy do Render referente ao commit `6e2f2b15` em **estado Live**, incorporando o fragmento e o diagnóstico oculto na produção.
- **Limitação:** o Render Free não oferece neste teste um ambiente controlado para afirmar redução fixa de tempo. Tempos podem variar por inicialização a frio, rede, carga e novas sessões.

## Etapa opcional v1.6 — Armazenamento privado

- Serviço em src/private_plans.py: identidade por iss+sub verificada, expiração OIDC, chave anônima SHA-256, validação de conteúdo sintético e conflito otimista de revisão.
- Migração migrations/006_private_action_plans.sql: segurança RLS FORCE, owner por transação, runtime SQL sem privilégios de bypass.
- Interface no fragmento Metas: login, salvar e carregar planos somente quando CX_PRIVATE_PLANS_ENABLED=true e CX_PUBLIC_DEMO não está habilitado.
- [Guia de instalação privada](PRIVATE_PLANS_V1.6.md). Sem cliente OIDC separado, não há login real na demo pública.
- O recurso não é preparado para dados de clientes reais, nem para controle de permissões organizacionais.

## Persistência e autenticação — módulo privado opcional (beta)

A v1.6 agora inclui um **módulo opcional de login OIDC e armazenamento privado de planos em PostgreSQL** (ver [instalação privada](PRIVATE_PLANS_V1.6.md)). Ele está **desativado no Render público** e depende da configuração de um cliente OIDC, de um papel SQL sem BYPASSRLS e da migração de tabelas. A integração com um provedor OIDC real ainda não foi validada; por isso permanece **experimental**.

Para transformar o protótipo em sistema corporativo auditável ainda serão necessários:

- Identidade real do usuário via provedor de autenticação/OIDC, sessões seguras, proteção CSRF, limites de requisição e verificação de e-mail conforme contexto;
- Autorização **por recurso** (`owner_id`, organização, e permissões) no backend, impedindo leitura/escrita de planos de terceiros mesmo com IDs conhecidos;
- PostgreSQL com migrações, segregação tenant, validações e transações, trilha de auditoria imutável no servidor e idempotência;
- Política de retenção, mínimo de dados, backups, criptografia em trânsito/repouso e LGPD;
- Separação **total** entre o app público com dados sintéticos e um eventual ambiente autenticado de uso operacional.

No Render público, os JSONs continuam sendo cópias locais do trabalho sintético, sem persistência em banco. Em uma instalação privada configurada, o usuário autenticado pode salvar explicitamente somente as ações simuladas no PostgreSQL. Importar um JSON continua sendo uma ação distinta de salvar no banco. Nunca introduza dados bancários ou pessoais reais no ambiente demonstrativo.

## Executar no Windows

```powershell
git pull origin main
python -m pytest -q
streamlit run app.py
```

Navegue até **🎯 Metas v1.5** e teste criação, edição e restauração. Consulte a [Release estável v1.5.0](RELEASE_NOTES_V1.5.0.md) para os indicadores e limitações do produto.
