import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from src.pipeline import get_or_create

FEATURES = ['channel', 'topic', 'resolution_hours', 'resolved', 'sentiment', 'csat', 'previous_tickets']
CATEGORICAL = ['channel', 'topic', 'sentiment']
NUMERICAL = ['resolution_hours', 'resolved', 'csat', 'previous_tickets']

def train_and_evaluate(df):
    """Split temporal: evita treinar em eventos posteriores aos do teste.
    Dataset sintético: resultados não representam desempenho real de CX.
    """
    ordered=df.sort_values(['date', 'ticket_id'])
    split=int(len(ordered)*.8)
    train, test=ordered.iloc[:split], ordered.iloc[split:]
    prep=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore'),CATEGORICAL),
                            ('num','passthrough',NUMERICAL)])
    clf=Pipeline([('prepare',prep),('classify',LogisticRegression(max_iter=1500, random_state=42))])
    clf.fit(train[FEATURES],train['repeat_contact_30d'])
    probs=clf.predict_proba(test[FEATURES])[:,1]
    actual=test['repeat_contact_30d']
    metrics={'test_rows':len(test), 'prevalence':round(float(actual.mean()),3),
             'roc_auc':round(float(roc_auc_score(actual,probs)),3) if actual.nunique()>1 else None,
             'average_precision':round(float(average_precision_score(actual,probs)),3)}
    out=test[['ticket_id','date','topic','channel','csat','sentiment','repeat_contact_30d']].copy()
    out['risk_score']=np.round(probs,3)
    return clf,metrics,out.sort_values('risk_score',ascending=False)

if __name__=='__main__':
    _,m,_=train_and_evaluate(get_or_create())
    print(m)
