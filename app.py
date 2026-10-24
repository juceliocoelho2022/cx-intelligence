"""CX Intelligence — dados principais sintéticos e fonte externa isolada."""
import os
from datetime import datetime, time, timezone, timedelta
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
from src.advanced_cx import weekly_cx_trends, segment_benchmarks, observed_repeat_30d
from src.reports import build_report, render_markdown
from src.bi_reports import compare_periods, render_bi_markdown, render_bi_html
from src.cx_goals import (METRICS as GOAL_METRICS, ROLES as GOAL_ROLES,
    TRANSITIONS as GOAL_TRANSITIONS, evaluate_goals, create_action,
    change_action_status, edit_action, load_plan_actions, report_payload,
    export_plan_json, export_plan_markdown)
from src.audit import audit_manifest, export_manifest
from src.ticket_events import schema_exists, load_event_history, load_status_as_of, load_ticket_status_as_of
from src.external_kaggle import external_schema_exists, load_external_tickets, SOURCE_URL

PUBLIC_DEMO = os.getenv("CX_PUBLIC_DEMO", "false").lower() in {"true", "1", "yes"}

st.set_page_config(page_title="CX Intelligence | Customer Experience", page_icon="📊", layout="wide", initial_sidebar_state="auto")
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
/* Narrow viewport: compact KPI cards and prevent Plotly's floating toolbar
   from covering chart headings on Android and other touchscreen layouts. */
@media (max-width: 767px) {
  .hero {padding:18px 17px;margin-bottom:12px}
  .hero h1 {font-size:1.95rem;line-height:1.14}
  .eyebrow {letter-spacing:.09em;font-size:.68rem}
  [data-testid="stMetric"] {min-height:102px;padding:12px}
  [data-testid="stMetricValue"] {font-size:1.55rem}
  [data-testid="stPlotlyChart"] .modebar,
  [data-testid="stPlotlyChart"] .modebar-container {
    display:none !important;
  }
}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return load_tickets() if os.getenv('CX_DATA_SOURCE','csv').lower() == 'postgres' else get_or_create()

def chart(fig):
    fig.update_layout(**PLOT)
    st.plotly_chart(fig, width="stretch")

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
st.sidebar.caption("🔒 KPIs principais: sintéticos; Kaggle em módulo isolado")
if PUBLIC_DEMO:
    st.sidebar.info("Demonstração pública: somente dados sintéticos gerados pelo projeto. Sem banco local, CSV Kaggle ou credenciais.")
