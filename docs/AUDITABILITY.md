# Qualidade analítica e rastreabilidade — v0.8

## Escopo
Manifesto JSON reproduzível do **recorte filtrado**. Não existe banco de auditoria, assinatura digital, autenticação ou repositório histórico automático nesta versão.

## Regras de negócio
- **RN-AUD-01:** antes de emitir manifesto, validar esquema, domínios, duplicidades de ID e ausência de valores nulos pelo validador atual.
- **RN-AUD-02:** recomputar KPIs no mesmo recorte e exigir igualdade com os indicadores no relatório.
- **RN-AUD-03:** verificar período mínimo e máximo, número de registros e unicidade dos tickets.
- **RN-AUD-04:** ordenar o conjunto pelo identificador do ticket e normalizar representação de datas e duração para um hash SHA-256 estável entre ordens de linhas.
- **RN-AUD-05:** manifesto contém hash, versão, data mínima/máxima, origem declarada, contagem, checks e KPIs — **não inclui linhas individuais**.
- **RN-AUD-06:** exportações incluem ressalva explícita de dados sintéticos e de que hash não comprova origem, integridade histórica nem completude de ingestão.
- **RN-AUD-07:** fonte é uma declaração da configuração do app, e não uma evidência autenticada de proveniência.

## Como usar
Na aba **Relatório executivo**, gere o memo e exporte o manifesto JSON do recorte. Alterar dados do recorte altera o hash; reordenar registros não altera.

## Limites
Um SHA-256 sem assinatura serve para comparar conteúdo, não oferece certificação de origem. Para auditoria corporativa são necessários identificação imutável da carga, retenção, versionamento de regras, assinatura/autenticação, cobertura temporal e trilhas persistentes.
