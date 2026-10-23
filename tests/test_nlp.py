import pytest
from src.nlp import make_dataset, train_sentiment, classify_message, compare_models

def test_dataset_is_balanced_and_unique():
    df=make_dataset()
    assert len(df)==60
    assert df.message.is_unique
    assert df.sentiment.value_counts().to_dict()=={"positivo":20,"negativo":20,"neutro":20}

def test_model_evaluation_is_reproducible():
    _,a=train_sentiment()
    _,b=train_sentiment()
    assert a==b
    assert a["test_rows"]==18
    assert 0<=a["f1_macro"]<=1

def test_inference_probabilities():
    model,_=train_sentiment()
    result=classify_message(model,"Preciso saber como consultar minha conta")
    assert result["sentiment"] in ("positivo","neutro","negativo")
    assert abs(sum(result["probabilities"].values())-1)<.01

def test_rejects_empty_input():
    model,_=train_sentiment()
    with pytest.raises(ValueError):
        classify_message(model,"  ")

def test_compare_models_uses_same_holdout():
    comparison, mistakes = compare_models()
    assert set(comparison.modelo) == {"LogisticRegression", "MultinomialNB", "LinearSVC"}
    assert comparison.amostra_teste.eq(18).all()
    assert comparison.f1_macro.between(0, 1).all()
    assert set(mistakes.columns) == {"modelo", "mensagem", "real", "previsto"}