st.sidebar.caption("Fonte: " + ("PostgreSQL" if os.getenv("CX_DATA_SOURCE","csv").lower()=="postgres" else "CSV local"))
st.markdown("""<div class="hero"><div class="eyebrow">Customer Experience Analytics · v1.4.0</div>
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
st.markdown('<div class="note">🔎 Os KPIs acima são exclusivamente do dataset sintético principal, não do Kaggle. * Reincidência e sentimento são rótulos simulados. Resolução não mede FCR; não calculamos NPS nem churn real.</div>',unsafe_allow_html=True)
st.caption("📱 No celular: deslize a faixa de abas até 📑 BI v1.4 ou 🎯 Metas v1.5.")
tab_overview,tab_voice,tab_risk,tab_nlp,tab_alerts,tab_insights,tab_advanced,tab_report,tab_bi,tab_goals,tab_events,tab_kaggle,tab_quality=st.tabs(["📈 Visão executiva","💬 Voz do cliente","🧠 Risco preditivo","🗣️ NLP experimental","🚨 Alertas CX","🔎 Diagnóstico CX","📐 Analytics v1.3","📋 Relatório executivo","📑 BI v1.4","🎯 Metas v1.5","🕒 Histórico de tickets","🌐 Kaggle externo","🛡️ Qualidade dos dados"])
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
    st.dataframe(per_topic.round(2),width="stretch",hide_index=True)
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
    st.dataframe(pred_view.head(100),width="stretch",hide_index=True)
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
    st.dataframe(comparison.sort_values("f1_macro", ascending=False), width="stretch", hide_index=True)
    with st.expander("Investigar erros de classificação"):
        st.dataframe(mistakes, width="stretch", hide_index=True)
    matrix=pd.DataFrame(eval_nlp["confusion"], index=eval_nlp["labels"], columns=eval_nlp["labels"])
    with st.expander("Matriz de confusão (linhas reais × colunas previstas)"):
        st.dataframe(matrix, width="stretch")
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
        st.dataframe(alerts, width="stretch", hide_index=True)
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
        st.dataframe(insights, width="stretch", hide_index=True)
        st.download_button("⬇ Exportar diagnóstico CSV", insights.to_csv(index=False).encode("utf-8"),
                           "cx_diagnostico_sintetico.csv","text/csv")
        st.info("Recomendação: discutir segmentos sinalizados com CX, revisar mudanças de processo e analisar séries históricas antes de qualquer intervenção.")

with tab_advanced:
    st.subheader("Analytics avançado — comparação, incerteza e recontato")
    st.caption("Versão v1.3: exclusivamente dados sintéticos. Análises descritivas, sem inferência causal, representatividade ou previsão operacional.")
    st.markdown("#### 1. Evolução semanal de CX")
    weekly_advanced = weekly_cx_trends(subset)
    if weekly_advanced.empty:
        st.info("Não há semanas disponíveis para o recorte.")
    else:
        week_chart = go.Figure()
        week_chart.add_trace(go.Scatter(
            x=weekly_advanced.week_start, y=weekly_advanced.ci_lower_pct,
            mode="lines", line=dict(width=0), hoverinfo="skip",
            showlegend=False, name="Limite inferior"))
        week_chart.add_trace(go.Scatter(
            x=weekly_advanced.week_start, y=weekly_advanced.ci_upper_pct,
            mode="lines", fill="tonexty", fillcolor="rgba(255,121,45,0.15)",
            line=dict(width=0), name="Intervalo Wilson 95%",
            hoverinfo="skip"))
        week_chart.add_trace(go.Scatter(
            x=weekly_advanced.week_start, y=weekly_advanced.csat_pct,
            mode="lines+markers", name="CSAT positivo (%)",
            line=dict(color=COLORS["orange"], width=3)))
        week_chart.update_layout(title="CSAT positivo semanal e faixa ilustrativa de Wilson (95%)",
                                 xaxis_title="Semana iniciada na segunda-feira",
                                 yaxis_title="CSAT positivo (%)", yaxis_range=[0, 100])
        chart(week_chart)
        st.caption("A faixa Wilson pressupõe observações independentes. Em amostras sintéticas e com múltiplos tickets por cliente, ela NÃO representa uma margem de erro validada para clientes reais.")
        if weekly_advanced.edge_week.any():
            st.info("As semanas nas bordas do período selecionado podem estar incompletas. Compare-as com cautela.")
        st.dataframe(weekly_advanced, width="stretch", hide_index=True)
        st.download_button("⬇ Exportar tendência semanal (CSV)",
                           weekly_advanced.to_csv(index=False).encode("utf-8"),
                           "cx_v13_tendencia_semanal_sintetica.csv", "text/csv",
                           key="v13_weekly_export")
    st.markdown("#### 2. Benchmark descritivo entre segmentos")
    selected_dimension = st.radio("Comparar indicadores por",
                                  ["Canal", "Assunto"], horizontal=True,
                                  key="v13_benchmark_dimension")
    advanced_dimension = "channel" if selected_dimension == "Canal" else "topic"
    min_advanced = st.slider("Mínimo de tickets por segmento (v1.3)",
                             min_value=10, max_value=150, value=30, step=10,
                             key="v13_min_sample")
    benchmarks = segment_benchmarks(subset, dimension=advanced_dimension,
                                    min_sample=min_advanced)
    if benchmarks.empty:
        st.info("Nenhum segmento atingiu o limite mínimo. Ajuste os filtros ou a amostra.")
    else:
        baseline_csat = benchmarks.baseline_csat_pct.iloc[0]
        fig_bench = go.Figure(go.Bar(
            x=benchmarks.segment, y=benchmarks.csat_pct,
            marker_color=COLORS["cyan"], name="CSAT positivo (%)",
            error_y=dict(type="data", symmetric=False,
                         array=(benchmarks.ci_upper_pct - benchmarks.csat_pct).clip(lower=0).tolist(),
                         arrayminus=(benchmarks.csat_pct - benchmarks.ci_lower_pct).clip(lower=0).tolist())))
        fig_bench.add_hline(y=float(baseline_csat), line_dash="dot",
                            line_color=COLORS["orange"],
                            annotation_text="Referência: recorte completo")
        fig_bench.update_layout(title="CSAT por segmento (intervalos ilustrativos)",
                                xaxis_title=selected_dimension, yaxis_title="CSAT positivo (%)",
                                yaxis_range=[0, 100])
        chart(fig_bench)
        st.dataframe(benchmarks, width="stretch", hide_index=True)
        st.download_button("⬇ Exportar comparação (CSV)",
                           benchmarks.to_csv(index=False).encode("utf-8"),
                           "cx_v13_benchmark_sintetico.csv", "text/csv",
                           key="v13_benchmark_export")
        st.caption("Lacunas em pontos percentuais usam como referência o recorte inteiro, que inclui cada segmento. Intervalos NÃO constituem teste de significância entre grupos.")
    st.markdown("#### 3. Recontato encontrado no histórico sintético — janela de 30 dias")
    st.warning("Esta métrica procura um NOVO ticket do mesmo customer_id em data posterior, dentro de 30 dias. Não é o rótulo sintético 'repeat_contact_30d', não mede FCR e não representa reincidência real de clientes.")
    repeat_result = observed_repeat_30d(df, cohort=subset,
                                        dimension=advanced_dimension,
                                        min_sample=min_advanced)
    rc = st.columns(4)
    rc[0].metric("Tickets da coorte", repeat_result["cohort_tickets"])
    rc[1].metric("Elegíveis (30 dias completos)", repeat_result["eligible_tickets"])
    rc[2].metric("Sem janela completa", repeat_result["censored_tickets"])
    rc[3].metric("Recontato em 30 dias", 
                 f'{repeat_result["repeat_pct"]:.1f}%' if repeat_result["repeat_pct"] is not None else "N/A")
    st.caption(f'Observação até {repeat_result["as_of"] or "sem dados"}; tickets após {repeat_result["cutoff"] or "sem corte"} são excluídos da taxa. A busca de tickets posteriores utiliza a base sintética inteira, inclusive quando os filtros ocultam os atendimentos seguintes.')
    if repeat_result["eligible_tickets"] == 0:
        st.info("Sem tickets com os 30 dias completos de observação. Amplie o período histórico.")
    elif repeat_result["groups"].empty:
        st.info("Há tickets elegíveis, mas nenhum grupo atingiu o tamanho mínimo de amostra.")
    else:
        chart(px.bar(repeat_result["groups"], x="segment", y="repeat_pct",
                     title="Recontato por segmento (apenas coortes elegíveis)",
                     labels={"segment": selected_dimension, "repeat_pct": "Recontato em 30 dias (%)"},
                     color_discrete_sequence=[COLORS["orange"]]))
        st.dataframe(repeat_result["groups"], width="stretch", hide_index=True)
        st.download_button("⬇ Exportar coortes elegíveis (CSV)",
                           repeat_result["groups"].to_csv(index=False).encode("utf-8"),
                           "cx_v13_recontato_sintetico.csv", "text/csv",
                           key="v13_repeat_export")
    st.caption("Limitação: não existem horários intradiários, então tickets do mesmo dia não são tratados como recontato. Completude e representatividade de uma operação real não estão estabelecidas.")

with tab_report:
    st.subheader("Relatório executivo de Customer Experience")
    st.caption("Síntese reproduzível, sem LLM. Achados são descritivos e as ações são hipóteses para investigação.")
    report_history = df[df.topic.isin(topics) & df.channel.isin(channels)].copy()
    report = build_report(subset, history=report_history)
    a,b,c=st.columns(3)
    a.metric("Chamados avaliados",report["metrics"]["total_tickets"])
    b.metric("Segmentos prioritários",report["priority_count"])
    c.metric("Alertas heurísticos",report["alerts_count"])
    origin = "PostgreSQL (dados sintéticos)" if os.getenv("CX_DATA_SOURCE","csv").lower()=="postgres" else "CSV local (dados sintéticos)"
    memo=render_markdown(report,source_label=origin)
    manifest=audit_manifest(subset,report,source="synthetic_postgres" if os.getenv("CX_DATA_SOURCE","csv").lower()=="postgres" else "synthetic_csv")
    st.markdown(memo)
    st.download_button("⬇ Baixar relatório executivo (.md)",memo.encode("utf-8"),
                       "cx_relatorio_executivo.md","text/markdown")
    st.download_button("⬇ Baixar manifesto de auditoria (.json)",export_manifest(manifest).encode("utf-8"),
                       "cx_manifesto_auditoria.json","application/json")
    with st.expander("Rastreabilidade e verificações analíticas"):
        st.code(manifest["dataset_sha256"],language=None)
        st.json(manifest)
        st.caption("Hash SHA-256 reproduzível do recorte; não é assinatura nem certificação de origem.")
    st.info("As recomendações não são decisões automatizadas. Valide amostras, integridade, sazonalidade e hipóteses junto ao time de CX.")

with tab_bi:
    st.subheader("Business Intelligence — Relatório Executivo Comparativo")
    st.caption("v1.4.0 · Somente dados sintéticos. Janelas civis consecutivas de igual duração; não são séries ajustadas por sazonalidade.")
    left_control, middle_control, right_control = st.columns([1, 1, 1])
    with left_control:
        bi_days = st.selectbox("Comparar os últimos", [7, 14, 30], index=1,
                               format_func=lambda day: f"{day} dias",
                               key="bi_window_days")
    with middle_control:
        bi_dimension_name = st.selectbox("Segmentar por", ["Canal", "Assunto"],
                                         key="bi_group_dimension")
    with right_control:
        bi_minimum = st.selectbox("Mínimo por grupo e período", [10, 20, 30, 50, 100],
                                  index=2, key="bi_minimum")
    # Sidebar date control chooses the reference END day. BI window length is
    # independent of the sidebar start day, preserving equal calendar periods.
    bi_end_date = dates[1] if len(dates) == 2 else subset.date.max().date()
    bi_comparison = compare_periods(
        df, end_date=bi_end_date, window_days=bi_days,
        dimension="channel" if bi_dimension_name == "Canal" else "topic",
        topics=topics, channels=channels, min_sample=bi_minimum,
    )
    current_period = bi_comparison["period_current"]
    previous_period = bi_comparison["period_previous"]
    st.caption(f"Período atual: {current_period['start']} a {current_period['end']} · "
               f"Anterior: {previous_period['start']} a {previous_period['end']}. "
               "Os filtros de Canal/Assunto são aplicados aos dois períodos; o início escolhido na barra lateral NÃO altera a duração da comparação.")
    if bi_comparison["status"] != "comparable":
        reason = {
            "insufficient_history": "O dataset não cobre os dois períodos completos. Variações não calculadas.",
            "empty_baseline": "Não há atendimentos do segmento selecionado no período anterior. Variações não calculadas.",
            "empty_current": "Não há atendimentos do segmento selecionado no período atual. Variações não calculadas.",
        }.get(bi_comparison["status"], "Comparação indisponível")
        st.warning(reason)
    metric_cards = st.columns(4)
    for container, item in zip(metric_cards, bi_comparison["metrics"]):
        val = item["current"]
        unit = "h" if item["metric"] == "avg_resolution_hours" else "%" if item["metric"] in ("csat_pct", "resolved_pct") else ""
        current_label = (format(int(val), ",").replace(",", ".") if item["metric"] == "tickets"
                         else f"{val:.2f}{unit}") if val is not None else "N/A"
        change = item["delta"]
        delta_label = (f'{change:+.2f} {item["delta_unit"]}' if change is not None else None)
        container.metric(item["label"], current_label, delta=delta_label,
                         help="Comparação apenas descritiva. Percentuais em pontos percentuais (pp); volume em variação relativa (%).")
    st.markdown("#### Comparação entre segmentos")
    seg_table = pd.DataFrame(bi_comparison["segments"])
    if seg_table.empty:
        st.info("Nenhum segmento comparável no mínimo amostral selecionado. A exportação registrará essa limitação.")
    else:
        chart(px.bar(seg_table, x="segment", y="csat_delta_pp",
                     title="Mudança descritiva de CSAT (pp): período atual vs anterior",
                     labels={"segment": bi_dimension_name, "csat_delta_pp": "Mudança (pp)"},
                     color_discrete_sequence=[COLORS["cyan"]]))
        st.dataframe(seg_table, width="stretch", hide_index=True)
    st.caption(f'Segmentos omitidos por amostra insuficiente: {bi_comparison["segments_excluded_small_sample"]}. '
               "Um grupo entra na comparação apenas se AMBOS os períodos tiverem tickets suficientes.")
    bi_md = render_bi_markdown(bi_comparison)
    bi_html = render_bi_html(bi_comparison)
    st.markdown("#### Relatório executivo pronto para compartilhar")
    st.info("O relatório HTML é autocontido e formatado para impressão. Abra-o no navegador e selecione Imprimir → Salvar como PDF, se desejar. Nenhum dado de cliente real é incluído.")
    download_md, download_html = st.columns(2)
    download_md.download_button("⬇ Relatório comparativo (.md)",
                               bi_md.encode("utf-8"), "cx_bi_v14_sintetico.md", "text/markdown",
                               key="bi_v14_markdown")
    download_html.download_button("⬇ Relatório para impressão (.html)",
                                 bi_html.encode("utf-8"), "cx_bi_v14_sintetico.html", "text/html",
                                 key="bi_v14_html")
    with st.expander("Ver prévia e limitações metodológicas", expanded=False):
        st.markdown(bi_md)

with tab_goals:
    st.subheader("Metas de CX e Plano de Ação — v1.5 (beta)")
    st.caption("Demonstração com dados 100% sintéticos. Metas configuráveis são propostas ilustrativas; nenhuma ação é executada por uma equipe real.")
    st.info("As ações ficam **somente nesta sessão de navegador**. Não há cadastro, banco de planos, login, agendamento de lembretes ou sincronização entre usuários. Exporte JSON ou Markdown para registrar um exemplo.")
    goal_window_col, goal_count_col = st.columns(2)
    with goal_window_col:
        goal_days = st.selectbox("Janela de análise das metas",
                                 [7, 14, 30], index=1,
                                 format_func=lambda val: f"{val} dias",
                                 key="v15_window")
    with goal_count_col:
        goal_minimum = st.selectbox("Mínimo de tickets na janela",
                                    [10, 20, 30, 50, 100], index=2,
                                    key="v15_minimum")
    goal_target_cols = st.columns(3)
    with goal_target_cols[0]:
        goal_csat = st.number_input("Meta ilustrativa de CSAT (%)",
                                    min_value=0.0, max_value=100.0,
                                    value=70.0, step=1.0,
                                    key="v15_target_csat")
    with goal_target_cols[1]:
        goal_resolved = st.number_input("Meta ilustrativa de resolvidos (%)",
                                        min_value=0.0, max_value=100.0,
                                        value=90.0, step=1.0,
                                        key="v15_target_resolved")
    with goal_target_cols[2]:
        goal_hours = st.number_input("Teto ilustrativo de tempo médio (h)",
                                     min_value=0.0, max_value=96.0,
                                     value=10.0, step=0.5,
                                     key="v15_target_hours")
    goal_end_date = dates[1] if len(dates) == 2 else subset.date.max().date()
    goal_period_report = compare_periods(
        df, end_date=goal_end_date, window_days=goal_days,
        topics=topics, channels=channels, min_sample=goal_minimum,
    )
    period_now = goal_period_report["period_current"]
    # Date-range coverage is a necessary condition, not a certification of
    # ingestion completeness. Incomplete current windows suppress goal verdicts.
    is_window_covered = (pd.to_datetime(df.date).min().normalize()
                         <= pd.Timestamp(period_now["start"]))
    goal_scores = evaluate_goals(
        goal_period_report["current"],
        targets={"csat_pct": goal_csat, "resolved_pct": goal_resolved,
                 "avg_resolution_hours": goal_hours},
        min_tickets=goal_minimum, current_covered=bool(is_window_covered),
    )
    st.caption(f"Janela corrente: {period_now['start']} a {period_now['end']}. "
               "Filtros de assunto e canal aplicados; a data inicial da barra lateral não altera os dias da janela.")
    goal_score_cards = st.columns(3)
    for slot, row_goal in zip(goal_score_cards, goal_scores):
        goal_suffix = " h" if row_goal["unit"] == "h" else "%"
        observed = (f'{row_goal["observed"]:.2f}{goal_suffix}'
                    if row_goal["observed"] is not None else "N/A")
        slot.metric(row_goal["label"], observed,
                    help="Meta configurada: " + f'{row_goal["target"]:.2f}{goal_suffix}')
        if row_goal["status"] == "met":
            slot.success("Meta ilustrativa atingida")
        elif row_goal["status"] == "attention":
            slot.warning(f'Distância para a meta: {row_goal["gap_to_target"]:.2f} {row_goal["unit"]}')
        else:
            slot.info("Sem avaliação válida: " + row_goal["status"])
    st.caption("CSAT e resolução são taxas em %. Distâncias correspondentes são em pontos percentuais (pp). "
               "Tempo médio e respectiva distância usam horas (h). Não existe teste de significância, SLA real ou atribuição causal.")
    st.markdown("#### Plano de ação demonstrativo")
    if "v15_actions" not in st.session_state:
        st.session_state["v15_actions"] = []
    with st.expander("📥 Restaurar plano de ação exportado (.json)", expanded=False):
        st.caption("Importe apenas um JSON previamente exportado por esta aba v1.5. "
                   "A restauração substitui as ações desta sessão, não importa métricas históricas "
                   "e não grava informações em banco de dados.")
        restore_file = st.file_uploader(
            "Selecionar exportação JSON v1.5 (máximo 200 KB)", type=["json"],
            key="v15_restore_file")
        if st.button("Restaurar ações nesta sessão", key="v15_restore_button",
                     disabled=restore_file is None):
            try:
                if restore_file.size > 200_000:
                    raise ValueError("Arquivo acima do máximo de 200 KB")
                restored = load_plan_actions(restore_file.getvalue())
                st.session_state["v15_actions"] = restored
                st.success(f"{len(restored)} ação(ões) restaurada(s) na sessão. "
                           "Metas recalculadas a partir dos filtros atuais.")
            except ValueError as exc:
                st.error(f"Não foi possível restaurar: {exc}")
    # Keep user-entered text if validation fails, so the form can be corrected.
    with st.form("v15_add_action", clear_on_submit=False):
        action_title = st.text_input(
            "Ação proposta (obrigatório; até 120 caracteres)",
            placeholder="Ex.: investigar motivos de insatisfação no fluxo Pix",
            max_chars=120,
        )
        action_hypothesis = st.text_area(
            "Hipótese a investigar (obrigatório; até 400 caracteres)",
            placeholder="Ex.: analisar possíveis dificuldades na jornada Pix, sem pressupor a causa.",
            max_chars=400,
            help="Campo obrigatório. Escreva uma frase explicando o que deseja investigar; evite quebras de linha.",
        )
        st.caption("Os dois campos de texto são obrigatórios. O exemplo cinza é uma sugestão, não um texto preenchido.")
        action_left, action_right = st.columns(2)
        with action_left:
            action_metric = st.selectbox(
                "Indicador relacionado", list(GOAL_METRICS.keys()),
                format_func=lambda metric: GOAL_METRICS[metric]["label"],
                key="v15_action_metric")
            action_role = st.selectbox("Área responsável fictícia", GOAL_ROLES,
                                       key="v15_action_role")
        with action_right:
            action_deadline = st.date_input("Prazo proposto",
                                            value=datetime.now().date() + timedelta(days=14),
                                            min_value=datetime.now().date(),
                                            key="v15_action_due")
        action_submitted = st.form_submit_button("Adicionar ação ilustrativa", type="primary")
    if action_submitted:
        try:
            st.session_state["v15_actions"] = create_action(
                st.session_state["v15_actions"],
                metric=action_metric, title=action_title, hypothesis=action_hypothesis,
                role=action_role, due_date=action_deadline,
                created_on=datetime.now().date(),
                period_start=period_now["start"], period_end=period_now["end"],
                topics=list(topics), channels=list(channels),
            )
            st.success("Ação adicionada ao plano desta sessão; nenhuma tarefa foi criada fora da aplicação.")
        except ValueError as exc:
            st.error(f"Não foi possível adicionar: {exc}")
    all_actions = st.session_state["v15_actions"]
    if all_actions:
        st.caption(f"{len(all_actions)} ação(ões) fictícia(s) registrada(s) apenas nesta sessão.")
        st.caption("Estados simulados: "
                   f"{sum(a['status'] == 'Planejada' for a in all_actions)} planejada(s), "
                   f"{sum(a['status'] == 'Em andamento' for a in all_actions)} em andamento, "
                   f"{sum(a['status'] == 'Concluída' for a in all_actions)} concluída(s).")
        actions_table = pd.DataFrame([
            {"ID": a["id"], "Ação": a["title"], "Indicador": GOAL_METRICS[a["metric"]]["label"],
             "Área fictícia": a["owner_role"], "Prazo": a["due_date"], "Estado": a["status"],
             "Recorte original": a["scope"]["period_start"] + " a " + a["scope"]["period_end"]}
            for a in all_actions
        ])
        st.dataframe(actions_table, hide_index=True, width="stretch")
        revised_actions = [a for a in all_actions if a.get("edits")]
        if revised_actions:
            st.caption("Revisões de texto registradas: " + "; ".join(
                f'{a["id"]}: {a["title"]}' for a in revised_actions))
        with st.expander("✏️ Corrigir título ou hipótese de uma ação", expanded=False):
            edit_id = st.selectbox(
                "Escolha a ação para corrigir", [a["id"] for a in all_actions],
                key="v15_edit_id")
            edit_source = next(a for a in all_actions if a["id"] == edit_id)
            revision_count = len(edit_source.get("edits", []))
            with st.form("v15_edit_form", clear_on_submit=False):
                edit_title_value = st.text_input(
                    "Título corrigido (até 120 caracteres)",
                    value=edit_source["title"], max_chars=120,
                    key=f"v15_edit_title_{edit_id}_{revision_count}")
                edit_hypothesis_value = st.text_area(
                    "Hipótese corrigida (até 400 caracteres)",
                    value=edit_source["hypothesis"], max_chars=400,
                    key=f"v15_edit_hypothesis_{edit_id}_{revision_count}")
                edit_submitted = st.form_submit_button("Salvar correção da ação")
            if edit_submitted:
                try:
                    st.session_state["v15_actions"] = edit_action(
                        all_actions, edit_id, title=edit_title_value,
                        hypothesis=edit_hypothesis_value,
                        changed_on=datetime.now().date())
                    st.success("Texto corrigido na sessão. O ID e o histórico de estados foram preservados; "
                               "a revisão fica registrada na exportação JSON.")
                    st.rerun()
                except ValueError as exc:
                    st.error(f"Correção rejeitada: {exc}")
        open_actions = [a for a in all_actions if GOAL_TRANSITIONS[a["status"]]]
        if open_actions:
            update_left, update_right = st.columns(2)
            with update_left:
                action_selected = st.selectbox(
                    "Selecionar ação a atualizar", [a["id"] for a in open_actions],
                    format_func=lambda key: next(a["title"] for a in open_actions if a["id"] == key),
                    key="v15_action_selected")
            selected_action = next(a for a in open_actions if a["id"] == action_selected)
            with update_right:
                allowed_statuses = sorted(GOAL_TRANSITIONS[selected_action["status"]])
                next_status = st.selectbox("Próximo estado permitido",
                                           allowed_statuses,
                                           key="v15_next_status")
            if st.button("Atualizar estado fictício", key="v15_update"):
                try:
                    st.session_state["v15_actions"] = change_action_status(
                        all_actions, action_selected, next_status,
                        datetime.now().date())
                    st.success("Estado atualizado apenas nesta sessão. Isso não representa execução real nem ganho comprovado.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        with st.expander("Hipóteses e histórico das ações"):
            for action_item in all_actions:
                st.write(f'{action_item["id"]} — {action_item["title"]}')
                st.write(action_item["hypothesis"])
                st.json(action_item["events"])
    else:
        st.info("Nenhuma ação proposta ainda. Use o formulário para criar seu primeiro exemplo.")
    goal_payload = report_payload(goal_scores, st.session_state["v15_actions"], period_now)
    v15_left, v15_right = st.columns(2)
    with v15_left:
        st.download_button("⬇ Exportar plano (.json)", export_plan_json(goal_payload).encode("utf-8"),
                           "cx_metas_v15_sintetico.json", "application/json",
                           key="v15_export_json")
    with v15_right:
        st.download_button("⬇ Exportar plano (.md)", export_plan_markdown(goal_payload).encode("utf-8"),
                           "cx_metas_v15_sintetico.md", "text/markdown",
                           key="v15_export_md")
    st.caption("Exportar NÃO salva no servidor. Um JSON de ações sintéticas v1.5 pode ser "
               "restaurado manualmente e substitui o plano da sessão. Mudanças de filtro alteram "
               "a avaliação atual, mas não os recortes originais das ações nem seus eventos.")

with tab_events:
    st.subheader("Histórico imutável de eventos dos tickets")
    st.warning("Transições exibidas são explicitamente simuladas. O campo 'resolved' legado é apenas o estado atual e não reconstitui eventos passados.")
    if os.getenv("CX_DATA_SOURCE", "csv").lower() != "postgres":
        if PUBLIC_DEMO:
            st.info("Modo público: o histórico SQL é demonstrado e testado localmente. Esta instância pública não recebe eventos nem se conecta ao PostgreSQL.")
        else:
            st.info("Este módulo requer PostgreSQL. Inicie o banco, configure CX_DATA_SOURCE=postgres e consulte docs/TICKET_HISTORY.md.")
    elif not schema_exists():
        st.info("Execute no terminal: python -m src.ticket_events init; depois, opcionalmente, python -m src.ticket_events demo")
    else:
        event_rows = load_event_history(limit=500)
        if not event_rows:
            st.info("Tabela inicializada, mas sem eventos. Para exemplos fictícios: python -m src.ticket_events demo")
        else:
            events_df = pd.DataFrame(event_rows)
            st.metric("Eventos exibidos (limite 500)", len(events_df))
            st.caption("O resumo de estados abrange todos os tickets com eventos registrados, não apenas os 500 exibidos nem os filtros da barra lateral.")
            selected_day = st.date_input("Estado observado até o fim do dia (UTC)",
                value=events_df.occurred_at.max().date(),
                min_value=events_df.occurred_at.min().date(),
                max_value=events_df.occurred_at.max().date(),
                key="history_as_of_day")
            state_at = datetime.combine(selected_day, time.max, tzinfo=timezone.utc)
            statuses = pd.DataFrame(load_status_as_of(state_at))
            if not statuses.empty:
                chart(px.bar(statuses, x="status", y="tickets",
                    title="Último estado registrado por ticket na data selecionada (UTC)",
                    color_discrete_sequence=[COLORS["orange"]]))
            else:
                st.info("Nenhum evento registrado até a data informada.")
            ticket_choice = st.selectbox("Linha do tempo — ticket fictício",
                                         sorted(events_df.ticket_id.unique()), key="history_ticket")
            ticket_status = load_ticket_status_as_of(ticket_choice, state_at)
            st.caption("Status até a data selecionada (UTC): " +
                       (ticket_status["status"] if ticket_status is not None else "sem evento registrado"))
            selected_events = events_df[events_df.ticket_id.eq(ticket_choice)].sort_values("occurred_at")
            st.dataframe(selected_events, width="stretch", hide_index=True)
            st.caption("A lista detalhada limita-se aos 500 eventos mais recentes. Para uma trilha completa, consulte a tabela SQL por ticket.")
            st.download_button("⬇ Exportar eventos exibidos (CSV)",
                events_df.to_csv(index=False).encode("utf-8"), "cx_eventos_sinteticos.csv","text/csv")

with tab_kaggle:
    st.subheader("Customer Support Tickets — dataset externo do Kaggle")
    st.caption("Fonte separada do pipeline sintético principal. Nenhum registro pessoal ou texto livre é importado.")
    st.markdown(f"Dataset: [Customer Support Ticket Dataset]({SOURCE_URL}). Consulte a licença na página original antes de redistribuir os arquivos.")
    st.warning("O dataset externo contém dados simulados e representa suporte a produtos tecnológicos, não atendimentos bancários. A data de compra não representa a data do ticket.")
    if os.getenv("CX_DATA_SOURCE", "csv").lower() != "postgres":
        if PUBLIC_DEMO:
            st.info("Modo público: a fonte Kaggle não está hospedada aqui para evitar redistribuir dados de terceiros. Consulte a documentação e execute o importador localmente.")
        else:
            st.info("Ative CX_DATA_SOURCE=postgres e importe o arquivo com python -m src.external_kaggle CAMINHO_DO_CSV --write.")
    elif not external_schema_exists():
        st.info("Nenhum dataset externo importado. Consulte docs/KAGGLE_INTEGRATION.md para executar uma prévia e importar o CSV.")
    else:
        external = load_external_tickets()
        if external.empty:
            st.info("A tabela externa está vazia. Importe o CSV para visualizar os indicadores.")
        else:
            c1,c2,c3,c4=st.columns(4)
            rated = external.satisfaction_rating.notna()
            c1.metric("Tickets externos",len(external))
            c2.metric("Avaliações válidas",int(rated.sum()))
            c3.metric("CSAT positivo (avaliados)",
                      f"{100*external.loc[rated,'satisfaction_rating'].ge(4).mean():.1f}%" if rated.any() else "N/A")
            c4.metric("Status Closed",f"{100*external.ticket_status.eq('Closed').mean():.1f}%")
            st.caption("Denominador CSAT: apenas tickets com nota disponível. 'Closed' é um status, não FCR nem comprovação de resolução.")
            left,right=st.columns(2)
            with left:
                counts=external.groupby("ticket_type",as_index=False).size().rename(columns={"size":"tickets"})
                chart(px.bar(counts,x="tickets",y="ticket_type",orientation="h",
                             title="Tickets por tipo",color_discrete_sequence=[COLORS["orange"]]))
            with right:
                channels_ext=external.groupby("ticket_channel",as_index=False).size().rename(columns={"size":"tickets"})
                chart(px.bar(channels_ext,x="ticket_channel",y="tickets",
                             title="Distribuição por canal",color_discrete_sequence=[COLORS["cyan"]]))
            st.markdown("#### Status e prioridade")
            priority_ext=pd.crosstab(external.ticket_priority,external.ticket_status).reset_index()
            st.dataframe(priority_ext,width="stretch",hide_index=True)
            st.caption("Não há duração confiável, histórico de eventos, reincidência, churn ou sentimento NLP disponível neste importador.")
            st.download_button("⬇ Exportar agregados por tipo (CSV)",
                               counts.to_csv(index=False).encode("utf-8"),
                               "cx_kaggle_agregados.csv","text/csv")

with tab_quality:
    errors=validate_data(df)
    l,r=st.columns(2)
    l.metric("Registros avaliados",len(df))
    r.metric("Erros detectados",len(errors))
    if errors:
        st.error("; ".join(errors))
    else:
        st.success("Validações implementadas aprovadas. Isto não substitui testes completos de contrato e integridade.")
    st.dataframe(pd.DataFrame({"coluna":df.columns,"tipo":df.dtypes.astype(str).values,"nulos":df.isna().sum().values}),width="stretch",hide_index=True)
    st.download_button("⬇ Exportar registros filtrados (CSV)",subset.to_csv(index=False).encode("utf-8"),"cx_filtrado.csv","text/csv")
