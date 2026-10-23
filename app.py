"""CX Intelligence — dashboard executivo v0.2 (dados integralmente sintéticos)."""
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.pipeline import get_or_create, kpis, validate_data
from src.database import load_tickets
from src.model import train_and_evaluate
from src.nlp import train_sentiment, classify_message, compare_models
from src.anomalies import detect_volume_anomalies, weekly_volumes
from src.insights import segment_insights

st.set_page_config(page_title="CX Intelligence | Customer Experience", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
COLORS = {"orange": "#FF792D", "cyan": "#28B8F6", "green": "#34D399", "red": "#FB7185", "muted": "#9BA9C0"}
PLOT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#DCE7F6"), margin=dict(l=15,r=15,t=45,b=20))
st.markdown("""
<style>
.stApp {background:linear-gradient(135deg,#081323 0%,#0C1B30 60%,#101827 100%);color:#E9F0FA}
[data-testid="stSidebar"] {background:#111F31}
h1,h2,h3 {letter-spacing:-.025em}
.hero {background:linear-gradient(110deg,#16243B,#09182D);padding:25px 28px;border:1px solid #304259;border-radius:17px;margin-bottom:16px}
.eyebrow {letter-spacing:.18em;color:#FF934A;font-size:.73rem;font-weight:700;text-transform:uppercase}
.hero h1 {color:#F7FAFE;margin:.25rem 0;font-size:2.35rem}
.hero p {margin:0;color:#B4C2D7}
.note {border-left:3px solid #FF792D;background:#19263B;padding:12px 15px;border-radius:5px;margin:16px 0;font-size:.87rem;color:#CBD6E6}
[data-testid="stMetric"] {background:#12243A;border:1px solid #2E4057;padding:16px;border-radius:14px;min-height:123px}
[data-testid="stMetricLabel"] {color:#ADBFD5}
[data-testid="stMetricValue"] {color:#F2F7FE;font-size:1.8rem}
[data-testid="stTabs"] button[aria-selected="true"] {color:#FF792D}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return load_tickets() if os.getenv('CX_DATA_SOURCE','csv').lower() == 'postgres' else get_or_create()

def chart(fig):
    fig.update_layout(**PLOT)
    st.plotly_chart(fig, use_container_width=True)

df=load_data()
st.sidebar.markdown("### 📊 CX Intelligence")
st.sidebar.caption("Exploração analítica — ambiente demonstrativo")
st.sidebar.divider()
topics=st.sidebar.multiselect("Assunto",sorted(df.topic.unique()),default=sorted(df.topic.unique()))
channels=st.sidebar.multiselect("Canal",sorted(df.channel.unique()),default=sorted(df.channel.unique()))
dates=st.sidebar.date_input("Período",value=(df.date.min().date(),df.date.max().date()),min_value=df.date.min().date(),max_value=df.date.max().date())
subset=df[df.topic.isin(topics)&df.channel.isin(channels)].copy()
if len(dates)==2:
    start,end=dates
    subset=subset[subset.date.dt.date.between(start,end)]
st.sidebar.divider()
st.sidebar.caption("🔒 Dataset sintético · Sem dados pessoais reais")
st.sidebar.caption("Fonte: " + ("PostgreSQL" if os.getenv("CX_DATA_SOURCE","csv").lower()=="postgres" else "CSV local"))
st.markdown("""<div class="hero"><div class="eyebrow">Customer Experience Analytics · v0.6</div>
<h1><span style="color:#FF792D">CX</span> Intelligence</h1>
<p>Transformando interações simuladas em indicadores, análises e hipóteses de melhoria.</p></div>""",unsafe_allow_html=True)
if subset.empty:
    st.warning("Nenhum registro no recorte selecionado. Ajuste os filtros da barra lateral.")
    st.stop()
m=kpis(subset)
kpi_cards=st.columns(5)
for slot,(name,value,tip) in zip(kpi_cards,[
    ("Atendimentos",f"{m['total_tickets']:,}".replace(",","."),"Tickets no período selecionado"),
    ("CSAT positivo",f"{m['csat_pct']:.1f}%","Notas simuladas 4–5 / avaliações"),
    ("Resolvidos",f"{m['fcr_proxy_pct']:.1f}%","Resolução registrada — não é FCR"),
    ("Tempo médio",f"{m['avg_resolution_hours']:.1f} h","Horas por chamado, não minutos"),
    ("Reincidência*",f"{m['repeat_contact_rate_pct']:.1f}%","Alvo sintético, não churn observado")]):
    slot.metric(name,value,help=tip)
st.markdown('<div class="note">🔎 Todos os números são sintéticos. * Reincidência e sentimento são rótulos simulados. A taxa de resolução não mede FCR e o projeto não mede NPS nem churn real.</div>',unsafe_allow_html=True)
tab_overview,tab_voice,tab_risk,tab_nlp,tab_alerts,tab_insights,tab_quality=st.tabs(["📈 Visão executiva","💬 Voz do cliente","🧠 Risco preditivo","🗣️ NLP experimental","🚨 Alertas CX","🔎 Diagnóstico CX","🛡️ Qualidade dos dados"])
with tab_overview:
    daily=subset.assign(day=subset.date.dt.date).groupby("day",as_index=False).agg(tickets=("ticket_id","count"),csat=("csat",lambda s:round(100*s.ge(4).mean(),1)))
    l,r=st.columns(2)
    with l:
        chart(px.line(daily,x="day",y="tickets",title="Volume diário de atendimentos",color_discrete_sequence=[COLORS["cyan"]],markers=True,labels={"day":"Data","tickets":"Chamados"}))
    with r:
        fig=px.line(daily,x="day",y="csat",title="CSAT positivo diário (%)",color_discrete_sequence=[COLORS["orange"]],labels={"day":"Data","csat":"CSAT (%)"})
        fig.update_yaxes(range=[0,100]);chart(fig)
    a,b=st.columns(2)
    with a:
        topic_summary=subset.groupby("topic",as_index=False).size().rename(columns={"size":"tickets"}).sort_values("tickets")
        chart(px.bar(topic_summary,x="tickets",y="topic",orientation="h",title="Principais motivos de atendimento",color_discrete_sequence=[COLORS["orange"]],labels={"topic":"Assunto","tickets":"Chamados"}))
    with b:
        channel_summary=subset.groupby("channel",as_index=False).size().rename(columns={"size":"tickets"})
        chart(px.pie(channel_summary,names="channel",values="tickets",hole=.65,title="Distribuição por canal",color_discrete_sequence=[COLORS["cyan"],COLORS["orange"],COLORS["green"],COLORS["red"]]))
    st.markdown("#### Insights descritivos do recorte")
    top=topic_summary.iloc[-1]
    st.info(f"**{top['topic']}** concentra o maior volume ({int(top['tickets'])} tickets; {100*top['tickets']/len(subset):.1f}% do recorte). Investigue processos e motivos antes de atribuir causas.")
with tab_voice:
    st.caption("Os sentimentos abaixo foram sorteados durante a geração dos dados. Não representam inferência NLP de textos.")
    sentiment=subset.groupby(["topic","sentiment"],as_index=False).size().rename(columns={"size":"tickets"})
    chart(px.bar(sentiment,x="topic",y="tickets",color="sentiment",barmode="stack",title="Distribuição de sentimentos sintéticos por assunto",color_discrete_map={"positivo":COLORS["green"],"neutro":COLORS["cyan"],"negativo":COLORS["red"]}))
    per_topic=subset.groupby("topic",as_index=False).agg(atendimentos=("ticket_id","size"),csat_positivo_pct=("csat",lambda s:round(100*s.ge(4).mean(),1)),resolvidos_pct=("resolved",lambda s:round(100*s.mean(),1)),tempo_medio_h=("resolution_hours","mean"))
    st.dataframe(per_topic.round(2),use_container_width=True,hide_index=True)
with tab_risk:
    st.info("Experimento supervisionado: o alvo de reincidência é gerado artificialmente. Não utilizar scores para decisões sobre pessoas reais.")
    with st.spinner("Treinando baseline temporal..."):
        _,score,pred=train_and_evaluate(df)
    c1,c2,c3=st.columns(3)
    c1.metric("ROC-AUC",str(score["roc_auc"]) if score["roc_auc"] is not None else "N/A")
    c2.metric("Average Precision",str(score["average_precision"]))
    c3.metric("Prevalência do teste",f"{score['prevalence']*100:.1f}%")
    st.caption("Treinamento usa o conjunto completo, com teste temporal. Filtros são aplicados somente à tabela de scores, não ao treinamento.")
    pred_view=pred[pred.topic.isin(topics)&pred.channel.isin(channels)]
    if len(dates)==2:
        pred_view=pred_view[pred_view.date.dt.date.between(start,end)]
    st.dataframe(pred_view.head(100),use_container_width=True,hide_index=True)
@st.cache_resource
def load_nlp_model():
    return train_sentiment()

with tab_nlp:
    st.subheader("Classificação exploratória de sentimentos")
    st.warning("Protótipo treinado com 60 frases fictícias. Amostra pequena e artificial; não utilizar em operações reais.")
    model_nlp, eval_nlp = load_nlp_model()
    c1, c2, c3 = st.columns(3)
    c1.metric("F1 macro", f"{eval_nlp['f1_macro']:.3f}")
    c2.metric("Acurácia", f"{eval_nlp['accuracy']:.3f}")
    c3.metric("Mensagens no teste", str(eval_nlp["test_rows"]))
    st.caption("TF-IDF + Regressão Logística. Divisão estratificada 70/30 (18 frases de teste); probabilidades não calibradas.")
    message = st.text_area("Digite uma frase fictícia para classificar", value="O atendimento foi rápido e resolveu minha dúvida", max_chars=500)
    if st.button("Analisar sentimento", key="run_nlp"):
        try:
            result = classify_message(model_nlp, message)
            st.success(f"Classe estimada: {result['sentiment']}")
            st.caption(f"Maior probabilidade estimada (não calibrada): {result['score']:.1%}")
            prob_df = pd.DataFrame({"sentimento": list(result["probabilities"].keys()), "probabilidade": list(result["probabilities"].values())})
            chart(px.bar(prob_df, x="sentimento", y="probabilidade", title="Distribuição de probabilidades do protótipo", color_discrete_sequence=[COLORS["orange"]]))
        except ValueError as exc:
            st.error(str(exc))
    comparison, mistakes = compare_models()
    st.markdown("#### Comparativo de algoritmos — mesmo conjunto de teste")
    st.dataframe(comparison.sort_values("f1_macro", ascending=False), use_container_width=True, hide_index=True)
    with st.expander("Investigar erros de classificação"):
        st.dataframe(mistakes, use_container_width=True, hide_index=True)
    matrix=pd.DataFrame(eval_nlp["confusion"], index=eval_nlp["labels"], columns=eval_nlp["labels"])
    with st.expander("Matriz de confusão (linhas reais × colunas previstas)"):
        st.dataframe(matrix, use_container_width=True)
    st.caption("Os campos sentiment e repeat_contact_30d dos tickets continuam sintéticos; este classificador não os produziu.")

with tab_alerts:
    st.subheader("Detecção explicável de picos de atendimento")
    st.caption("Monitoramento histórico por semana ISO e assunto. Regras heurísticas, não previsão e não inferência causal.")
    st.info("Regra: no mínimo 4 semanas completas de histórico, baseline >= 5, aumento >= 50% e pelo menos 5 tickets adicionais. Semanas iniciais/finais incompletas são descartadas.")
    history = df[df.topic.isin(topics) & df.channel.isin(channels)].copy()
    # Calculate a comparable baseline using the full historical date range,
    # then show only alerts falling within the requested display window.
    alerts = detect_volume_anomalies(history)
    if len(dates) == 2:
        alerts = alerts[alerts.week_start.dt.date.between(start, end)]
    n_high = int(alerts.severity.eq("Alta").sum()) if not alerts.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Alertas identificados", len(alerts))
    c2.metric("Alertas de alta intensidade", n_high)
    c3.metric("Assuntos com alertas", alerts.topic.nunique() if not alerts.empty else 0)
    if alerts.empty:
        st.info("Nenhum pico elegível detectado para o recorte. Isto não comprova ausência de problemas ou cobertura de dados completa.")
    else:
        st.dataframe(alerts, use_container_width=True, hide_index=True)
        st.download_button("⬇ Exportar alertas (CSV)", alerts.to_csv(index=False).encode("utf-8"),
                           "cx_alertas_sinteticos.csv", "text/csv")
    weeks = weekly_volumes(history)
    if not weeks.empty:
        fig_alert = px.line(weeks, x="week_start", y="volume", color="topic", markers=True,
                            title="Volume semanal de tickets por assunto",
                            labels={"week_start": "Início da semana", "volume": "Tickets", "topic": "Assunto"})
        chart(fig_alert)
    st.caption("Sem evidência de cobertura diária da ingestão, ausência de eventos não comprova ausência de chamados. Valide sempre com a operação de CX.")

with tab_insights:
    st.subheader("Diagnóstico de segmentos: assunto × canal")
    st.caption("Análise descritiva de diferenças — não estabelece causas nem significância estatística.")
    min_n = st.slider("Mínimo de tickets por segmento", min_value=10, max_value=100, value=30, step=10)
    insights = segment_insights(subset, min_sample=min_n)
    if insights.empty:
        st.info("Nenhum segmento atingiu o mínimo de registros no recorte. Amplie o período ou reduza o limite.")
    else:
        a,b,c=st.columns(3)
        a.metric("Segmentos elegíveis",len(insights))
        b.metric("Investigações prioritárias",int(insights.priority.eq("Prioritário").sum()))
        c.metric("Investigações adicionais",int(insights.priority.eq("Investigar").sum()))
        fig_insights=px.scatter(insights, x="csat_gap_pp", y="resolution_gap_pp",
                color="priority", size="tickets", hover_name="topic",
                hover_data=["channel","tickets","csat_pct","resolved_pct"],
                title="Diferença versus total filtrado (pontos percentuais)",
                labels={"csat_gap_pp":"Diferença de CSAT (pp)","resolution_gap_pp":"Diferença de resolução (pp)"},
                color_discrete_map={"Prioritário":COLORS["red"],"Investigar":COLORS["orange"],"Monitorar":COLORS["cyan"]})
        fig_insights.add_vline(x=0,line_dash="dot",line_color="#8795A8")
        fig_insights.add_hline(y=0,line_dash="dot",line_color="#8795A8")
        chart(fig_insights)
        st.dataframe(insights, use_container_width=True, hide_index=True)
        st.download_button("⬇ Exportar diagnóstico CSV", insights.to_csv(index=False).encode("utf-8"),
                           "cx_diagnostico_sintetico.csv","text/csv")
        st.info("Recomendação: discutir segmentos sinalizados com CX, revisar mudanças de processo e analisar séries históricas antes de qualquer intervenção.")

with tab_quality:
    errors=validate_data(df)
    l,r=st.columns(2)
    l.metric("Registros avaliados",len(df))
    r.metric("Erros detectados",len(errors))
    if errors:
        st.error("; ".join(errors))
    else:
        st.success("Validações implementadas aprovadas. Isto não substitui testes completos de contrato e integridade.")
    st.dataframe(pd.DataFrame({"coluna":df.columns,"tipo":df.dtypes.astype(str).values,"nulos":df.isna().sum().values}),use_container_width=True,hide_index=True)
    st.download_button("⬇ Exportar registros filtrados (CSV)",subset.to_csv(index=False).encode("utf-8"),"cx_filtrado.csv","text/csv")
