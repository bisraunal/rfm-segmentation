"""
app.py
------
RFM Müşteri Segmentasyon Dashboard
"""

import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ─────────────────────────────────────────────
# Sayfa Konfigürasyonu
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RFM Analytics",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR     = Path(__file__).resolve().parent
DATA_DIR     = BASE_DIR / "data"
CLUSTER_FILE = DATA_DIR / "rfm_clustered.csv"
RFM_FILE     = DATA_DIR / "rfm_data.csv"
ELBOW_IMAGE  = BASE_DIR / "assets" / "elbow_plot.png"

# ─────────────────────────────────────────────
# Renk Paleti (Editorial Dark)
# ─────────────────────────────────────────────
COLORS = {
    "bg":          "#0d0d0e",
    "surface":     "#16161a",
    "surface_2":   "#1c1c22",
    "border":      "#2a2a30",
    "border_soft": "#222228",
    "text":        "#ece6d9",
    "text_muted":  "#8a8478",
    "text_dim":    "#5a554c",
    "accent":      "#c8a165",
    "accent_dim":  "#8a7048",
}

SEGMENT_COLORS = {
    "Şampiyonlar":           "#b8c98a",
    "Sadık Müşteriler":      "#7da3c4",
    "Potansiyel Sadık":      "#d8a76d",
    "Risk Altındakiler":     "#c97864",
    "Kaybedilen Müşteriler": "#6b665e",
}

# ─────────────────────────────────────────────
# CSS — Editorial Dark
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600&family=Manrope:wght@200;300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Manrope', sans-serif;
    color: {COLORS['text']};
}}

.stApp {{
    background: {COLORS['bg']};
    background-image:
        radial-gradient(ellipse at top left, rgba(200, 161, 101, 0.04), transparent 60%),
        radial-gradient(ellipse at bottom right, rgba(125, 163, 196, 0.03), transparent 60%);
}}

#MainMenu {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.stDeployButton {{ display: none; }}
footer {{ visibility: hidden; }}

.block-container {{
    padding-top: 2.5rem !important;
    padding-bottom: 4rem !important;
    max-width: 1400px !important;
}}

h1, h2, h3, h4, h5 {{
    font-family: 'Fraunces', serif !important;
    color: {COLORS['text']} !important;
    font-weight: 400 !important;
    letter-spacing: -0.02em;
}}

h1 {{
    font-size: 3.2rem !important;
    line-height: 1.05 !important;
    font-weight: 300 !important;
    margin-bottom: 0 !important;
}}
h2 {{ font-size: 1.6rem !important; font-weight: 400 !important; }}
h3 {{ font-size: 1.15rem !important; font-weight: 500 !important; }}
p, .stMarkdown {{
    color: {COLORS['text_muted']};
    font-size: 0.95rem;
    line-height: 1.6;
}}

/* ──── Editorial Header ──── */
.editorial-header {{
    border-bottom: 1px solid {COLORS['border']};
    padding-bottom: 2rem;
    margin-bottom: 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}}
.editorial-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: {COLORS['accent']};
    margin-bottom: 0.8rem;
}}
.editorial-subtitle {{
    font-family: 'Manrope', sans-serif;
    font-size: 0.95rem;
    color: {COLORS['text_muted']};
    margin-top: 0.6rem;
    max-width: 520px;
    line-height: 1.5;
}}
.editorial-meta {{
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {COLORS['text_dim']};
    line-height: 1.9;
}}
.editorial-meta strong {{
    color: {COLORS['text']};
    font-weight: 500;
    font-size: 0.85rem;
}}

/* ──── Section Label ──── */
.section-label {{
    display: flex;
    align-items: baseline;
    gap: 1rem;
    margin-top: 3rem;
    margin-bottom: 1.5rem;
    border-top: 1px solid {COLORS['border_soft']};
    padding-top: 2rem;
}}
.section-label-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    color: {COLORS['accent']};
    font-weight: 500;
}}
.section-label-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.5rem;
    font-weight: 400;
    color: {COLORS['text']};
    letter-spacing: -0.01em;
}}
.section-label-desc {{
    font-family: 'Manrope', sans-serif;
    font-size: 0.85rem;
    color: {COLORS['text_muted']};
    margin-left: auto;
    font-weight: 300;
}}

