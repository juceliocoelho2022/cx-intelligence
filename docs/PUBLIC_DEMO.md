# CX Intelligence v1.2 — Demonstração pública segura

## Objetivo
Disponibilizar um dashboard Streamlit de portfólio em modo **100% sintético**. Este deploy não necessita PostgreSQL, CSV do Kaggle, credenciais de terceiros nem dados de clientes.

## Configuração do Render (Python)
- **Plano:** Free (sem instâncias pagas, sujeito a suspensão por inatividade e limitações de memória).
- **Repositório:** `https://github.com/juceliocoelho2022/cx-intelligence`
- **Branch:** `main`
- **Build:** `python -m pip install -r requirements.txt`
- **Start:** `python -m streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`
- **Env:** `CX_PUBLIC_DEMO=true`, `CX_DATA_SOURCE=csv`, `PYTHON_VERSION=3.12.11`, `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`.

O Render exige escuta em `0.0.0.0:$PORT`. `PYTHON_VERSION` fixa uma versão testada pelo CI e evita mudanças inesperadas na versão padrão.

## Comportamento intencional
- Os 4.000 tickets demonstrativos são gerados deterministicamente na inicialização se o arquivo não existir, com `src.pipeline.get_or_create()`.
- O dashboard executivo, a exploração, NLP experimental e relatórios continuam disponíveis; métricas não representam clientes reais.
- As abas **Histórico de tickets** e **Kaggle externo** exibem mensagens explicando por que essas fontes não estão disponíveis no servidor público.
- Nenhum `DATABASE_URL`, senha de PostgreSQL, token Kaggle, CSV Kaggle ou mensagem de cliente real é enviado ao Render.
- Não publicar arquivos da pasta `data/raw`; o Git os ignora.

## Como conferir após deploy
1. Confirmar que o serviço chegou a `Live` no Render, sem exceções em logs.
2. Abrir o URL público informado pelo Render e conferir os 4.000 tickets na Visão executiva.
3. Abrir NLP, Relatório executivo e o filtro de assunto para verificar uma interação.
4. Conferir aviso de modo público nas abas Histórico de tickets e Kaggle externo.
5. Checar que o deploy não expôs variáveis de ambiente ou downloads não autorizados.

## Limitações
- A camada local PostgreSQL e a integração Kaggle foram validadas separadamente; a demo pública é propositalmente mais restrita.
- Dados gerados sinteticamente e avaliações ML não são validação externa.
- Disco efêmero no plano gratuito; regeneração determinística ao reiniciar.
- A instância gratuita pode dormir em períodos de inatividade e demorar a responder na primeira visita.
- Nenhuma representação de vínculo comercial com instituição financeira.
