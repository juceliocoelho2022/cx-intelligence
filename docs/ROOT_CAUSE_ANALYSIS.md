# CX Root Cause Investigation — v0.6

## Missão
Descobrir **segmentos candidatos à investigação**, não afirmar causas. A análise cruza assunto × canal e compara CSAT positivo e taxa de resolução de cada grupo contra o total filtrado.

## Regras de negócio
- **RN-INS-01:** somente segmentos com no mínimo 30 tickets (limiar configurável no código) entram no relatório.
- **RN-INS-02:** CSAT = 100 × notas 4–5 / notas válidas; resolução = 100 × resolvidos / tickets.
- **RN-INS-03:** referência = todos os registros do recorte, inclusive o segmento comparado. É um benchmark descritivo, não uma comparação com grupo de controle.
- **RN-INS-04:** lacunas são calculadas em **pontos percentuais (pp)**: taxa do segmento menos taxa global.
- **RN-INS-05:** 'Prioritário' quando **CSAT e resolução** estiverem pelo menos 5 pp abaixo da referência; 'Investigar' quando uma estiver pelo menos 5 pp abaixo; senão 'Monitorar'.
- **RN-INS-06:** recomendações significam **hipóteses de investigação**, sujeitas à validação pelo negócio.
- **RN-INS-07:** valores inválidos, ausentes ou limites não válidos resultam em erro explícito; sem registros elegíveis retorna tabela vazia.
- **RN-INS-08:** diferenças de composição, amostragem, sazonalidade e tamanho do segmento podem explicar variações. Não alegar causalidade nem significância estatística.

## Interpretação
Exemplo: Pix/Chat com CSAT 50% e total 65% apresenta gap **-15 pp**. Hipóteses: complexidade das solicitações, fluxos de atendimento, composição dos clientes, tempo de resolução. A métrica por si só **não estabelece** o motivo.

## Validação e próximos avanços
`python -m pytest -q`. Futuramente avaliar intervalos de confiança, estratificação por período e perfil, mínimos amostrais dinâmicos, persistência de descobertas, registro de hipóteses e resultado das ações.
