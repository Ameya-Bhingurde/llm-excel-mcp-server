import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import time
import sys

# Add parent directory to path to import from app module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Import Excel operations directly
from app.excel_ops import (
    load_excel,
    clean_sheet,
    profile_data,
    prepare_chart_data,
    create_pivot_table as create_pivot,
    insert_formula as insert_formula_to_excel,
    save_excel
)
from app.llm_service import generate_formula_from_intent

# Import Plotly - Explicit Try/Except with Logging
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_files"


# -----------------------------------------------------------------------------
# UTILS
# -----------------------------------------------------------------------------

def save_uploaded_file(uploaded_file) -> str:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    target = SAMPLE_DIR / uploaded_file.name
    with target.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    return uploaded_file.name


# -----------------------------------------------------------------------------
# THEME & AESTHETICS (ANTIGRAVITY V2)
# -----------------------------------------------------------------------------

def inject_theme():
    # CSS: Transparent backgrounds to allow the Spotlight to shine through
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
        
        /* Force transparency on main app containers so the fixed background is visible */
        .stApp {
            background-color: transparent !important;
        }
        
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* Typography */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            color: #e2e8f0;
        }

        /* Input styling */
        .stTextInput > div > div > input, 
        .stMultiSelect > div > div > div, 
        .stSelectbox > div > div > div,
        .stTextArea > div > div > textarea {
            background-color: rgba(20, 20, 25, 0.7) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 10px;
        }
        
        /* Glass Card */
        .glass-card {
            background: rgba(13, 13, 16, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        }

        /* Primary Button */
        .stButton > button {
            background: linear-gradient(90deg, #7c3aed, #db2777);
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-weight: 600;
            color: white;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
        }
        .stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(219, 39, 119, 0.6);
        }
        
        /* Remove Sidebar if any remains */
        [data-testid="stSidebar"] {
            display: none;
        }

        /* H1 Gradient */
        h1 {
            background: linear-gradient(to right, #c4b5fd, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3.5rem;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # JS: The Spotlight Effect
    spotlight_script = """
    <script>
    (function() {
        const doc = window.parent.document;
        
        const old = doc.getElementById('spotlight-canvas');
        if (old) old.remove();

        const canvas = doc.createElement('div');
        canvas.id = 'spotlight-canvas';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100vw';
        canvas.style.height = '100vh';
        canvas.style.zIndex = '-1';
        canvas.style.background = '#020205'; // Deep black base
        canvas.style.pointerEvents = 'none';
        
        const glow = doc.createElement('div');
        glow.style.position = 'absolute';
        glow.style.width = '800px';
        glow.style.height = '800px';
        glow.style.borderRadius = '50%';
        glow.style.background = 'radial-gradient(circle, rgba(139, 92, 246, 0.25) 0%, rgba(0,0,0,0) 70%)';
        glow.style.transform = 'translate(-50%, -50%)';
        glow.style.pointerEvents = 'none';
        glow.style.transition = 'opacity 0.5s ease';
        
        canvas.appendChild(glow);
        doc.body.appendChild(canvas);

        doc.addEventListener('mousemove', (e) => {
            glow.style.left = e.clientX + 'px';
            glow.style.top = e.clientY + 'px';
        });
    })();
    </script>
    """
    components.html(spotlight_script, height=0, width=0)


# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="AutoXL", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
    inject_theme()

    # -- Header Section (Centered) --
    
    st.markdown("<div style='text-align: center; margin-bottom: 2rem;'><h1>AutoXL</h1><p style='color: #94a3b8;'>Intelligent Data Automation</p></div>", unsafe_allow_html=True)
    
    # Center the uploader
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        uploaded_file = st.file_uploader("Upload an Excel file (.xlsx)", type="xlsx", label_visibility="visible")

    if not uploaded_file:
        # Welcome / Empty State
        st.markdown(
            """
            <div class='glass-card' style='text-align: center; margin-top: 4rem; border: 1px dashed rgba(255,255,255,0.1);'>
                <h2 style='color: #c4b5fd;'>Ready to Excelerate?</h2>
                <p style='font-size: 1.2rem; color: #94a3b8;'>
                    Upload your spreadsheet above to unlock intelligent analysis.<br>
                    Try the new <strong>Auto-QA</strong> feature to chat with your data.
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        return

    # -- Processing --
    try:
        rel_path = save_uploaded_file(uploaded_file)
        if "file_path" not in st.session_state or st.session_state.file_path != rel_path:
            st.session_state.file_path = rel_path
            st.session_state.sheet_name = "Sales"
            st.session_state.analyze_result = None
            st.session_state.clean_summary = None
            st.session_state.pivot_data = None
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return

    # -- Main Tabs --
    tabs = st.tabs(["📊 Visual Analysis", "🌪️ Smart Pivot", "🧪 Smart Formula", "🧹 Data Cleanup"])

    # ------------------------------------------------
    # 1. VISUAL ANALYSIS
    # ------------------------------------------------
    with tabs[0]:
        st.markdown("### Interactive Insights")
        
        # Controls
        with st.container():
            col_in, col_btn = st.columns([3, 1])
            sheet_in = col_in.text_input("Sheet Name", value=st.session_state.get("sheet_name", "Sales"), label_visibility="collapsed", placeholder="Sheet Name", key="viz_sheet")
            if col_btn.button("Analyze Data", use_container_width=True):
                with st.spinner("Analyzing structure..."):
                    try:
                        file_path = SAMPLE_DIR / st.session_state.file_path
                        df = load_excel(file_path, sheet_in)
                        chart_data = prepare_chart_data(df)
                        st.session_state.analyze_result = {
                            "success": True,
                            "chart_data": chart_data
                        }
                    except Exception as e:
                        st.session_state.analyze_result = {
                            "error": "Analysis failed",
                            "details": str(e)
                        }

        if st.session_state.analyze_result:
            res = st.session_state.analyze_result
            if "error" in res:
                st.error(f"Analysis Error: {res.get('details', res['error'])}")
            else:
                data = res.get("chart_data", {})
                profile = data.get("profile", {})
                
                # Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Rows", profile.get("row_count", 0))
                m2.metric("Columns", profile.get("column_count", 0))
                numeric_cols = profile.get("numeric_columns", [])
                categorical_cols = profile.get("categorical_columns", [])
                m3.metric("Numeric", len(numeric_cols))
                m4.metric("Categorical", len(categorical_cols))

                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                
                # Chart Controls
                cc1, cc2, cc3 = st.columns(3)
                chart_type = cc1.selectbox("Chart Style", ["Bar", "Line", "Area", "Scatter", "Pie", "Donut"])
                
                all_cols = profile.get("columns", [])
                
                # Logic: If Pie/Donut, Y is numeric size, X is label
                x_ax = cc2.selectbox("X Axis (Category)", all_cols, index=0 if all_cols else 0)
                y_ax = cc3.selectbox("Y Axis (Value)", numeric_cols, index=0 if numeric_cols else 0)
                
                # Render
                raw = data.get("data", [])
                df_vis = pd.DataFrame(raw)
                
                if df_vis.empty:
                    st.warning("No data rows available to plot.")
                elif HAS_PLOTLY:
                    fig = None
                    colors = px.colors.sequential.Plotly3
                    
                    if chart_type == "Bar":
                        fig = px.bar(df_vis, x=x_ax, y=y_ax, color=x_ax, template="plotly_dark", color_discrete_sequence=colors)
                    elif chart_type == "Line":
                        fig = px.line(df_vis, x=x_ax, y=y_ax, template="plotly_dark", markers=True)
                        fig.update_traces(line_color="#c4b5fd")
                    elif chart_type == "Area":
                        fig = px.area(df_vis, x=x_ax, y=y_ax, template="plotly_dark")
                        fig.update_traces(line_color="#ec4899")
                    elif chart_type == "Scatter":
                        fig = px.scatter(df_vis, x=x_ax, y=y_ax, color=x_ax, template="plotly_dark", size=y_ax)
                    elif chart_type == "Pie":
                        fig = px.pie(df_vis, names=x_ax, values=y_ax, template="plotly_dark", color_discrete_sequence=colors)
                    elif chart_type == "Donut":
                        fig = px.pie(df_vis, names=x_ax, values=y_ax, template="plotly_dark", hole=0.5, color_discrete_sequence=colors)
                    
                    if fig:
                        fig.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", 
                            plot_bgcolor="rgba(0,0,0,0)",
                            font_family="Outfit"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------------
    # 2. SMART PIVOT
    # ------------------------------------------------
    with tabs[1]:
        st.markdown("### Pivot Builder")
        
        c1, c2, c3 = st.columns([2, 5, 2])
        p_sheet = c1.text_input("Sheet", value="Sales", key="psheet")
        
        known = []
        if st.session_state.analyze_result:
             known = st.session_state.analyze_result.get("chart_data", {}).get("profile", {}).get("columns", [])
        
        if known:
            p_idx = c2.multiselect("Rows", known, placeholder="Select index columns")
            p_val = c2.multiselect("Values", known, placeholder="Select value columns")
        else:
            p_idx = c2.text_input("Rows (comma separated)", "Region").split(",")
            p_val = c2.text_input("Values (comma separated)", "Revenue").split(",")
            p_idx = [x.strip() for x in p_idx if x.strip()]
            p_val = [x.strip() for x in p_val if x.strip()]

        p_agg = c3.selectbox("Function", ["sum", "mean", "count", "min", "max"])
        
        if st.button("Generate Pivot", type="primary"):
            with st.spinner("Pivoting..."):
                try:
                    file_path = SAMPLE_DIR / st.session_state.file_path
                    df = load_excel(file_path, p_sheet)
                    pivot_df = create_pivot(df, index=p_idx, values=p_val, aggfunc=p_agg)
                    st.session_state.pivot_data = {
                        "success": True,
                        "full_data": pivot_df.to_dict(orient="records")
                    }
                except Exception as e:
                    st.session_state.pivot_data = {
                        "error": f"Pivot failed: {str(e)}"
                    }
        
        if st.session_state.pivot_data:
            res = st.session_state.pivot_data
            if "error" in res:
                st.error(res["error"])
            else:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                df_p = pd.DataFrame(res.get("full_data", []))
                st.dataframe(df_p, use_container_width=True)
                csv = df_p.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "pivot.csv", "text/csv")
                st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------------
    # 3. SMART FORMULA
    # ------------------------------------------------
    with tabs[2]:
        st.markdown("### AI Formula Generator")
        
        with st.container():
            c1, c2 = st.columns([1, 1])
            f_sheet = c1.text_input("Sheet", value="Sales", key="fsheet")
            f_cell = c2.text_input("Target Cell", value="E2")
            
            f_intent = st.text_area("What should happen in this cell?", height=100, placeholder="Example: Multiply Quantity by Unit Price")
            
            if st.button("Generate & Insert", type="primary", key="f_btn"):
                if not f_intent:
                    st.warning("Please enter instructions.")
                else:
                    with st.spinner("Thinking..."):
                        try:
                            file_path = SAMPLE_DIR / st.session_state.file_path
                            df = load_excel(file_path, f_sheet)
                            schema = list(df.columns)
                            formula = generate_formula_from_intent(f_intent, schema, f_cell)
                            if formula:
                                insert_formula_to_excel(file_path, f_sheet, f_cell, formula)
                                res = {
                                    "success": True,
                                    "metadata": {"formula": formula, "calculated_value": None}
                                }
                            else:
                                res = {"error": "Could not generate formula"}
                        except Exception as e:
                            res = {"error": f"Formula generation failed: {str(e)}"}
                    
                    if "error" in res:
                        st.error(f"Failed: {res.get('details', res['error'])}")
                    else:
                        meta = res.get("metadata", {})
                        formula = meta.get("formula", "???")
                        # Also check if we got a calculated answer
                        calculated_value = meta.get("calculated_value", None)
                        
                        st.markdown(
                            f"""
                            <div class='glass-card' style='border-left: 5px solid #10b981;'>
                                <h3 style='color: #10b981; margin: 0;'>Formula Generated</h3>
                                <code style='font-size: 1.5rem; display: block; margin: 1rem 0;'>{formula}</code>
                                <p>Inserted into <strong>{f_cell}</strong></p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        # Show calculated result if available
                        if calculated_value:
                             st.markdown(
                                f"""
                                <div class='glass-card' style='border-left: 5px solid #ec4899; margin-top: 1rem;'>
                                    <h3 style='color: #ec4899; margin: 0;'>Projected Answer</h3>
                                    <p style='font-size: 1.2rem; color: white;'>The result of this formula would be: <strong>{calculated_value}</strong></p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        target = SAMPLE_DIR / st.session_state.file_path
                        if target.exists():
                             with target.open("rb") as f:
                                st.download_button("Download Updated File", f.read(), f"updated_{st.session_state.file_path}")

    # ------------------------------------------------
    # 4. CLEANUP
    # ------------------------------------------------
    with tabs[3]:
        st.markdown("### Intelligent Cleanup")
        c_sheet = st.text_input("Sheet to Clean", value="Sales", key="csheet")
        
        if st.button("Clean Data", type="primary"):
            with st.spinner("Scrubbing..."):
                try:
                    file_path = SAMPLE_DIR / st.session_state.file_path
                    df = load_excel(file_path, c_sheet)
                    cleaned_df, summary = clean_sheet(df)
                    save_excel(cleaned_df, file_path, c_sheet)
                    st.session_state.clean_summary = {
                        "success": True,
                        "cleaning_summary": summary
                    }
                except Exception as e:
                    st.session_state.clean_summary = {
                        "error": f"Cleaning failed: {str(e)}"
                    }
        
        if st.session_state.clean_summary:
            res = st.session_state.clean_summary
            if "error" in res:
                st.error(res["error"])
            else:
                summ = res.get("cleaning_summary", {})
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.success("Cleanup Successful")
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Rows Removed", summ.get("rows_removed", 0))
                sc2.metric("Final Rows", summ.get("final_rows", 0))
                
                target = SAMPLE_DIR / st.session_state.file_path
                if target.exists():
                     with target.open("rb") as f:
                        st.download_button("Download Cleaned File", f.read(), f"cleaned_{st.session_state.file_path}")
                st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
