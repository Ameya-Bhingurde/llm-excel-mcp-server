import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st


API_BASE_URL = "http://localhost:8000"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_files"


def call_api(
    path: str,
    sheet: str,
    operation: str,
    index: Optional[List[str]] = None,
    values: Optional[List[str]] = None,
    aggfunc: str = "sum",
    cell: Optional[str] = None,
    formula: Optional[str] = None,
) -> Dict[str, Any]:
    """Invoke the FastAPI backend for the given operation."""

    endpoint_map = {
        "Profile Excel": "/mcp/profile-excel",
        "Clean Excel": "/mcp/clean-excel",
        "Create Pivot Table": "/mcp/create-pivot-table",
        "Insert Formula": "/mcp/insert-formula",
    }
    url = API_BASE_URL + endpoint_map[operation]

    payload: Dict[str, Any] = {"path": path, "sheet": sheet}

    if operation == "Create Pivot Table":
        payload["index"] = index or []
        payload["values"] = values or []
        payload["aggfunc"] = aggfunc or "sum"
    elif operation == "Insert Formula":
        payload["cell"] = cell
        payload["formula"] = formula

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
    except httpx.RequestError as exc:
        return {
            "error": "Connection error",
            "details": str(exc),
            "hint": f"Is the FastAPI server running at {API_BASE_URL}?",
        }

    if resp.headers.get("content-type", "").startswith("application/json"):
        data = resp.json()
    else:
        data = {"raw": resp.text}

    if not resp.is_success:
        return {
            "error": f"HTTP {resp.status_code}",
            "details": data,
        }

    return data


def save_uploaded_file(uploaded_file) -> str:
    """
    Save the uploaded Excel file into the sample_files directory.

    Returns the relative path used by the backend APIs.
    """

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    target = SAMPLE_DIR / uploaded_file.name
    with target.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    # Backend expects paths relative to sample_files/
    return uploaded_file.name


