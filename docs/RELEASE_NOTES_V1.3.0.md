# CX Intelligence v1.3.0 — Notas de lançamento

**Preparado em:** 24/10/2026
**Status de publicação:** **GitHub Release v1.3.0 publicada e verificada em 24/10/2026**, com tag apontando para `1586b8e29f48625cdf987335fb6679d66f38b85d`. O Render estava `Live` nesse commit e o CI foi aprovado.
**Release oficial atual:** [v1.3.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.3.0). A versão histórica [v1.2.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.2.0) permanece disponível.

## Novidades — Analytics avançado de CX

A v1.3.0 amplia os indicadores descritivos do projeto com uma aba exclusiva **📐 Analytics v1.3**:

1. **Série semanal de CX:** volume de tickets, CSAT positivo, percentual de resolução e tempo médio (horas), com identificação de semanas de borda e faixas de Wilson 95% **apenas ilustrativas**.
2. **Benchmark por canal ou assunto:** tamanho amostral configurável, desempenho de CSAT/resolução e diferenças em pontos percentuais versus toda a base filtrada. A comparação parte-versus-todo não é experimento causal nem teste de hipótese.
3. **Recontato em 30 dias nos tickets fictícios:** novo registro do mesmo `customer_id` em **dia posterior**, no máximo 30 dias depois. Tickets sem acompanhamento completo são excluídos do denominador (censura à direita); contatos posteriores são buscados na base completa, mesmo fora dos filtros da coorte. **Não confundir com o rótulo artificial `repeat_contact_30d` usado pelo modelo ML**.
4. Exportações CSV dos três componentes analíticos e documentação dos denominadores e das limitações.

## Aprimoramentos de experiência móvel

- Layout de KPIs compactado para dispositivos estreitos.
- Barra de ferramentas flutuante do Plotly oculta somente em telas até 767 px; no desktop continua disponível.
- Barra lateral em modo `auto`, recolhida por padrão em dispositivos pequenos.
- Dica de navegação horizontal até a aba **Analytics v1.3**.

## Engenharia e garantia de qualidade

- **98 testes da suíte pytest principal aprovados** no GitHub Actions com Python 3.12; execução nos Python 3.10 e 3.14 também aprovada. Os 2 smoke tests originais são uma reexecução de subconjunto da suíte principal, não devem ser somados como casos adicionais.
- Testes com PostgreSQL 16 em serviço de CI isolado para o histórico v1.1 e importação Kaggle v1.2.
- **Teste de navegador Chrome headless com viewport móvel 390 × 844**, em job adicional, validando três seções analíticas, ocultação da toolbar do Plotly, barra lateral recolhida e troca Canal ↔ Assunto.
- Execução com quatro jobs verdes: https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40106300542
- Demonstração pública sintética: https://cx-intelligence-demo.onrender.com/

## Transparência metodológica

O CX Intelligence é um **projeto independente de portfólio**, sem relação institucional com instituição financeira. A demonstração pública utiliza **4.000 tickets inteiramente sintéticos**; não contém o CSV Kaggle original, dados de clientes reais nem acesso ao PostgreSQL local.

A taxa de recontato observada nos tickets fictícios é uma contagem descritiva na base simulada e **não é** FCR, NPS, churn, nem retorno observado de clientes reais. Os valores simulados têm distribuição criada artificialmente e não permitem generalização. O CSV Kaggle foi validado no ambiente local como recurso independente, sem alimentar os KPIs da demo.

## Checklist de publicação

- [x] Implementação e testes do domínio avançado;
- [x] Interface Streamlit com exportações;
- [x] CI Python 3.10, 3.12, 3.14 e PostgreSQL;
- [x] Smoke test real de Chrome com viewport móvel;
- [x] Deploy Render com dados sintéticos;
- [x] Confirmar CI verde do commit `1586b8e` apontado pela tag: https://github.com/juceliocoelho2022/cx-intelligence/actions/runs/40106620236;
- [x] Tag `v1.3.0` criada e Release publicada em https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.3.0;
- [x] Conferir o URL da Release depois da publicação;
- [ ] Opcional: inspeção manual da nova aba Analytics no Android físico para complementar a emulação móvel.

**Documentação de negócio e metodologia:** [ADVANCED_CX_V1.3.md](ADVANCED_CX_V1.3.md). **Histórico da beta:** [RELEASE_NOTES_V1.3.0_BETA.md](RELEASE_NOTES_V1.3.0_BETA.md).

## Nota editorial sobre a descrição da GitHub Release

A descrição digitada durante a publicação da Release reutilizou texto de **pré-lançamento** e ainda contém frases como "não devem ser anunciadas até sua criação". Essas frases **já não refletem o estado do repositório**. O arquivo no branch `main` está corrigido; a descrição da Release já publicada deve ser ajustada em **Edit release**, retirando a orientação anterior. A tag `v1.3.0` permanece fixa no commit original e não incorpora automaticamente atualizações posteriores do README nem destas notas.
