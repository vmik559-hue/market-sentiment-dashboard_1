
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from streamlit_extras.colored_header import colored_header
import os

# ==================== CONFIGURATION ====================
st.set_page_config(
    page_title="Market Sentiment AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Premium Cards & Lists
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    h1 {text-align: center; font-size: 2.5rem; font-weight: 800; color: #0E1117; margin-bottom: 0px;}
    p {font-size: 1rem; color: #666;}

    /* Card Style for Top Lists */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        height: 100%;
    }

    /* List Items */
    .list-item {
        display: flex;
        justify_content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        font-size: 1rem;
    }
    .list-item:last-child {border-bottom: none;}

    /* Colors */
    .score-pos { color: #2ca02c; font-weight: bold; }
    .score-neg { color: #d62728; font-weight: bold; }
    .sector-tag { color: #555; font-size: 0.85rem; font-style: italic;}

    </style>
    """, unsafe_allow_html=True)

# ==================== PATH CONFIGURATION (FIXED) ====================
# This logic works in both Jupyter Notebooks AND Python Scripts
try:
    BASE_PATH = Path(__file__).parent
except NameError:
    BASE_PATH = Path(os.getcwd())

EXCEL_FILE = BASE_PATH / "Sentiment_Analysis_Production.xlsx"

# ==================== DATA LOADING ====================
@st.cache_data
def load_data():
    if not EXCEL_FILE.exists(): return None
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name='Quarterly Sentiment')
        df['Date_Str'] = df['Month'] + ' ' + df['Year'].astype(str)
        df['Date'] = pd.to_datetime(df['Date_Str'], format='%b %Y')
        df = df.sort_values(['Company', 'Date'])

        if 'Overall_Score' in df.columns: df['Score'] = df['Overall_Score']
        elif 'Overall_Sentiment' in df.columns: df['Score'] = df['Overall_Sentiment']
        return df
    except Exception as e:
        st.error(f"Error: {e}"); return None

# ==================== MAIN UI ====================
def main():
    df = load_data()
    if df is None: 
        st.error(f"❌ Data file not found at: {EXCEL_FILE}")
        st.stop()

    # --- 1. HERO HEADER ---
    st.markdown("<h1>Indian Market Sentiment Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Analysis of Corporate Earnings Calls & Reports</p>", unsafe_allow_html=True)
    st.markdown("---")

    # --- 2. THREE-COLUMN METRIC CARDS ---
    latest_df = df.sort_values('Date').groupby('Company').tail(1)

    c1, c2, c3 = st.columns(3)

    # COLUMN 1: TOP POSITIVE
    with c1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        colored_header(label="Top Positive", description="Highest sentiment scores", color_name="green-70")
        top_pos = latest_df.sort_values('Score', ascending=False).head(5)

        for _, row in top_pos.iterrows():
            st.markdown(f"""
            <div class="list-item">
                <b>{row['Company']}</b> 
                <span class="score-pos">: {row['Score']:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # COLUMN 2: TOP NEGATIVE
    with c2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        colored_header(label="Top Negative", description="Lowest sentiment scores", color_name="red-70")
        top_neg = latest_df.sort_values('Score', ascending=True).head(5)

        for _, row in top_neg.iterrows():
            st.markdown(f"""
            <div class="list-item">
                <b>{row['Company']}</b> 
                <span class="score-neg">: {row['Score']:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # COLUMN 3: SECTOR AVERAGE
    with c3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        colored_header(label="Sector Average", description="Best performing industries", color_name="blue-70")
        sector_avg = latest_df.groupby('Sector')['Score'].mean().sort_values(ascending=False).head(5)

        for sector, score in sector_avg.items():
            color_class = "score-pos" if score > 0 else "score-neg"
            st.markdown(f"""
            <div class="list-item">
                <b>{sector}</b>
                <span class="{color_class}">: {score:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("###") # Spacer

    # --- 3. HEATMAP & HISTOGRAM ---
    col_heat, col_dist = st.columns([2, 1])

    with col_heat:
        st.subheader("Sector Performance Map")
        sector_perf = latest_df.groupby('Sector')[['Score']].mean().reset_index()
        sector_perf['Count'] = latest_df.groupby('Sector')['Company'].count().values

        fig_heat = px.treemap(sector_perf, path=['Sector'], values='Count', color='Score', 
                              color_continuous_scale='RdYlGn', range_color=[-0.5, 0.5])
        fig_heat.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=320)
        fig_heat.data[0].textinfo = "label+text+value"
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_dist:
        st.subheader("Market Spread")
        fig_hist = px.histogram(latest_df, x="Score", nbins=15, color_discrete_sequence=['#4C78A8'])
        fig_hist.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=320, xaxis_title="Score", showlegend=False, template="plotly_white")
        fig_hist.add_vline(x=0, line_dash="dot", line_color="black")
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- 4. DEEP DIVE SECTION ---
    colored_header(label="Company Deep Dive", description="Analyze individual trends", color_name="blue-70")

    c_nav, c_graph = st.columns([1, 3])

    with c_nav:
        st.write("###### Filters")
        sectors = ["All Sectors"] + sorted(df['Sector'].unique().tolist())
        sel_sector = st.selectbox("Industry", sectors)

        if sel_sector != "All Sectors":
            comps = sorted(df[df['Sector'] == sel_sector]['Company'].unique())
        else:
            comps = sorted(df['Company'].unique())

        sel_comp = st.selectbox("Company Name", comps)
        compare_comp = st.selectbox("Compare With (Optional)", ["None"] + [c for c in comps if c != sel_comp])

        if sel_comp:
            st.divider()
            row = latest_df[latest_df['Company'] == sel_comp].iloc[0]
            st.metric("Current Score", f"{row['Score']:.2f}")
            st.caption(f"Sector: {row['Sector']}")
            st.caption(f"Latest: {row['Month']} {row['Year']}")

    with c_graph:
        if sel_comp:
            comp_data = df[df['Company'] == sel_comp]

            fig = go.Figure()

            # 1. Main Line
            fig.add_trace(go.Scatter(x=comp_data['Date'], y=comp_data['Score'],
                                     mode='lines+markers', name=sel_comp,
                                     line=dict(color='#1f77b4', width=4),
                                     marker=dict(size=10, color=comp_data['Score'], colorscale='RdYlGn', cmin=-0.5, cmax=0.5)))

            # 2. Comparison Line
            if compare_comp != "None":
                comp2_data = df[df['Company'] == compare_comp]
                fig.add_trace(go.Scatter(x=comp2_data['Date'], y=comp2_data['Score'],
                                         mode='lines+markers', name=compare_comp,
                                         line=dict(color='#ff7f0e', width=3, dash='dot')))

            # 3. Background Zones
            fig.add_hrect(y0=0, y1=1.5, fillcolor="green", opacity=0.05, line_width=0)
            fig.add_hrect(y0=-1.5, y1=0, fillcolor="red", opacity=0.05, line_width=0)

            fig.update_layout(
                title=dict(text=f"Sentiment Trend Analysis", font=dict(size=18)),
                yaxis_title="Sentiment Score",
                yaxis=dict(range=[-1.1, 1.1]),
                height=450,
                hovermode="x unified",
                template="plotly_white",
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- 5. DETAILED DATA GRID ---
    with st.expander("View & Download Raw Data"):
        st.dataframe(
            latest_df[['Company', 'Sector', 'Score', 'Month', 'Year']].sort_values('Score', ascending=False),
            use_container_width=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Sentiment Score",
                    help="AI Score from -1 to +1",
                    format="%.2f",
                    min_value=-1,
                    max_value=1,
                ),
            }
        )

if __name__ == "__main__":
    main()

