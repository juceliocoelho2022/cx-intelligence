"""Educational sentiment NLP on fictional messages; no real customer conversations."""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.model_selection import train_test_split

EXAMPLES = {
 "positivo": [
  "Atendimento excelente, meu problema foi resolvido rapidamente",
  "Gostei muito do suporte, equipe atenciosa e eficiente",
  "Consegui usar o aplicativo sem dificuldade, muito bom",
  "Minha transferência foi concluída, tudo funcionou perfeitamente",
  "Recebi uma orientação clara e fui bem atendido",
  "O atendente explicou com paciência e resolveu minha dúvida",
  "Experiência ótima, atendimento rápido e cordial",
  "Meu cartão foi desbloqueado, obrigado pelo suporte",
  "Consegui acessar a conta, estou satisfeito com o serviço",
  "Equipe prestativa, finalmente consegui fazer o pix"
 ],
 "negativo": [
  "Meu problema continua sem solução e estou frustrado",
  "Atendimento muito demorado e ninguém resolve minha solicitação",
  "Não consigo acessar o aplicativo, estou insatisfeito",
  "Minha transferência falhou e não recebi nenhuma explicação",
  "Suporte ruim, tive que repetir meu problema várias vezes",
  "Meu cartão permanece bloqueado mesmo após o atendimento",
  "Péssima experiência, a equipe não conseguiu ajudar",
  "O aplicativo trava toda hora, isso é inaceitável",
  "Minha reclamação não foi resolvida, muito decepcionante",
  "Estou irritado com a demora para liberar o pix"
 ],
 "neutro": [
  "Gostaria de saber como consultar meu saldo",
  "Solicito informações sobre o prazo de uma transferência",
  "Preciso verificar o status do meu atendimento",
  "Como faço para alterar o limite do cartão",
  "Quero entender os horários disponíveis para suporte",
  "Poderiam explicar onde encontro o extrato da conta",
  "Preciso consultar as tarifas disponíveis",
  "Gostaria de atualizar meus dados de cadastro",
  "Qual o procedimento para redefinir a senha",
  "Quero saber como solicitar um novo cartão"
 ]
}

def make_dataset():
    """Thirty independent templates: do not augment before splitting."""
    return pd.DataFrame([(msg, label) for label, messages in EXAMPLES.items() for msg in messages],
                        columns=["message", "sentiment"])

def train_sentiment(data=None):
    """Held-out illustrative evaluation; very small sample, not production evidence."""
    data = make_dataset() if data is None else data.copy()
    if data.message.isna().any() or data.sentiment.isna().any():
        raise ValueError("Mensagens e rótulos não podem ser nulos")
    if data.message.duplicated().any():
        raise ValueError("Mensagens duplicadas podem contaminar a avaliação")
    if len(data) < 15 or data.sentiment.value_counts().min() < 4:
        raise ValueError("Amostra insuficiente para avaliação estratificada")
    x_train,x_test,y_train,y_test=train_test_split(data.message,data.sentiment,
        test_size=.3, random_state=42,stratify=data.sentiment)
    model=Pipeline([
        ("tfidf",TfidfVectorizer(strip_accents="unicode",ngram_range=(1,2),max_features=1500)),
        ("classifier",LogisticRegression(max_iter=1000,random_state=42))
    ])
    model.fit(x_train,y_train)
    pred=model.predict(x_test)
    labels=["negativo","neutro","positivo"]
    return model,{
        "accuracy":round(float(accuracy_score(y_test,pred)),3),
        "f1_macro":round(float(f1_score(y_test,pred,average="macro")),3),
        "test_rows":int(len(y_test)),
        "report":classification_report(y_test,pred,labels=labels,output_dict=True,zero_division=0),
        "confusion":confusion_matrix(y_test,pred,labels=labels).tolist(),
        "labels":labels
    }

def classify_message(model, message):
    if not isinstance(message,str) or not message.strip():
        raise ValueError("Informe uma mensagem não vazia")
    probs=model.predict_proba([message])[0]
    classes=model.named_steps["classifier"].classes_
    top=int(np.argmax(probs))
    return {"sentiment":str(classes[top]), "score":round(float(probs[top]),3),
            "probabilities":{str(k):round(float(v),3) for k,v in zip(classes,probs)}}

if __name__=="__main__":
    _,metrics=train_sentiment()
    print({k:v for k,v in metrics.items() if k not in ("report","confusion")})