/* ──── Metric Cards ──── */
[data-testid="stMetric"] {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    padding: 1.5rem 1.5rem 1.4rem;
    border-radius: 2px;
    position: relative;
    overflow: hidden;
}}
[data-testid="stMetric"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 32px;
    height: 1px;
    background: {COLORS['accent']};
}}
[data-testid="stMetricLabel"] {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: {COLORS['text_muted']} !important;
    font-weight: 500 !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Fraunces', serif !important;
    font-size: 2.6rem !important;
    font-weight: 300 !important;
    letter-spacing: -0.03em !important;
    color: {COLORS['text']} !important;
    line-height: 1.1 !important;
    margin-top: 0.4rem !important;
}}

/* ──── Sidebar ──── */
[data-testid="stSidebar"] {{
    background: {COLORS['bg']};
    border-right: 1px solid {COLORS['border_soft']};
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 2.5rem; }}
[data-testid="stSidebar"] h1 {{
    font-size: 1.4rem !important;
    font-weight: 500 !important;
    margin-bottom: 0.2rem !important;
}}
.sidebar-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {COLORS['accent']};
    margin-bottom: 0.4rem;
}}
[data-testid="stSidebar"] hr {{
    border-color: {COLORS['border_soft']};
    margin: 1.6rem 0;
}}
[data-testid="stSidebar"] label {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: {COLORS['text_muted']} !important;
    font-weight: 500 !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background: {COLORS['surface_2']} !important;
    border: 1px solid {COLORS['border']} !important;
    color: {COLORS['text']} !important;
    border-radius: 2px !important;
    font-size: 0.78rem !important;
}}
[data-testid="stSidebar"] [data-testid="stAlert"] {{
    background: {COLORS['surface']} !important;
    border: 1px solid {COLORS['border_soft']} !important;
    border-left: 2px solid {COLORS['accent']} !important;
    border-radius: 0 !important;
    color: {COLORS['text_muted']} !important;
    font-size: 0.78rem !important;
    padding: 1rem 1.2rem !important;
    line-height: 1.7 !important;
}}
.stSlider [data-baseweb="slider"] [role="slider"] {{
    background: {COLORS['accent']} !important;
    border: 2px solid {COLORS['bg']} !important;
}}

/* ──── Inputs ──── */
.stTextInput > div > div > input {{
    background: {COLORS['surface']} !important;
    border: 1px solid {COLORS['border']} !important;
    color: {COLORS['text']} !important;
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {COLORS['accent']} !important;
    box-shadow: none !important;
}}

/* ──── Dataframe ──── */
[data-testid="stDataFrame"] {{
    border: 1px solid {COLORS['border_soft']};
    border-radius: 2px;
    overflow: hidden;
}}

/* ──── Tabs ──── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: transparent;
    border-bottom: 1px solid {COLORS['border']};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border: none !important;
    color: {COLORS['text_muted']} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0.8rem 1.4rem !important;
    border-radius: 0 !important;
    border-bottom: 1px solid transparent !important;
    margin-bottom: -1px !important;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    color: {COLORS['accent']} !important;
    border-bottom: 1px solid {COLORS['accent']} !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.5rem; }}

/* ──── Image ──── */
[data-testid="stImage"] {{
    border: 1px solid {COLORS['border_soft']};
    border-radius: 2px;
    overflow: hidden;
}}

/* ──── Footer ──── */
.footer-credit {{
    margin-top: 4rem;
    padding-top: 2rem;
    border-top: 1px solid {COLORS['border_soft']};
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {COLORS['text_dim']};
    display: flex;
    justify-content: space-between;
}}

