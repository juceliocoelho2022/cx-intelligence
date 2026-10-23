# NLP e análise de sentimentos — protótipo v0.4

## Objetivo
Demonstrar a sequência `mensagem sintética -> TF-IDF -> classificador -> avaliação -> previsão exploratória`. Nenhuma conversa real ou dado confidencial é utilizado.

## Dados
30 frases **redigidas artificialmente** em português, dez por classe (`positivo`, `neutro`, `negativo`). O conjunto é muito pequeno, com vocabulário padronizado e padrões artificiais. O classificador **não** é uma solução operacional de sentiment analysis.

## Metodologia
- Divisão estratificada de 70% treinamento e 30% teste com semente fixa 42, **antes** de ajustar o TF-IDF.
- TF-IDF com unigramas e bigramas, remoção de acentos; regressão logística multiclasses.
- Métricas: accuracy, F1 macro, precision/recall/F1 por classe e matriz de confusão.
- Inferência interativa produz classe e probabilidades **não calibradas**. Valores não devem ser tratados como confiança estatisticamente validada.

## Regras de negócio
- RN-NLP-01: apenas dados fictícios, sem PII, em demonstrações públicas.
- RN-NLP-02: mensagem vazia é rejeitada.
- RN-NLP-03: novo texto é previsão exploratória; não representa sentimento de cliente real.
- RN-NLP-04: métricas de teste são exibidas com tamanho da amostra e limitações.
- RN-NLP-05: rótulos sintéticos do CSV de tickets são **independentes** do modelo NLP; não inferir que o modelo classificou esses tickets.
- RN-NLP-06: nenhum resultado pode acionar decisão automática adversa.

## Como validar
```powershell
python -m pytest -q
python -m src.nlp
streamlit run app.py
```

## Próximos passos científicos
Dataset maior com variação linguística, linguagem informal/ambígua, revisão de rótulos, validação cruzada repetida, F1 macro com intervalos de confiança, análises de erros, teste fora da distribuição, privacidade e avaliação de drift. Só após validações independentes comparar com modelos de linguagem maiores.