def main() -> None:
    st.set_page_config(
        page_title="LLM-Driven Excel Automation",
        page_icon="📊",
        layout="wide",
    )

    # Initialize session state
    if "selected_operation" not in st.session_state:
        st.session_state.selected_operation = None

    # ========================================================================
    # CSS STYLING - Railway-inspired dark theme with ambient background
    # ========================================================================
    st.markdown(
        """
        <style>
        /* Railway-style dark background with subtle gradient and dot grid */
        .stApp {
            background: 
                radial-gradient(circle at 20% 30%, rgba(67, 56, 202, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
                linear-gradient(180deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%);
            background-attachment: fixed;
            color: #e5e7eb;
        }
        
        /* Subtle dot grid overlay */
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image: 
                radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.15) 1px, transparent 0);
            background-size: 40px 40px;
            pointer-events: none;
            opacity: 0.4;
            z-index: 0;
        }
        
        /* Soft glow effect behind main content */
        .main-content-wrapper {
            position: relative;
            z-index: 1;
        }
        
        /* Header styling */
        h1 {
            color: #ffffff;
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        /* Subtitle styling */
        .subtitle {
            color: #9ca3af;
            font-size: 0.95rem;
            font-weight: 400;
        }
        
        /* Section heading */
        h3 {
            color: #f3f4f6;
            font-weight: 500;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        
        /* Card-style action buttons */
        .stButton > button {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(30, 41, 59, 0.8) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            cursor: pointer;
            transition: all 0.2s ease;
            height: auto !important;
            min-height: 160px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            text-align: left !important;
            white-space: normal !important;
            line-height: 1.6 !important;
            font-size: 1rem !important;
            color: #e5e7eb !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            justify-content: flex-start !important;
        }
        
        .stButton > button:hover {
            border-color: rgba(99, 102, 241, 0.6) !important;
            background: rgba(15, 23, 42, 0.8) !important;
            box-shadow: 0 8px 16px rgba(99, 102, 241, 0.2) !important;
            transform: translateY(-2px);
        }
        
        .stButton > button[type="primary"] {
            border-color: #6366f1 !important;
            background: rgba(30, 41, 59, 0.9) !important;
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4) !important;
        }
        
        .stButton > button[type="secondary"] {
            background: rgba(15, 23, 42, 0.6) !important;
            color: #e5e7eb !important;
        }
        
        /* Style bold text in buttons */
        .stButton > button strong {
            color: #ffffff !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            display: block;
            margin: 0.5rem 0;
        }
        
        /* Form inputs styling */
        .stTextInput > div > div > input {
            background-color: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(30, 41, 59, 0.8);
            color: #e5e7eb;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        /* File uploader styling */
        .stFileUploader > div {
            background-color: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(30, 41, 59, 0.8);
            border-radius: 8px;
        }
        
        /* Primary button styling */
        .stButton > button[type="primary"] {
            background: #6366f1;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton > button[type="primary"]:hover {
            background: #4f46e5;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }
        
        /* Code block styling */
        .stCodeBlock {
            background-color: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(30, 41, 59, 0.8);
        }
        
        /* Success/Error messages */
        .stSuccess {
            background-color: rgba(16, 185, 129, 0.1);
            border-left: 4px solid #10b981;
        }
        
        .stError {
            background-color: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================================
    # HEADER SECTION
    # ========================================================================
    st.markdown(
        """
        <div class="main-content-wrapper" style="text-align: center; margin-top: 3rem; margin-bottom: 3rem;">
            <h1 style="margin-bottom: 0.5rem;">LLM-Driven Excel Automation</h1>
            <p class="subtitle">Safely automate Excel workflows using deterministic tools</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================================
    # FILE UPLOAD SECTION
    # ========================================================================
    uploaded_file = st.file_uploader(
        "Upload an Excel file (.xlsx)",
        type=["xlsx"],
        help="File will be stored temporarily under the server's sample_files/ directory.",
    )

    # ========================================================================
    # ACTION SELECTION SECTION - Card-style buttons in 2x2 grid
    # ========================================================================
    st.markdown("### Choose an action")

    # Define action cards with icon, title, and description
    actions = [
        {
            "key": "Clean Excel",
            "icon": "🧹",
            "title": "Clean Excel",
            "description": "Remove empty rows and normalise column names and data types.",
        },
        {
            "key": "Create Pivot Table",
            "icon": "📊",
            "title": "Create Pivot Table",
            "description": "Aggregate data by index and value columns into a pivot table.",
        },
        {
            "key": "Profile Excel",
            "icon": "📋",
            "title": "Profile Excel",
            "description": "Summarise rows, columns, and missing values.",
        },
        {
            "key": "Insert Formula",
            "icon": "✏️",
            "title": "Insert Formula",
            "description": "Write an Excel formula into a specific cell.",
        },
    ]

    # Create 2x2 grid layout
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        for action in actions[:2]:
            is_selected = st.session_state.selected_operation == action["key"]
            
            # Multi-line button label with icon, title, and description
            button_label = f"{action['icon']}\n\n**{action['title']}**\n\n{action['description']}"
            
            if st.button(
                button_label,
                key=f"btn_{action['key'].replace(' ', '_')}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state.selected_operation = action["key"]
                st.rerun()

    with col2:
        for action in actions[2:]:
            is_selected = st.session_state.selected_operation == action["key"]
            
            # Multi-line button label with icon, title, and description
            button_label = f"{action['icon']}\n\n**{action['title']}**\n\n{action['description']}"
            
            if st.button(
                button_label,
                key=f"btn_{action['key'].replace(' ', '_')}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state.selected_operation = action["key"]
                st.rerun()

    # ========================================================================
    # DYNAMIC FORM SECTION - Based on selected operation
    # ========================================================================
    operation = st.session_state.selected_operation

    if operation:
        st.markdown(f"**Selected:** {operation}")
        st.markdown("---")

        sheet_name = st.text_input("Sheet name", value="Sales")

        index_cols: List[str] = []
        value_cols: List[str] = []
        aggfunc = "sum"
        cell = ""
        formula = ""

        if operation == "Create Pivot Table":
            st.markdown("**Pivot configuration**")
            index_raw = st.text_input("Index columns (comma-separated)", value="Region")
            values_raw = st.text_input("Value columns (comma-separated)", value="Revenue")
            aggfunc = st.text_input("Aggregation function", value="sum")
            index_cols = [c.strip() for c in index_raw.split(",") if c.strip()]
            value_cols = [c.strip() for c in values_raw.split(",") if c.strip()]
        elif operation == "Insert Formula":
            st.markdown("**Formula configuration**")
            cell = st.text_input("Cell (e.g. E2)", value="E2")
            formula = st.text_input("Formula (e.g. =C2*D2)", value="=C2*D2")

        run_clicked = st.button("Run Selected Operation", type="primary", use_container_width=True)

        # ========================================================================
        # RESULTS SECTION
        # ========================================================================
        st.markdown("### Result")
        result_placeholder = st.empty()

        if run_clicked:
            if uploaded_file is None:
                result_placeholder.error("Please upload an Excel (.xlsx) file first.")
            else:
                rel_path = save_uploaded_file(uploaded_file)

                with st.spinner("Running operation against backend..."):
                    data = call_api(
                        path=rel_path,
                        sheet=sheet_name,
                        operation=operation,
                        index=index_cols,
                        values=value_cols,
                        aggfunc=aggfunc,
                        cell=cell or None,
                        formula=formula or None,
                    )

                if "error" in data:
                    result_placeholder.error(data.get("error", "Unknown error"))
                    st.code(json.dumps(data, indent=2), language="json")
                else:
                    result_placeholder.success("Operation completed successfully.")
                    st.code(json.dumps(data, indent=2), language="json")

                    # For operations that modify the workbook, offer a download link
                    if operation in {"Clean Excel", "Insert Formula"}:
                        target = SAMPLE_DIR / rel_path
                        if target.exists():
                            with target.open("rb") as f:
                                st.download_button(
                                    label="Download updated Excel file",
                                    data=f.read(),
                                    file_name=uploaded_file.name,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                )
    else:
        st.info("👆 Select an action above to get started.")


if __name__ == "__main__":
    main()
