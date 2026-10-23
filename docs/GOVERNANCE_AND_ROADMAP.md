# Qualidade, governança, avaliação e roadmap

## Dados e ética
- **Natureza dos dados:** completamente sintéticos. Nenhum vínculo com clientes ou datasets internos de empresas.
- **LGPD:** nunca publicar PII, conversas reais, dados bancários, chaves de API ou credenciais.
- **IA responsável:** score é experimental, não causal e não adequado a decisões reais sobre pessoas.
- **Proveniência:** registrar versão de código, seed, parâmetros de geração, esquema e momento da carga.
- **Segurança futura:** RBAC, segregação de ambientes, criptografia, mascaramento, retenção e auditoria.

## Estratégia de testes
1. **Unitários:** regras de geração, filtros e fórmulas de KPI, incluindo tabela vazia.
2. **Contrato de dados:** obrigatoriedade, unicidade, tipos, domínios e integridade temporal.
3. **Integração:** leitura/escrita CSV; migrações/queries PostgreSQL quando integrado.
4. **ML:** holdout temporal, checagem de leakage, distribuição de classes, benchmark de baseline, calibração e drift.
5. **UI:** filtros, estados sem dados, unidades, títulos e exportação.
6. **Segurança:** revisão de dependências e escaneamento de segredos antes de publicar.

## Cuidados metodológicos
O gerador incorpora dependências sintéticas entre satisfação, resolução, sentimento e reincidência, tornando parte do sinal do classificador previsível **por construção**. Métricas positivas aqui não provam capacidade preditiva sobre clientes reais.

Na evolução, criar um simulador de **eventos temporais observáveis** e excluir dos rótulos os períodos censurados. Avaliar primeiro regressão logística versus baseline simples, PR-AUC, ROC-AUC, recall/precision no limiar proposto, curva de calibração e estabilidade por canal/assunto. Definir o custo de falsos positivos/negativos com o negócio.

## Entregas planejadas
| Versão | Foco | Definition of Done |
| --- | --- | --- |
| v0.2 | Qualidade + UI | Contrato de dados e fórmulas testadas; filtros, unidades e estados vazios claros |
| v0.3 | Persistência | PostgreSQL e ETL idempotente; Docker Compose; testes SQL |
| v0.4 | NLP | Textos artificiais, taxonomia e comparação quantitativa de modelos |
| v0.5 | Predição | Alvo temporal observável, censura, validação rolling-window e calibração |
| v1.0 | Operação demo | CI, alertas com trilha de auditoria, observabilidade e demonstração online |

## Princípio orientador
**Primeiro medir corretamente; depois prever; finalmente automatizar.** A cada versão, atualizar documentação, testes e limitações, sem prometer recursos que ainda não existem.
