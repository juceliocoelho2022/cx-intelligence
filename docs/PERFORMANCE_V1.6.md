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

## Persistência e autenticação — desenho futuro, NÃO IMPLEMENTADAS

A v1.6 **não cria login, senha, tabelas de planos ou gerenciamento real de tarefas**. Transformar o protótipo público em sistema multiusuário exigirá:

- Identidade real do usuário via provedor de autenticação/OIDC, sessões seguras, proteção CSRF, limites de requisição e verificação de e-mail conforme contexto;
- Autorização **por recurso** (`owner_id`, organização, e permissões) no backend, impedindo leitura/escrita de planos de terceiros mesmo com IDs conhecidos;
- PostgreSQL com migrações, segregação tenant, validações e transações, trilha de auditoria imutável no servidor e idempotência;
- Política de retenção, mínimo de dados, backups, criptografia em trânsito/repouso e LGPD;
- Separação **total** entre o app público com dados sintéticos e um eventual ambiente autenticado de uso operacional.

Até então, os JSONs exportados são cópias locais do trabalho sintético. Importá-los substitui o plano da sessão, sem persistência em banco. Não usar dados bancários ou clientes reais no site público.

## Executar no Windows

```powershell
git pull origin main
python -m pytest -q
streamlit run app.py
```

Navegue até **🎯 Metas v1.5** e teste criação, edição e restauração. Consulte a [Release estável v1.5.0](RELEASE_NOTES_V1.5.0.md) para os indicadores e limitações do produto.
