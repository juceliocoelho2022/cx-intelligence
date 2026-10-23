from pathlib import Path
import numpy as np
import pandas as pd

CHANNELS = ['Chat', 'Telefone', 'App', 'Email']
TOPICS = ['Pix', 'Cartão', 'Conta', 'Empréstimo', 'Acesso ao app', 'Tarifas']

def generate_data(n=4000, seed=42):
    """Dados 100% fictícios. Inclui sinais sintéticos para demonstração."""
    rng = np.random.default_rng(seed)
    base_date = pd.Timestamp('2026-08-01')
    customer_ids = rng.integers(1, max(80, n // 5), size=n)
    channel = rng.choice(CHANNELS, n, p=[.46, .18, .28, .08])
    topic = rng.choice(TOPICS, n, p=[.28, .19, .17, .13, .15, .08])
    resolution_hours = np.clip(rng.gamma(2.2, 5.0, n), 0.1, 96).round(2)
    resolved = (rng.random(n) > (.08 + .004 * resolution_hours)).astype(int)
    sentiment = rng.choice(['positivo', 'neutro', 'negativo'], n, p=[.38, .30, .32])
    score = 4.5 - .032 * resolution_hours - .85 * (1-resolved) - .65*(sentiment=='negativo')
    csat = np.clip(np.rint(score + rng.normal(0, .8, n)), 1, 5).astype(int)
    date = base_date + pd.to_timedelta(rng.integers(0, 80, n), unit='D')
    data = pd.DataFrame({'ticket_id': [f'T{v:06d}' for v in range(1,n+1)],
        'customer_id': [f'C{v:05d}' for v in customer_ids], 'date': date,
        'channel':channel, 'topic':topic, 'resolution_hours': resolution_hours,
        'resolved':resolved, 'sentiment':sentiment, 'csat':csat})
    data = data.sort_values(['customer_id','date','ticket_id']).reset_index(drop=True)
    data['previous_tickets'] = data.groupby('customer_id').cumcount()
    # Alvo prospectivo ilustrativo, gerado apenas após definição dos atributos de entrada.
    prob = np.clip(.07 + .12*(sentiment=='negativo') + .09*(csat<=2) +
                   .08*(1-resolved) + .045*(data['previous_tickets']>=2), .01, .8)
    data['repeat_contact_30d'] = rng.binomial(1, prob.to_numpy())
    return data.sort_values('ticket_id').reset_index(drop=True)

def validate_data(df):
    required = {'ticket_id','customer_id','date','channel','topic','resolution_hours',
                'resolved','sentiment','csat','previous_tickets','repeat_contact_30d'}
    missing = required.difference(df.columns)
    errors=[]
    if missing: errors.append(f'Colunas ausentes: {sorted(missing)}'); return errors
    if df['ticket_id'].isna().any() or df['ticket_id'].duplicated().any(): errors.append('ticket_id nulo ou duplicado')
    if df[list(required)].isna().any().any(): errors.append('Valores nulos encontrados')
    if not df['csat'].between(1,5).all(): errors.append('CSAT fora do intervalo 1..5')
    if not df['resolution_hours'].ge(0).all(): errors.append('Tempo de resolução negativo')
    for col in ['resolved','repeat_contact_30d']:
        if not df[col].isin([0,1]).all(): errors.append(f'{col} não binário')
    return errors

def kpis(df):
    return {'total_tickets':int(len(df)), 'csat_pct':round(100*df['csat'].ge(4).mean(),1),
            'fcr_proxy_pct':round(100*df['resolved'].mean(),1),
            'avg_resolution_hours':round(df['resolution_hours'].mean(),1),
            'repeat_contact_rate_pct':round(100*df['repeat_contact_30d'].mean(),1)}

def get_or_create(path='data/cx_tickets.csv', n=4000):
    path=Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        generate_data(n=n).to_csv(path,index=False)
    df=pd.read_csv(path,parse_dates=['date'])
    errors=validate_data(df)
    if errors: raise ValueError('; '.join(errors))
    return df

if __name__ == '__main__':
    df=get_or_create()
    print(kpis(df))
