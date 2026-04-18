import math
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Document Similarity Intelligence Hub",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = PROJECT_ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

OUTPUTS_CSV = RESULTS_DIR / "outputs.csv"
METRICS_TXT = RESULTS_DIR / "metrics.txt"


# ---------------------------------------------------------
# STYLING
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f8fbff 0%, #eef6ff 28%, #fdfcff 68%, #f7fbf8 100%);
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.8rem;
        max-width: 1480px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5fbff 0%, #edf6ff 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.12);
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(96,165,250,0.18), rgba(168,85,247,0.14), rgba(34,197,94,0.14), rgba(251,191,36,0.16));
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 24px;
        padding: 1.4rem 1.6rem 1.2rem 1.6rem;
        box-shadow: 0 10px 30px rgba(90, 132, 255, 0.08);
        margin-bottom: 1rem;
    }

    .soft-card {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(99, 102, 241, 0.10);
        border-radius: 22px;
        padding: 1rem 1rem 0.7rem 1rem;
        box-shadow: 0 10px 24px rgba(31, 41, 55, 0.06);
        backdrop-filter: blur(8px);
        margin-bottom: 1rem;
    }

    .kpi-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(245,249,255,0.92));
        border: 1px solid rgba(99, 102, 241, 0.10);
        border-radius: 22px;
        padding: 1rem 1rem;
        min-height: 116px;
        box-shadow: 0 10px 24px rgba(31, 41, 55, 0.05);
    }

    .kpi-title {
        font-size: 0.92rem;
        color: #64748b;
        margin-bottom: 0.35rem;
        font-weight: 600;
    }

    .kpi-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.18rem;
    }

    .kpi-sub {
        font-size: 0.84rem;
        color: #64748b;
    }

    .mini-pill {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(59,130,246,0.10);
        color: #1d4ed8;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-top: 0.25rem;
    }

    .flow-box {
        border-radius: 22px;
        padding: 1rem 1rem;
        background: linear-gradient(180deg, rgba(255,255,255,0.90), rgba(243,248,255,0.95));
        border: 1px solid rgba(99, 102, 241, 0.10);
        box-shadow: 0 10px 24px rgba(31, 41, 55, 0.05);
    }

    .flow-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }

    .flow-step {
        flex: 1;
        min-width: 130px;
        text-align: center;
        padding: 0.8rem 0.7rem;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(224,242,254,0.95), rgba(255,255,255,0.95));
        border: 1px solid rgba(59,130,246,0.12);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.25);
        position: relative;
        overflow: hidden;
    }

    .flow-step::after {
        content: "";
        position: absolute;
        top: 0;
        left: -30%;
        width: 30%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.7), transparent);
        animation: shimmer 2.7s infinite;
    }

    @keyframes shimmer {
        0% { left: -35%; }
        100% { left: 120%; }
    }

    .flow-arrow {
        font-size: 1.5rem;
        color: #60a5fa;
        font-weight: 700;
    }

    .doc-preview-card {
        background: rgba(255,255,255,0.85);
        border: 1px solid rgba(99,102,241,0.10);
        border-radius: 20px;
        padding: 0.95rem 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 8px 20px rgba(31,41,55,0.05);
    }

    .small-muted {
        color: #64748b;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATA HELPERS
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_results() -> pd.DataFrame:
    if OUTPUTS_CSV.exists():
        df = pd.read_csv(OUTPUTS_CSV)
        if not df.empty:
            if "similarity" in df.columns:
                df["similarity"] = pd.to_numeric(df["similarity"], errors="coerce")
            for col in ["doc1", "doc2"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)
        return df
    return pd.DataFrame(columns=["doc1", "doc2", "similarity"])


@st.cache_data(show_spinner=False)
def load_documents():
    docs = []
    if RAW_DIR.exists():
        for file_path in sorted(RAW_DIR.glob("*.txt")):
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                docs.append(
                    {
                        "doc_id": file_path.stem,
                        "filename": file_path.name,
                        "chars": len(text),
                        "words": len(text.split()),
                        "preview": text[:1600],
                        "full_text": text,
                    }
                )
            except Exception:
                continue
    return docs


@st.cache_data(show_spinner=False)
def load_metrics_text() -> str:
    if METRICS_TXT.exists():
        return METRICS_TXT.read_text(encoding="utf-8", errors="ignore")
    return "No metrics file found."


def build_kpis(df: pd.DataFrame, docs: list[dict]) -> dict:
    total_docs = len(docs)
    total_pairs = len(df)
    avg_similarity = round(float(df["similarity"].mean()), 4) if not df.empty else 0.0
    max_similarity = round(float(df["similarity"].max()), 4) if not df.empty else 0.0
    connected_docs = 0
    if not df.empty:
        connected_docs = len(set(df["doc1"]).union(set(df["doc2"])))
    return {
        "total_docs": total_docs,
        "total_pairs": total_pairs,
        "avg_similarity": avg_similarity,
        "max_similarity": max_similarity,
        "connected_docs": connected_docs,
    }


def paginate_df(df: pd.DataFrame, page_size: int, page_number: int) -> pd.DataFrame:
    start = (page_number - 1) * page_size
    end = start + page_size
    return df.iloc[start:end]


def paginate_list(items: list, page_size: int, page_number: int) -> list:
    start = (page_number - 1) * page_size
    end = start + page_size
    return items[start:end]


def build_graph(df: pd.DataFrame, max_edges: int = 220) -> nx.Graph:
    G = nx.Graph()
    if df.empty:
        return G
    slim = df.sort_values("similarity", ascending=False).head(max_edges)
    for _, row in slim.iterrows():
        G.add_edge(str(row["doc1"]), str(row["doc2"]), weight=float(row["similarity"]))
    return G


# ---------------------------------------------------------
# VISUAL HELPERS
# ---------------------------------------------------------
def render_kpi(title: str, value: str, subtitle: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_flow():
    st.markdown(
        """
        <div class="flow-box">
            <h3 style="margin-top:0; color:#1e3a8a;">Live Pipeline Storyboard</h3>
            <div class="small-muted">An animated view of how documents move through the similarity engine.</div>
            <div class="flow-row">
                <div class="flow-step"><b>Raw Documents</b><br><span class="small-muted">TXT / Upload / API</span></div>
                <div class="flow-arrow">→</div>
                <div class="flow-step"><b>Preprocessing</b><br><span class="small-muted">Clean • Tokenize • Filter</span></div>
                <div class="flow-arrow">→</div>
                <div class="flow-step"><b>Shingling</b><br><span class="small-muted">2-gram / 3-gram sets</span></div>
                <div class="flow-arrow">→</div>
                <div class="flow-step"><b>MinHash + LSH</b><br><span class="small-muted">Fast candidate detection</span></div>
                <div class="flow-arrow">→</div>
                <div class="flow-step"><b>Similarity Results</b><br><span class="small-muted">Pairs • Scores • Insights</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def similarity_distribution(df: pd.DataFrame):
    if df.empty:
        st.info("No similarity data available.")
        return
    fig = px.histogram(
        df,
        x="similarity",
        nbins=25,
        title="Similarity Score Distribution",
        template="plotly_white",
    )
    fig.update_traces(marker_color="#60a5fa", marker_line_color="#2563eb", marker_line_width=1)
    fig.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.65)",
        title_font=dict(size=20, color="#1e3a8a"),
        xaxis_title="Similarity Score",
        yaxis_title="Frequency",
    )
    st.plotly_chart(fig, use_container_width=True)


def top_pairs_chart(df: pd.DataFrame, top_n: int):
    if df.empty:
        st.info("No result data available.")
        return
    top_df = df.sort_values("similarity", ascending=False).head(top_n).copy()
    top_df["pair"] = top_df["doc1"].astype(str) + " ↔ " + top_df["doc2"].astype(str)
    fig = px.bar(
        top_df,
        x="similarity",
        y="pair",
        orientation="h",
        title=f"Top {top_n} Similar Document Pairs",
        template="plotly_white",
        color="similarity",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.65)",
        title_font=dict(size=20, color="#1e3a8a"),
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig, use_container_width=True)


def doc_size_chart(docs: list[dict]):
    if not docs:
        st.info("No documents available.")
        return
    df = pd.DataFrame(docs)
    fig = px.scatter(
        df,
        x="words",
        y="chars",
        size="words",
        hover_name="filename",
        title="Document Size Landscape",
        template="plotly_white",
        color="words",
        color_continuous_scale="Tealgrn",
    )
    fig.update_layout(
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.65)",
        title_font=dict(size=20, color="#1e3a8a"),
    )
    st.plotly_chart(fig, use_container_width=True)


def animated_dataflow_3d(df: pd.DataFrame):
    if df.empty:
        st.info("No result data available for 3D flow view.")
        return

    top_df = df.sort_values("similarity", ascending=False).head(80).copy().reset_index(drop=True)

    steps = {
        "Input": 0,
        "Preprocess": 1,
        "Shingles": 2,
        "LSH": 3,
        "Output": 4,
    }

    nodes = []
    for idx, row in top_df.iterrows():
        base_y = idx
        sim = float(row["similarity"])
        z = sim * 10

        for step_name, x in steps.items():
            nodes.append(
                {
                    "x": x,
                    "y": base_y,
                    "z": z + (x * 0.08),
                    "label": f"{row['doc1']} ↔ {row['doc2']}<br>{step_name}<br>Similarity: {sim:.4f}",
                    "step": step_name,
                    "sim": sim,
                }
            )

    node_df = pd.DataFrame(nodes)

    fig = go.Figure()

    for idx, row in top_df.iterrows():
        sim = float(row["similarity"])
        y = idx
        z = sim * 10
        xs = [0, 1, 2, 3, 4]
        ys = [y, y, y, y, y]
        zs = [z, z + 0.08, z + 0.16, z + 0.24, z + 0.32]

        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="lines",
                line=dict(color=f"rgba(37,99,235,{0.20 + sim * 0.6})", width=6),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter3d(
            x=node_df["x"],
            y=node_df["y"],
            z=node_df["z"],
            mode="markers",
            text=node_df["label"],
            hoverinfo="text",
            marker=dict(
                size=6,
                color=node_df["sim"],
                colorscale="Viridis",
                colorbar=dict(title="Similarity"),
                opacity=0.90,
            ),
            showlegend=False,
        )
    )

    fig.update_layout(
        title="3D Animated Data Flow View",
        template="plotly_white",
        height=720,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=60, b=0),
        scene=dict(
            xaxis=dict(
                title="Pipeline Stage",
                tickmode="array",
                tickvals=list(steps.values()),
                ticktext=list(steps.keys()),
                backgroundcolor="rgba(239,246,255,0.65)",
                gridcolor="rgba(148,163,184,0.3)",
            ),
            yaxis=dict(
                title="Pair Index",
                backgroundcolor="rgba(239,246,255,0.65)",
                gridcolor="rgba(148,163,184,0.3)",
            ),
            zaxis=dict(
                title="Similarity Elevation",
                backgroundcolor="rgba(239,246,255,0.65)",
                gridcolor="rgba(148,163,184,0.3)",
            ),
            camera=dict(eye=dict(x=1.8, y=1.55, z=1.15)),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def similarity_network_3d(df: pd.DataFrame, max_edges: int = 120):
    G = build_graph(df, max_edges=max_edges)
    if G.number_of_nodes() == 0:
        st.info("No graph data available for 3D view.")
        return

    pos = nx.spring_layout(G, dim=3, seed=42)

    edge_x, edge_y, edge_z = [], [], []
    for u, v in G.edges():
        x0, y0, z0 = pos[u]
        x1, y1, z1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_z += [z0, z1, None]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line=dict(color="rgba(96,165,250,0.35)", width=4),
            hoverinfo="none",
            showlegend=False,
        )
    )

    node_x, node_y, node_z, text, size, color = [], [], [], [], [], []
    for node in G.nodes():
        x, y, z = pos[node]
        degree = G.degree(node)
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        size.append(8 + degree * 2)
        color.append(degree)
        text.append(f"{node}<br>Connections: {degree}")

    fig.add_trace(
        go.Scatter3d(
            x=node_x,
            y=node_y,
            z=node_z,
            mode="markers+text",
            text=["" for _ in node_x],
            hovertext=text,
            hoverinfo="text",
            marker=dict(
                size=size,
                color=color,
                colorscale="Plasma",
                opacity=0.95,
                colorbar=dict(title="Connectivity"),
            ),
            showlegend=False,
        )
    )

    fig.update_layout(
        title="3D Similarity Network Universe",
        template="plotly_white",
        height=720,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=60, b=0),
        scene=dict(
            xaxis=dict(showbackground=True, backgroundcolor="rgba(239,246,255,0.65)"),
            yaxis=dict(showbackground=True, backgroundcolor="rgba(239,246,255,0.65)"),
            zaxis=dict(showbackground=True, backgroundcolor="rgba(239,246,255,0.65)"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def show_plot_gallery():
    images = []
    if PLOTS_DIR.exists():
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            images.extend(sorted(PLOTS_DIR.glob(ext)))

    if not images:
        st.info("No plot images found in results/plots.")
        return

    if "gallery_page" not in st.session_state:
        st.session_state.gallery_page = 1

    per_page = 1
    total_pages = max(1, math.ceil(len(images) / per_page))

    cols = st.columns([1, 1, 2])
    with cols[0]:
        if st.button("⬅ Previous", use_container_width=True, key="gallery_prev"):
            st.session_state.gallery_page = max(1, st.session_state.gallery_page - 1)
    with cols[1]:
        if st.button("Next ➡", use_container_width=True, key="gallery_next"):
            st.session_state.gallery_page = min(total_pages, st.session_state.gallery_page + 1)
    with cols[2]:
        st.caption(f"Image page {st.session_state.gallery_page} of {total_pages}")

    page_images = paginate_list(images, per_page, st.session_state.gallery_page)
    for image_path in page_images:
        st.image(str(image_path), caption=image_path.name, use_container_width=True)


# ---------------------------------------------------------
# API CONTROLS
# ---------------------------------------------------------
def api_controls():
    st.markdown("### API Studio")
    st.caption("Upload text directly or choose a local .txt file from your device.")

    api_base = st.text_input("API base URL", value="http://127.0.0.1:5000")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Ping /health", use_container_width=True):
            try:
                resp = requests.get(f"{api_base}/health", timeout=5)
                st.success(f"API healthy: {resp.status_code}")
                try:
                    st.json(resp.json())
                except Exception:
                    st.write(resp.text)
            except Exception as e:
                st.error(f"Health check failed: {e}")

    with c2:
        if st.button("Show API usage note", use_container_width=True):
            st.info("The upload action sends JSON with text and optional filename to the API.")

    st.markdown("---")

    mode = st.radio(
        "Choose input mode",
        ["Type text", "Upload .txt file from device"],
        horizontal=True,
    )

    upload_text = ""
    upload_filename = ""

    if mode == "Type text":
        upload_text = st.text_area(
            "Document text",
            value="This is a new sample document for similarity ingestion.",
            height=180,
        )
        upload_filename = st.text_input(
            "Optional filename",
            value="dashboard_uploaded_doc.txt",
        )
    else:
        uploaded_file = st.file_uploader("Choose a .txt file", type=["txt"])
        if uploaded_file is not None:
            try:
                upload_text = uploaded_file.read().decode("utf-8", errors="ignore")
                upload_filename = uploaded_file.name
                st.success(f"Loaded file: {upload_filename}")
                st.text_area("File preview", value=upload_text[:3000], height=220)
            except Exception as e:
                st.error(f"Could not read uploaded file: {e}")

    if st.button("Upload document to API", type="primary", use_container_width=True):
        if not upload_text.strip():
            st.warning("Please enter text or upload a .txt file first.")
        else:
            payload = {"text": upload_text, "filename": upload_filename}
            try:
                resp = requests.post(f"{api_base}/upload", json=payload, timeout=20)
                st.success(f"Upload response: {resp.status_code}")
                try:
                    st.json(resp.json())
                except Exception:
                    st.write(resp.text)
            except Exception as e:
                st.error(f"Upload failed: {e}")


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Control Center")
    auto_refresh = st.toggle("Auto refresh", value=False)
    refresh_seconds = st.slider("Refresh every (sec)", 5, 60, 10)
    if auto_refresh and st_autorefresh is not None:
        st_autorefresh(interval=refresh_seconds * 1000, key="dash_refresh")

    st.markdown("---")
    list_mode = st.toggle("List mode for results", value=False)
    show_only_high = st.toggle("Show only high-similarity pairs", value=False)
    threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.5, 0.01)

    st.markdown("---")
    st.subheader("Analytics Scope")
    top_n = st.slider("Top pairs to visualize", 5, 50, 20)
    rows_per_page = st.slider("Rows per page", 5, 50, 10)
    docs_per_page = st.slider("Documents per page", 3, 20, 6)

    st.markdown("---")
    st.markdown('<span class="mini-pill">Light UI</span><span class="mini-pill">3D Visuals</span><span class="mini-pill">Interactive</span>', unsafe_allow_html=True)
    st.caption("Built for clear, high-level similarity exploration.")


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
results_df = load_results()
documents = load_documents()
metrics_text = load_metrics_text()

if show_only_high and not results_df.empty:
    results_df = results_df[results_df["similarity"] >= threshold].copy()

kpis = build_kpis(results_df, documents)

# ---------------------------------------------------------
# HERO
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero-card">
        <h1 style="margin-bottom:0.2rem; color:#1e3a8a;">📘 Document Similarity Intelligence Hub</h1>
        <div style="font-size:1.05rem; color:#475569; margin-bottom:0.45rem;">
            A vibrant, executive-style control dashboard for document similarity discovery, monitoring, analytics, and API interaction.
        </div>
        <span class="mini-pill">Scalable Analysis</span>
        <span class="mini-pill">Explorable Results</span>
        <span class="mini-pill">3D Visual Storytelling</span>
        <span class="mini-pill">API Studio</span>
    </div>
    """,
    unsafe_allow_html=True,
)

render_pipeline_flow()

st.markdown("")

# ---------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_kpi("Documents", str(kpis["total_docs"]), "Indexed source documents")
with k2:
    render_kpi("Matched Pairs", str(kpis["total_pairs"]), "Threshold-qualified pairs")
with k3:
    render_kpi("Average Similarity", str(kpis["avg_similarity"]), "Across visible results")
with k4:
    render_kpi("Peak Similarity", str(kpis["max_similarity"]), "Best matching pair")
with k5:
    render_kpi("Connected Docs", str(kpis["connected_docs"]), "Documents appearing in matches")

st.markdown("")

# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Overview",
        "Results Explorer",
        "3D Analytics",
        "Document Browser",
        "API Controls",
    ]
)

