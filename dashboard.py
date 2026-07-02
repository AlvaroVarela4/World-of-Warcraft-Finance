import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from app.utils.currency import format_price, to_gold
from app.services.analysis import (
    available_realms,
    latest_realm_snapshot_id,
    market_overview_named,
    items_in_realm,
    price_history_for_item,
    current_listings_for_item,
)

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WoW Auction Analyzer",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

QUALITY_COLOR = {
    "POOR":      "#9d9d9d",
    "COMMON":    "#e0e0e0",
    "UNCOMMON":  "#1eff00",
    "RARE":      "#0070dd",
    "EPIC":      "#a335ee",
    "LEGENDARY": "#ff8000",
    "ARTIFACT":  "#e6cc80",
    "HEIRLOOM":  "#00ccff",
}

QUALITY_LABEL = {
    "POOR":      "Pobre",
    "COMMON":    "Común",
    "UNCOMMON":  "Poco común",
    "RARE":      "Raro",
    "EPIC":      "Épico",
    "LEGENDARY": "Legendario",
    "ARTIFACT":  "Artefacto",
    "HEIRLOOM":  "Herencia",
}

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚔️ WoW Auction Analyzer")
    st.markdown("---")

    realms = available_realms()
    if not realms:
        st.warning(
            "No hay datos de ningún reino. "
            "Ejecuta `python sync_realms_batch.py <Nombre>` para importar uno."
        )
        st.stop()

    realm_by_name = {r["name"]: r["connected_realm_id"] for r in realms}
    realm_name = st.selectbox("🌍 Reino", options=list(realm_by_name.keys()))
    connected_realm_id = realm_by_name[realm_name]

    st.markdown("---")

    search_query = st.text_input(
        "🔍 Buscar objeto",
        placeholder="Hierba, Mineral, Tela...",
    )

    items = items_in_realm(connected_realm_id, name_filter=search_query, limit=100)

    if not items:
        if search_query:
            st.info("No hay objetos con ese nombre en el último snapshot.")
        else:
            st.warning(
                "No hay auctions para este reino. "
                "Ejecuta `python sync_realms_batch.py <Nombre>` para importar datos."
            )
        st.stop()

    unnamed_count = sum(1 for i in items if i["name"].startswith("(item "))
    if unnamed_count > 0 and not search_query:
        st.info(
            f"{unnamed_count} objeto(s) sin nombre. "
            "Ejecuta `python resolve.py realm` para resolver los nombres desde la API."
        )

    item_by_name = {i["name"]: i for i in items}
    selected_name = st.selectbox("📦 Objeto", options=list(item_by_name.keys()))
    selected_item = item_by_name[selected_name]

    st.markdown("---")
    n_snapshots = st.slider("Ventana histórica (snapshots)", 5, 120, 30)

# ─── Header del item ─────────────────────────────────────────────────────────
quality = selected_item.get("quality") or "COMMON"
q_color = QUALITY_COLOR.get(quality, "#e0e0e0")
q_label = QUALITY_LABEL.get(quality, quality.capitalize())

st.markdown(
    f"<h1 style='margin-bottom:2px'>"
    f"<span style='color:{q_color}'>{selected_name}</span>"
    f"<span style='font-size:0.5em; color:#666; margin-left:12px'>· {q_label}</span>"
    f"</h1>",
    unsafe_allow_html=True,
)
st.caption(f"Reino: **{realm_name}**  ·  Item ID: `{selected_item['id']}`")

# ─── Histórico de precios ──────────────────────────────────────────────────────
history = price_history_for_item(selected_item["id"], connected_realm_id, n_snapshots=n_snapshots)

if not history:
    st.warning(
        "No hay historial de precios para este objeto en este reino. "
        "Es posible que no aparezca en ningún snapshot reciente."
    )
    st.stop()

df = pd.DataFrame(history)

# ─── Métricas ─────────────────────────────────────────────────────────────────
latest = history[-1]
prev   = history[-2] if len(history) >= 2 else history[0]

