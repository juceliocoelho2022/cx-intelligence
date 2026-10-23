# CX Intelligence v1.0.0 — Notas de release

**Status:** versão demonstrativa de portfólio, homologada pelo autor; não é uma solução bancária em produção.

## Destaques
- Dashboard Streamlit de Customer Experience com filtros de assunto, canal e período.
- Dados de tickets **100% sintéticos**, validados e reprodutíveis.
- ETL PostgreSQL opcional com UPSERT idempotente e histórico de cargas bem-sucedidas.
- Baseline supervisionado para reincidência sintética e NLP experimental de frases fictícias.
- Detecção heurística de picos semanais e diagnóstico descritivo por canal/assunto.
- Relatório executivo Markdown com recomendações para investigação.
- Manifesto JSON com hash SHA-256 determinístico, verificações de consistência e limitações declaradas.
- 35 testes automatizados aprovados localmente em Python 3.14.8; workflow GitHub Actions em Python 3.10, 3.12 e 3.14. A conferência individual de cada job é separada da validação local.

## Executar
```powershell
git clone https://github.com/juceliocoelho2022/cx-intelligence.git
cd cx-intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

Para usar PostgreSQL, consulte `docs/POSTGRES_ETL.md`.

## Transparência metodológica
- Taxa de resolução **não é** FCR.
- Reincidência é rótulo sintético; **não** é churn observado.
- A classificação NLP é experimental e não gera o campo `sentiment` dos tickets.
- Os alertas são heurísticas, não previsões validadas nem prova de causa raiz.
- O manifesto não tem assinatura digital nem certificação de proveniência.
- Não há vínculo oficial com o Banco Inter ou outra instituição.

## Recursos
- [Demonstração para portfólio](docs/PORTFOLIO_DEMO.md)
- [Regras de negócio](docs/BUSINESS_RULES.md)
- [Dicionário de dados](docs/DATA_DICTIONARY.md)
- [Auditoria e rastreabilidade](docs/AUDITABILITY.md)
