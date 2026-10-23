# CX Intelligence — roteiro de apresentação para portfólio (v1.0 candidata)

> Projeto independente, com instituição e atendimentos fictícios. Sem vínculo com qualquer banco real.

## Pitch de 60 segundos
O CX Intelligence transforma tickets simulados de atendimento em indicadores executivos de satisfação, volume, resolução e reincidência. Um pipeline Python gera e valida dados sintéticos; PostgreSQL opcional recebe cargas idempotentes; Streamlit permite explorar KPIs e recortes. Há experiências separadas de risco supervisionado e NLP, além de alertas heurísticos, diagnóstico por segmento e exportação de relatório executivo com manifesto SHA-256 do conjunto analisado. Os resultados são demonstrativos e não fundamentam decisões sobre clientes reais.

## Demonstração de 5 minutos
1. **Contexto e fonte** (30 s): abrir a home, indicar que o dataset é sintético e mostrar a origem CSV ou PostgreSQL.
2. **Indicadores** (60 s): visão executiva e filtros; explicar CSAT positivo (notas 4–5), resolução (não FCR), duração em horas e reincidência simulada.
3. **Investigação** (60 s): diagnóstico de segmentos por assunto/canal e diferença em pontos percentuais; não confundir correlação e causa.
4. **Alertas** (45 s): picos por semana ISO com baseline de quatro semanas e limites heurísticos; diferenças não provam incidente.
5. **Relatório + auditoria** (60 s): gerar memo Markdown e baixar JSON do manifesto; mostrar hash SHA-256, contagem e verificações.
6. **Engenharia e limites** (45 s): executar os testes, mostrar workflow do GitHub, documentos de regras e roadmap.

## Evidências recomendadas
- Print do workflow verde na aba Actions, após verificação real.
- Capturas das abas Visão executiva, Diagnóstico CX, Alertas CX e Relatório executivo.
- Saída de `python -m pytest -q` executado na mesma revisão.
- No PostgreSQL, demonstrar duas cargas idênticas e contagem idempotente sem expor credenciais.
- CSV, Markdown e JSON de amostras sintéticas, se fizer sentido publicar.

## Checklist de aceite da v1.0
- [ ] Testes locais passaram sem erros.
- [ ] Workflow Actions passou nas versões de Python configuradas.
- [ ] Streamlit abre e renderiza todas as abas sem erro.
- [ ] Banco PostgreSQL (quando habilitado) conecta e mostra dados corretos.
- [ ] Relatório e manifesto foram baixados e conferidos.
- [ ] Documentação não afirma deploy público, uso de clientes reais ou causalidade comprovada.
- [ ] Nenhum segredo, senha, arquivo de ambiente ou registro pessoal foi incluído no repositório.

## Limites de uso
Não é uma solução em produção nem possui monitoramento real, SLA, certificação LGPD, previsão validada em clientes reais ou deploy público verificado. O hash do manifesto não autentica a origem dos dados. Para uso corporativo, seriam necessários governança, autenticação, observabilidade e testes sobre dados devidamente autorizados.