delta_copper = latest["min_price"] - prev["min_price"]
delta_pct    = (delta_copper / prev["min_price"] * 100) if prev["min_price"] else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Precio mínimo (actual)",
    format_price(latest["min_price"]),
)
col2.metric(
    "Variación (período anterior)",
    format_price(latest["min_price"]),
    delta=f"{delta_pct:+.2f}%",
    delta_color="inverse",   # rojo = precio subió (malo para el comprador)
)
col3.metric(
    "Volumen en circulación",
    f"{latest['total_quantity']:,}",
)
col4.metric(
    "Listados activos",
    f"{latest['listings']:,}",
)

st.divider()

# ─── Gráfico de precio + volumen ──────────────────────────────────────────────
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    row_heights=[0.72, 0.28],
    vertical_spacing=0.04,
)

ts       = df["fetched_at"]
min_gold = df["min_price"].apply(to_gold)
avg_gold = df["median_price"].apply(to_gold)
max_gold = df["max_price"].apply(to_gold)

# Banda rellena entre mínimo y máximo
fig.add_trace(go.Scatter(
    x=ts, y=max_gold,
    mode="lines", line=dict(width=0),
    showlegend=False, name="_max_fill",
    hoverinfo="skip",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=ts, y=min_gold,
    mode="lines", line=dict(width=0),
    fill="tonexty", fillcolor="rgba(0,112,221,0.12)",
    showlegend=False, name="_min_fill",
    hoverinfo="skip",
), row=1, col=1)

# Líneas de precio
fig.add_trace(go.Scatter(
    x=ts, y=min_gold,
    mode="lines+markers",
    name="Mínimo",
    line=dict(color="#1eff00", width=2),
    marker=dict(size=5),
    hovertemplate="%{y:.2f}g<extra>Mínimo</extra>",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=ts, y=avg_gold,
    mode="lines+markers",
    name="Mediana",
    line=dict(color="#ffd700", width=2, dash="dot"),
    marker=dict(size=4),
    hovertemplate="%{y:.2f}g<extra>Mediana</extra>",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=ts, y=max_gold,
    mode="lines+markers",
    name="Máximo",
    line=dict(color="#ff4444", width=1.5, dash="dash"),
    marker=dict(size=4),
    hovertemplate="%{y:.2f}g<extra>Máximo</extra>",
), row=1, col=1)

# Barras de volumen
fig.add_trace(go.Bar(
    x=ts,
    y=df["total_quantity"],
    name="Volumen",
    marker_color="#0070dd",
    opacity=0.65,
    hovertemplate="%{y:,}<extra>Volumen</extra>",
), row=2, col=1)

fig.update_layout(
    template="plotly_dark",
    height=520,
    hovermode="x unified",
    legend=dict(orientation="h", y=1.05, x=0, bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
fig.update_yaxes(
    row=1, col=1,
    title_text="Oro",
    ticksuffix="g",
    gridcolor="#2a2a2a",
    zeroline=False,
)
fig.update_yaxes(
    row=2, col=1,
    title_text="Cantidad",
    gridcolor="#2a2a2a",
    zeroline=False,
)
fig.update_xaxes(gridcolor="#2a2a2a", showgrid=True)

st.plotly_chart(fig, use_container_width=True)

# ─── Parte inferior: listados actuales + mercado general ──────────────────────
left_col, right_col = st.columns([1, 1.6])

with left_col:
    st.subheader("Listados actuales")
    listings = current_listings_for_item(selected_item["id"], connected_realm_id, limit=20)
    if listings:
        st.dataframe(
            pd.DataFrame([
                {
                    "Precio ud.": row["unit_price_fmt"],
                    "Cantidad": row["quantity"],
                    "Tiempo restante": row["time_left"],
                }
                for row in listings
            ]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Sin listados en el snapshot más reciente.")

with right_col:
    st.subheader(f"Top mercado — {realm_name}")
    snapshot_id = latest_realm_snapshot_id(connected_realm_id)
    overview = market_overview_named(snapshot_id, limit=25) if snapshot_id else []
    if overview:
        st.dataframe(
            pd.DataFrame([
                {
                    "Objeto":         row["name"],
                    "Calidad":        QUALITY_LABEL.get(row["quality"] or "", row["quality"] or "—"),
                    "Cantidad":       row["total_quantity"],
                    "Listados":       row["listings"],
                    "Precio mínimo":  row["min_price_fmt"],
                    "Precio mediano": row["median_price_fmt"],
                }
                for row in overview
            ]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Sin datos de mercado.")