/* ──── Segment Cards ──── */
.segment-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0;
    border: 1px solid {COLORS['border_soft']};
    border-radius: 2px;
    margin-bottom: 1rem;
    overflow: hidden;
}}
.segment-card {{
    padding: 1.4rem 1.5rem;
    border-right: 1px solid {COLORS['border_soft']};
    background: {COLORS['surface']};
    position: relative;
}}
.segment-card:last-child {{ border-right: none; }}
.segment-card-bar {{
    position: absolute;
    top: 0; left: 0;
    height: 2px;
    width: 100%;
}}
.segment-card-name {{
    font-family: 'Fraunces', serif;
    font-size: 1.05rem;
    color: {COLORS['text']};
    margin-bottom: 0.2rem;
    margin-top: 0.5rem;
    font-weight: 400;
}}
.segment-card-count {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    color: {COLORS['text_muted']};
    text-transform: uppercase;
}}
.segment-card-stats {{
    margin-top: 0.9rem;
    padding-top: 0.9rem;
    border-top: 1px dashed {COLORS['border_soft']};
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: {COLORS['text_muted']};
    line-height: 1.7;
}}
.segment-card-stats span {{ color: {COLORS['text']}; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Veri Yükleme
# ─────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_data():
    if not CLUSTER_FILE.exists():
        with st.spinner("Pipeline çalıştırılıyor…"):
            sys.path.insert(0, str(BASE_DIR))
            try:
                from preprocessing import run_pipeline
                from clustering    import run_clustering
                run_pipeline()
                run_clustering()
            except Exception as e:
                st.error(f"Pipeline hatası: {type(e).__name__}: {e}")
                st.info("Terminalden manuel çalıştırın: python preprocessing.py — python clustering.py")
                st.stop()
    return pd.read_csv(CLUSTER_FILE)


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

def render_sidebar(df: pd.DataFrame):
    st.sidebar.markdown('<div class="sidebar-eyebrow">Control Panel</div>', unsafe_allow_html=True)
    st.sidebar.markdown("# Filtreler")
    st.sidebar.markdown("---")

    segments = sorted(df["Segment"].unique())
    selected = st.sidebar.multiselect("Segment Seçimi", segments, default=segments)

    st.sidebar.markdown("&nbsp;", unsafe_allow_html=True)
    r_min, r_max = int(df["Recency"].min()), int(df["Recency"].max())
    recency_range = st.sidebar.slider("Recency Aralığı (gün)", r_min, r_max, (r_min, r_max))

    st.sidebar.markdown("---")
    st.sidebar.info(
        "RECENCY · Son alışverişten geçen gün\n\n"
        "FREQUENCY · Toplam sipariş sayısı\n\n"
        "MONETARY · Toplam harcama tutarı"
    )
    return selected, recency_range


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────

def render_header(df: pd.DataFrame):
    total = len(df)
    n_seg = df["Segment"].nunique()
    sil = df["Silhouette"].iloc[0] if "Silhouette" in df.columns else None
    sil_html = f'<span><strong>{sil:.4f}</strong> · Silhouette</span><br/>' if sil else ''

    st.markdown(f"""
    <div class="editorial-header">
        <div>
            <div class="editorial-eyebrow">RFM Analytics — Customer Segmentation</div>
            <h1>Müşteri Davranış<br/>Segmentasyon Paneli</h1>
            <div class="editorial-subtitle">
                K-Means kümeleme algoritması ile Recency, Frequency ve Monetary
                metrikleri üzerinden müşteri portföyünün davranışsal analizi.
            </div>
        </div>
        <div class="editorial-meta">
            <span><strong>{total:,}</strong> · Müşteri</span><br/>
            <span><strong>{n_seg}</strong> · Segment</span><br/>
            {sil_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def section(num: str, title: str, desc: str = ""):
    st.markdown(f"""
    <div class="section-label">
        <div class="section-label-num">/ {num}</div>
        <div class="section-label-title">{title}</div>
        <div class="section-label-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 1. KPI'lar
# ─────────────────────────────────────────────

def render_kpis(df: pd.DataFrame):
    section("01", "Genel Bakış", "Anahtar performans göstergeleri")
    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("Toplam Müşteri",     f"{len(df):,}")
    c2.metric("Ortalama Recency",   f"{df['Recency'].mean():.0f} g")
    c3.metric("Ortalama Frequency", f"{df['Frequency'].mean():.1f}")
    c4.metric("Ortalama Monetary",  f"£{df['Monetary'].mean():,.0f}")


# ─────────────────────────────────────────────
# 2. Segment Profilleri
# ─────────────────────────────────────────────

def render_segment_cards(df: pd.DataFrame):
    section("02", "Segment Profilleri", "Her bir kümenin davranışsal özeti")

    summary = (
        df.groupby("Segment")
        .agg(count=("CustomerID", "count"),
             r=("Recency",   "mean"),
             f=("Frequency", "mean"),
             m=("Monetary",  "mean"))
        .sort_values("m", ascending=False)
    )

    cards = []
    for seg, row in summary.iterrows():
        color = SEGMENT_COLORS.get(seg, COLORS["accent"])
        share = row["count"] / len(df) * 100
        cards.append(
            f'<div class="segment-card">'
            f'<div class="segment-card-bar" style="background:{color};"></div>'
            f'<div class="segment-card-name">{seg}</div>'
            f'<div class="segment-card-count">{int(row["count"]):,} musteri &middot; %{share:.1f}</div>'
            f'<div class="segment-card-stats">'
            f'Recency&nbsp;&nbsp;<span>{row["r"]:.0f} gun</span><br/>'
            f'Frequency <span>{row["f"]:.1f}</span><br/>'
            f'Monetary&nbsp;<span>&pound;{row["m"]:,.0f}</span>'
            f'</div>'
            f'</div>'
        )
    cards_html = '<div class="segment-grid">' + ''.join(cards) + '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. Veri Tablosu
# ─────────────────────────────────────────────

def render_data_table(df: pd.DataFrame):
    section("03", "Müşteri Veritabanı", "Aranabilir, sıralanabilir RFM tablosu")

    col1, col2 = st.columns([3, 1])
    with col2:
        search = st.text_input("Müşteri Ara", placeholder="CustomerID ile ara…", label_visibility="collapsed")

    display = df.copy()
    if search:
        display = display[display["CustomerID"].astype(str).str.contains(search, case=False)]

    st.dataframe(
        display[["CustomerID","Recency","Frequency","Monetary","Cluster","Segment"]]
        .sort_values("Monetary", ascending=False)
        .reset_index(drop=True)
        .style
        .format({"Monetary": "£{:,.2f}", "Recency": "{:.0f} gün"})
        .background_gradient(subset=["Monetary"], cmap="Greys_r", low=0.7)
        .background_gradient(subset=["Recency"],  cmap="Greys_r", low=0.7),
        use_container_width=True,
        height=420,
        hide_index=True,
    )


# ─────────────────────────────────────────────
# 4. 3D Scatter
# ─────────────────────────────────────────────

def render_3d_scatter(df: pd.DataFrame):
    section("04", "Üç Boyutlu Küme Haritası",
            "Recency · Frequency · Monetary uzayında dağılım")

    fig = px.scatter_3d(
        df, x="Recency", y="Frequency", z="Monetary",
        color="Segment", color_discrete_map=SEGMENT_COLORS,
        hover_data={"CustomerID": True, "Cluster": True}, opacity=0.78,
    )
    fig.update_traces(marker=dict(size=3.5, line=dict(width=0)))

    axis_style = dict(
        backgroundcolor="rgba(0,0,0,0)",
        gridcolor=COLORS["border_soft"],
        zerolinecolor=COLORS["border"],
        showbackground=True,
        tickfont=dict(family="JetBrains Mono", size=10, color=COLORS["text_dim"]),
    )

    fig.update_layout(
        height=620,
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(family="Manrope", color=COLORS["text"]),
        legend=dict(
            title=dict(text="SEGMENT",
                       font=dict(family="JetBrains Mono", size=10, color=COLORS["text_muted"])),
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Manrope", size=11, color=COLORS["text"]),
            x=0.02, y=0.98,
        ),
        scene=dict(
            xaxis=dict(**axis_style, title=dict(text="RECENCY (gün)",
                       font=dict(family="JetBrains Mono", size=10, color=COLORS["text_muted"]))),
            yaxis=dict(**axis_style, title=dict(text="FREQUENCY",
                       font=dict(family="JetBrains Mono", size=10, color=COLORS["text_muted"]))),
            zaxis=dict(**axis_style, title=dict(text="MONETARY (£)",
                       font=dict(family="JetBrains Mono", size=10, color=COLORS["text_muted"]))),
            bgcolor=COLORS["surface"],
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.9)),
        ),
        margin=dict(l=0, r=0, b=0, t=20),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# 5. Segment Karşılaştırma
# ─────────────────────────────────────────────

def render_segment_charts(df: pd.DataFrame):
    section("05", "Segment Karşılaştırması", "Müşteri sayısı ve gelir kontribüsyonu")

    raw = (
        df.groupby("Segment")
        .agg(customers=("CustomerID", "count"), revenue=("Monetary", "sum"))
        .reset_index()
    )

    title_font = dict(family="JetBrains Mono", size=11, color=COLORS["text_muted"])

    def _make_title(text):
        return dict(text=text, font=title_font, x=0.02, xanchor="left", pad=dict(t=10, b=10))

    plot_layout = dict(
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(family="Manrope", color=COLORS["text"], size=12),
        height=380,
        margin=dict(l=10, r=40, t=50, b=10),
        showlegend=False,
        xaxis=dict(gridcolor=COLORS["border_soft"], zerolinecolor=COLORS["border"],
                   tickfont=dict(family="JetBrains Mono", size=10, color=COLORS["text_dim"])),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", zerolinecolor=COLORS["border"],
                   tickfont=dict(family="Manrope", size=11, color=COLORS["text"])),
    )

    tab1, tab2, tab3 = st.tabs(["Müşteri Sayısı", "Toplam Gelir", "Pazar Payı"])

    with tab1:
        d1 = raw.sort_values("customers")
        fig1 = go.Figure(go.Bar(
            x=d1["customers"], y=d1["Segment"], orientation="h",
            marker=dict(color=[SEGMENT_COLORS.get(s, COLORS["accent"]) for s in d1["Segment"]]),
            text=d1["customers"].map("{:,}".format),
            textposition="outside",
            textfont=dict(family="JetBrains Mono", color=COLORS["text"], size=11),
        ))
        fig1.update_layout(title=_make_title("SEGMENT BASINA MUSTERI"), **plot_layout)
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        d2 = raw.sort_values("revenue")
        fig2 = go.Figure(go.Bar(
            x=d2["revenue"], y=d2["Segment"], orientation="h",
            marker=dict(color=[SEGMENT_COLORS.get(s, COLORS["accent"]) for s in d2["Segment"]]),
            text=d2["revenue"].map("£{:,.0f}".format),
            textposition="outside",
            textfont=dict(family="JetBrains Mono", color=COLORS["text"], size=11),
        ))
        fig2.update_layout(title=_make_title("SEGMENT BASINA TOPLAM GELIR"), **plot_layout)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        fig3 = go.Figure(go.Pie(
            labels=raw["Segment"], values=raw["customers"],
            marker=dict(
                colors=[SEGMENT_COLORS.get(s, COLORS["accent"]) for s in raw["Segment"]],
                line=dict(color=COLORS["bg"], width=3),
            ),
            hole=0.62,
            textfont=dict(family="JetBrains Mono", size=10, color=COLORS["bg"]),
            textinfo="percent",
        ))
        fig3.update_layout(
            paper_bgcolor=COLORS["surface"],
            plot_bgcolor=COLORS["surface"],
            font=dict(family="Manrope", color=COLORS["text"]),
            height=380,
            margin=dict(l=10, r=10, t=50, b=10),
            title=dict(text="MÜŞTERİ DAĞILIMI",
                       font=dict(family="JetBrains Mono", size=11, color=COLORS["text_muted"]),
                       x=0.02, xanchor="left"),
            showlegend=True,
            legend=dict(font=dict(family="Manrope", size=11, color=COLORS["text"]),
                        bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(
                text=f"{len(df):,}<br><span style='font-size:10px;color:{COLORS['text_muted']}'>MÜŞTERİ</span>",
                font=dict(family="Fraunces", size=24, color=COLORS["text"]),
                showarrow=False,
            )],
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# 6. Elbow
# ─────────────────────────────────────────────

def render_elbow():
    if not ELBOW_IMAGE.exists():
        return
    section("06", "Optimum K Tespiti", "Elbow ve Silhouette analiz çıktıları")
    st.image(str(ELBOW_IMAGE), use_column_width=True)


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────

def render_footer():
    st.markdown("""
    <div class="footer-credit">
        <span>RFM Analytics · K-Means Clustering</span>
        <span>StandardScaler · log1p · Plotly · Streamlit</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    df = load_data()
    selected, recency_range = render_sidebar(df)

    filtered = df[
        (df["Segment"].isin(selected)) &
        (df["Recency"] >= recency_range[0]) &
        (df["Recency"] <= recency_range[1])
    ].copy()

    render_header(df)

    if filtered.empty:
        st.warning("Seçili filtreler için veri bulunamadı.")
        return

    render_kpis(filtered)
    render_segment_cards(filtered)
    render_data_table(filtered)
    render_3d_scatter(filtered)
    render_segment_charts(filtered)
    render_elbow()
    render_footer()


if __name__ == "__main__":
    main()