# ---------------------------------------------------------
# TAB 1
# ---------------------------------------------------------
with tab1:
    left, right = st.columns([1.15, 0.85])

    with left:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        similarity_distribution(results_df)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown("### Run Summary")
        st.text_area("Metrics log", value=metrics_text, height=360)
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns([1.1, 0.9])
    with b1:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        top_pairs_chart(results_df, top_n)
        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown("### Plot Gallery")
        show_plot_gallery()
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2
# ---------------------------------------------------------
with tab2:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown("### Results Explorer")

    df = results_df.copy()

    if not df.empty:
        min_sim = float(df["similarity"].min())
        max_sim = float(df["similarity"].max())
    else:
        min_sim, max_sim = 0.0, 1.0

    f1, f2, f3 = st.columns([1, 1, 1.2])
    with f1:
        sim_range = st.slider(
            "Similarity range",
            min_value=0.0,
            max_value=1.0,
            value=(max(0.0, min_sim), min(1.0, max_sim)),
            step=0.01,
        )
    with f2:
        order = st.selectbox("Sort order", ["Highest first", "Lowest first"])
    with f3:
        keyword = st.text_input("Filter by document id / filename", value="")

    if not df.empty:
        df = df[(df["similarity"] >= sim_range[0]) & (df["similarity"] <= sim_range[1])]
        if keyword.strip():
            kw = keyword.strip().lower()
            df = df[
                df["doc1"].astype(str).str.lower().str.contains(kw)
                | df["doc2"].astype(str).str.lower().str.contains(kw)
            ]
        df = df.sort_values("similarity", ascending=(order == "Lowest first")).reset_index(drop=True)

    total_pages = max(1, math.ceil(len(df) / rows_per_page)) if len(df) else 1
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    page_df = paginate_df(df, rows_per_page, page)

    st.caption(f"Showing {len(page_df)} row(s) out of {len(df)} filtered result(s).")

    if list_mode:
        for idx, row in page_df.iterrows():
            st.markdown(
                f"""
                <div class="doc-preview-card">
                    <div style="font-weight:700; color:#1e3a8a; font-size:1.05rem;">{row['doc1']} ↔ {row['doc2']}</div>
                    <div class="small-muted">Similarity score: {row['similarity']:.4f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.dataframe(page_df, use_container_width=True, height=500)

    st.download_button(
        "Download filtered results as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_similarity_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 3
# ---------------------------------------------------------
with tab3:
    top, bottom = st.columns([1, 1])

    with top:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        animated_dataflow_3d(results_df)
        st.markdown("</div>", unsafe_allow_html=True)

    with bottom:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        doc_size_chart(documents)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    similarity_network_3d(results_df, max_edges=140)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 4
# ---------------------------------------------------------
with tab4:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown("### Document Browser")

    if documents:
        query = st.text_input("Search document filename or id", value="")
        filtered_docs = documents

        if query.strip():
            q = query.strip().lower()
            filtered_docs = [
                d for d in documents
                if q in d["filename"].lower() or q in d["doc_id"].lower()
            ]

        total_doc_pages = max(1, math.ceil(len(filtered_docs) / docs_per_page)) if filtered_docs else 1
        doc_page = st.number_input(
            "Document page",
            min_value=1,
            max_value=total_doc_pages,
            value=1,
            step=1,
            key="doc_page",
        )
        docs_page = paginate_list(filtered_docs, docs_per_page, doc_page)

        st.caption(f"Showing {len(docs_page)} document(s) out of {len(filtered_docs)} result(s).")

        for doc in docs_page:
            with st.expander(f"📄 {doc['filename']} | Words: {doc['words']} | Chars: {doc['chars']}", expanded=False):
                st.text_area(
                    f"Preview - {doc['filename']}",
                    value=doc["preview"],
                    height=220,
                    key=f"preview_{doc['filename']}",
                )
                st.download_button(
                    f"Download {doc['filename']}",
                    data=doc["full_text"].encode("utf-8"),
                    file_name=doc["filename"],
                    mime="text/plain",
                    key=f"download_{doc['filename']}",
                )
    else:
        st.info("No documents found in data/raw.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 5
# ---------------------------------------------------------
with tab5:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    api_controls()
    st.markdown("</div>", unsafe_allow_html=True)