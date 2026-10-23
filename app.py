import streamlit as st
import plotly.express as px
import pandas as pd
from src.pipeline import get_or_create, kpis
from src.model import train_and_evaluate

st.set_page_config(page_title='CX Intelligence | Analytics',page_icon='📊',layout='wide')
st.title('CX Intelligence')
st.caption('Customer Experience Analytics | Portfólio demonstrativo — dados integralmente sintéticos')
@st.cache_data
def load(): return get_or_create()
df=load()
with st.sidebar:
    st.header('Filtros')
    topics=st.multiselect('Assunto',sorted(df.topic.unique()),default=sorted(df.topic.unique()))
    channels=st.multiselect('Canal',sorted(df.channel.unique()),default=sorted(df.channel.unique()))
filtered=df[df.topic.isin(topics)&df.channel.isin(channels)].copy()
if filtered.empty:
    st.warning('Sem registros para os filtros selecionados.'); st.stop()
metrics=kpis(filtered)
cols=st.columns(5)
for col, label, value in zip(cols,['Atendimentos','CSAT (4–5)','Resolvidos*','Tempo médio (h)','Reincidência simulada'],
       [metrics['total_tickets'],f"{metrics['csat_pct']}%",f"{metrics['fcr_proxy_pct']}%",metrics['avg_resolution_hours'],f"{metrics['repeat_contact_rate_pct']}%"]):
    col.metric(label,value)
st.caption('* Percentual resolvido; não é FCR real. Reincidência e sentimento são campos simulados.')
tab1,tab2,tab3,tab4=st.tabs(['Visão executiva','Voz do cliente','Risco preditivo','Qualidade e dicionário'])
with tab1:
    a,b=st.columns(2)
    daily=filtered.assign(day=filtered.date.dt.date).groupby('day',as_index=False).agg(tickets=('ticket_id','count'),csat=('csat',lambda s:100*s.ge(4).mean()))
    with a: st.plotly_chart(px.line(daily,x='day',y='tickets',title='Volume diário de chamados'),use_container_width=True)
    with b: st.plotly_chart(px.line(daily,x='day',y='csat',title='CSAT diário (%)'),use_container_width=True)
    st.plotly_chart(px.bar(filtered.groupby('topic',as_index=False).agg(tickets=('ticket_id','count')),x='topic',y='tickets',title='Volume por tema'),use_container_width=True)
with tab2:
    count=filtered.groupby(['topic','sentiment']).size().reset_index(name='chamados')
    st.plotly_chart(px.bar(count,x='topic',y='chamados',color='sentiment',barmode='stack',title='Sentimentos simulados por tema'),use_container_width=True)
    st.dataframe(filtered.groupby('topic').agg(atendimentos=('ticket_id','count'),csat_medio=('csat','mean'),tempo_medio_h=('resolution_hours','mean')).round(2),use_container_width=True)
with tab3:
    st.info('Modelo supervisionado treinado com dados sintéticos. Alvo: reincidência futura simulada. Não usar scores para decisões sobre clientes reais.')
    _,m,pred=train_and_evaluate(df)
    c1,c2,c3=st.columns(3)
    c1.metric('ROC-AUC (holdout temporal)',m['roc_auc'])
    c2.metric('Average Precision',m['average_precision'])
    c3.metric('Prevalência no teste',f"{m['prevalence']*100:.1f}%")
    st.dataframe(pred[pred.topic.isin(topics)&pred.channel.isin(channels)].head(100),use_container_width=True)
with tab4:
    st.write('**Validações:** identificadores únicos, campos obrigatórios, CSAT 1–5, duração não negativa e indicadores binários.')
    st.dataframe(pd.DataFrame({'coluna':df.columns,'tipo':df.dtypes.astype(str).values}),use_container_width=True)
    st.download_button('Exportar registros filtrados (CSV)',filtered.to_csv(index=False).encode('utf-8'),'cx_filtrado.csv','text/csv')
