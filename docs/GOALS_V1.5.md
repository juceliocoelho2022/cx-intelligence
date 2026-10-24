# CX Intelligence v1.5 (beta) — Metas e planos de ação

**Status: implementação experimental na `main`, sem tag ou GitHub Release v1.5.**
Última release estável: [v1.4.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.4.0).

## Objetivo demonstrativo

A aba **🎯 Metas v1.5** relaciona indicadores sintéticos a metas de referência e ações **propostas** no navegador. Ela é um protótipo de acompanhamento de gestão, **não** um sistema de tarefas real, integração empresarial ou avaliação de pessoas.

A implementação nunca salva ações em PostgreSQL, não envia e-mails e não agenda lembretes. Cada visitante tem sua própria memória de sessão do Streamlit; ao perder a sessão o plano desaparece. Exporte `JSON` ou `Markdown` para guardar um exemplo offline; **não existe importação de volta ao app**.

## Regras de negócio e fórmulas

A medição usa o motor `compare_periods` da v1.4, portanto os dados são os **tickets sintéticos do conjunto principal** com os filtros de assunto e canal aplicados. O Kaggle é isolado.

O usuário escolhe janelas de **7, 14 ou 30 dias** cujo final corresponde à data final do filtro lateral; o início do filtro lateral não interfere no tamanho da janela. São consideradas apenas as observações do período atual, não a variação contra a janela anterior.

| Indicador | Meta inicial fictícia | Sentido desejado | Distância para a meta |
| --- | ---: | --- | --- |
| CSAT positivo (notas 4/5) | 70% | maior ou igual | `max(0, meta - observado)` pontos percentuais |
| Tickets resolvidos | 90% | maior ou igual | `max(0, meta - observado)` pontos percentuais |
| Tempo médio dos tickets | 10 horas | menor ou igual | `max(0, observado - meta)` horas |

Cada meta pode ser alterada na interface; esses valores não foram fornecidos por instituição financeira e **não constituem SLAs, benchmarks de mercado ou recomendações estatísticas**.

### Estados de avaliação de metas

- `met`: valor observado satisfaz o limite configurado.
- `attention`: valor não alcança o limite; apresenta distância com unidade correta.
- `no_data`: nenhum ticket no recorte.
- `insufficient_sample`: menos tickets que o mínimo selecionado.
- `incomplete_window`: a data inicial do histórico principal está após o começo da janela; não há conclusão.
- `missing_metric`: a métrica não está disponível.

A cobertura é inferida a partir da data inicial do dataset inteiro; ela **não** certifica ingestão contínua, amostragem representativa ou qualidade dos registros. Os indicadores são agregações descritivas. Uma meta atingida **não demonstra impacto de intervenção**.

## Plano de ação da sessão

Cada registro possui: ID sequencial local `A0001`, indicador vinculado, título, hipótese de investigação, **área fictícia** de responsabilidade, prazo proposto, data de criação, estado atual e eventos de mudança de estado. O recorte de assunto, canal e datas é guardado junto à ação para evitar confusão quando os filtros mudarem.

Estados e transições permitidas:

```text
Planejada -> Em andamento -> Concluída
                 |
                 +--------> Planejada
```

Não é permitido concluir diretamente uma ação planejada nem reabrir uma concluída. Os eventos antigos não são alterados; a função retorna uma nova lista. Prazos anteriores à criação e mudanças com data anterior ao evento mais recente são recusados.

### Exportação e segurança

- JSON UTF-8 com campos explicitamente estruturados, serialização determinística (`sort_keys=True`) e `schema_version: 1.5.0-beta`; valores não finitos são rejeitados.
- Markdown: tabela de metas, ações propostas e aviso de limitações. Nomes de ações têm limite de 120 caracteres; hipóteses, 400; quebras de linha e caracteres de controle são rejeitados.
- O conteúdo digitado pertence apenas à sessão em memória. Evite inserir **dados pessoais reais, informações bancárias ou segredos**, já que este é um projeto demonstrativo público.
- O indicador de conclusão do plano significa somente uma **alteração fictícia de estado** no aplicativo, sem comprovar alteração nos KPIs.

## Testes e critérios de aceite

`tests/test_cx_goals.py` cobre direção do alvo, limites, ausência/amostra insuficiente, dados inválidos, IDs, transições, histórico, ausência de mutação, exportações determinísticas e Markdown seguro. O Chrome mobile deve verificar controles, entrada de ação e arquivos exportados.

### Executar localmente (Windows PowerShell)

```powershell
git pull origin main
python -m pytest -q
streamlit run app.py
```

Acesse a aba **🎯 Metas v1.5**. Altere a meta, crie uma ação de investigação fictícia, inicie sua execução simulada, exporte o plano e confira o aviso de escopo.

**Critério para eventual promoção:** testes Python 3.10/3.12/3.14 e Chrome mobile verdes, revisão da documentação, Render publicado, e confirmação de exportações públicas, sem comprometer as limitações metodológicas.
