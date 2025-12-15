
=======
## LLM-Driven Excel Automation MCP Server

Production-style personal project that exposes Excel automation capabilities to LLMs via an MCP (Model Context Protocol) server and a FastAPI HTTP API. The system lets an LLM safely load, clean, profile, and transform Excel workbooks – locally and when deployed on Render’s free tier.

---

### 1. Problem Statement

Most “LLM + spreadsheets” demos rely on brittle CSV parsing or ad‑hoc scripts. There is rarely:

- **A deterministic, auditable tool layer** between the LLM and Excel.
- **Clear server boundaries** suitable for deployment on platforms like Render.
- **A portfolio-ready backend** that recruiters can quickly understand and run.

This project solves that by providing a **typed, well-structured Excel MCP server** that an LLM can call via tools, while also exposing the same operations over **FastAPI endpoints**.

---

### 2. High-Level Architecture

**Text diagram:**

- **User**
  - talks to →
- **Local LLM (Ollama – LLaMA 3 / Phi-3)**
  - decides which MCP tools to call →
- **MCP Server (Python MCP SDK)**
  - delegates work to →
- **Excel Operations Layer (pandas + openpyxl)**
  - reads/writes →
- **Excel Files (under `sample_files/`)**
  - responses returned to →
- **LLM / User**

In parallel, the same operations are exposed as **HTTP endpoints** using **FastAPI**, so you can test with **Postman / curl** and deploy to **Render**.

---

### 3. Features

- **Excel loading and cleaning**
  - Load specific sheets from `.xlsx` files.
  - Remove empty rows, normalize column names, and infer data types.
- **Data profiling**
  - Row / column counts.
  - Column list.
  - Per-column null counts.
- **Pivot table creation**
  - Flexible `index`, `values`, and `aggfunc` (`sum`, `mean`, `count`).
  - Returns pivoted data as JSON for the LLM to consume.
- **Formula insertion**
  - Insert arbitrary Excel formulas into specific cells using `openpyxl`.
- **MCP tools for LLMs**
  - `clean_excel`
  - `profile_excel`
  - `create_pivot_table`
  - `insert_excel_formula`
- **FastAPI HTTP endpoints**
  - `/health`
  - `/mcp/clean-excel`
  - `/mcp/profile-excel`
  - `/mcp/create-pivot-table`
  - `/mcp/insert-formula`
- **Local LLM demo client**
  - Minimal helper that calls **Ollama** and guides the model to emit JSON tool calls.
- **Dockerized and Render-ready**
  - `python:3.10-slim` base.
  - Exposes port `10000`.

---

### 4. Tech Stack

- **Language**: Python 3.10+
- **API Framework**: FastAPI
- **Excel Operations**: pandas, openpyxl
- **MCP Server**: `mcp` (Python MCP SDK)
- **Local LLM**: Ollama (LLaMA 3 / Phi-3)
- **Optional Cloud LLM**: Groq (free tier only, not hardcoded)
- **Deployment**: Docker on Render free tier
- **Demo Clients**: HTTP (Postman / curl), local LLM demo helper

---

### 5. Repository Structure

```text
llm-excel-mcp-server/

├── app/
│   ├── main.py          # FastAPI app entry point
│   ├── mcp_server.py    # MCP tool definitions
│   ├── excel_ops.py     # Excel operation logic
│   ├── schemas.py       # Pydantic request/response models
│   ├── config.py        # App configuration
│   ├── utils.py         # Helper utilities
│   └── llm_client.py    # Local LLM helper for demos (Ollama)
│
├── sample_files/
│   ├── .gitkeep
│   └── sales_data.xlsx  # (created locally by you – not committed)
│
├── tests/
│   └── __init__.py
│
├── Dockerfile
├── requirements.txt
├── README.md
└── .gitignore
```

---

### 6. Local Setup

#### 6.1 Prerequisites

- Python **3.10+**
- `pip`
- (Optional for LLM flow) **Ollama** installed locally:
  - Install from `https://ollama.com`
  - Then run:

```bash
ollama pull llama3
```

#### 6.2 Create and activate virtualenv

```bash
cd llm-excel-mcp-server
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# or
.venv\Scripts\activate           # Windows
```

#### 6.3 Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 6.4 Create a sample Excel file

In `sample_files/`, create a workbook named `sales_data.xlsx` with a sheet `Sales` containing columns like:

- `Region`
- `Product`
- `Revenue`
- `Quantity`

Example minimal data:

| Region | Product | Revenue | Quantity |
|--------|---------|---------|----------|
| East   | A       | 1000    | 10       |
| East   | B       | 500     | 5        |
| West   | A       | 700     | 7        |

Save it as `sample_files/sales_data.xlsx`.

---

### 7. Running the Server Locally

Start the FastAPI app with uvicorn:

```bash
uvicorn app.main:app --reload
```

By default the app serves on `http://127.0.0.1:8000`. The Render deployment will listen on port `10000` inside the container.

- **Health check**: `GET /health`
- **OpenAPI docs**: `GET /docs`

---

### 8. HTTP Endpoints & Example Calls

All examples assume the server is running locally on `http://127.0.0.1:8000`.

- **Clean Excel**

```bash
curl -X POST http://127.0.0.1:8000/mcp/clean-excel \
  -H "Content-Type: application/json" \
  -d '{
    "path": "sales_data.xlsx",
    "sheet": "Sales"
  }'
```

- **Profile Excel**

```bash
curl -X POST http://127.0.0.1:8000/mcp/profile-excel \
  -H "Content-Type: application/json" \
  -d '{
    "path": "sales_data.xlsx",
    "sheet": "Sales"
  }'
```

- **Create Pivot Table**

```bash
curl -X POST http://127.0.0.1:8000/mcp/create-pivot-table \
  -H "Content-Type: application/json" \
  -d '{
    "path": "sales_data.xlsx",
    "sheet": "Sales",
    "index": ["Region"],
    "values": ["Revenue"],
    "aggfunc": "sum"
  }'
```

- **Insert Formula**

```bash
curl -X POST http://127.0.0.1:8000/mcp/insert-formula \
  -H "Content-Type: application/json" \
  -d '{
    "path": "sales_data.xlsx",
    "sheet": "Sales",
    "cell": "E2",
    "formula": "=C2*D2"
  }'
```

> Note: the backend restricts file access to the `sample_files/` directory for safety. When calling the API, use paths relative to that directory (e.g. `"sales_data.xlsx"`).

---

### 9. MCP Tools (For LLMs)

The project defines MCP tools in `app/mcp_server.py`:

- **`clean_excel(path: str, sheet: str)`**
- **`profile_excel(path: str, sheet: str)`**
- **`create_pivot_table(path: str, sheet: str, index: list, values: list, aggfunc: str = "sum")`**
- **`insert_excel_formula(path: str, sheet: str, cell: str, formula: str)`**

An LLM (via MCP-aware client) would emit tool calls like:

```json
{
  "tool": "create_pivot_table",
  "arguments": {
    "path": "sample_files/sales_data.xlsx",
    "sheet": "Sales",
    "index": ["Region"],
    "values": ["Revenue"]
  }
}
```

The tool layer handles:

- Input validation (file exists, sheet exists, columns exist).
- Exceptions converted to friendly error messages.
- JSON-serializable responses with small previews.

---

### 10. End-to-End Example Scenario

User prompt to the LLM:

> "Clean the sales Excel file and generate a pivot table showing total revenue by region."

LLM behavior:

- Chooses to first call `clean_excel`:
  - `{"tool": "clean_excel", "arguments": {"path": "sample_files/sales_data.xlsx", "sheet": "Sales"}}`
- Then calls `create_pivot_table`:
  - `{"tool": "create_pivot_table", "arguments": {"path": "sample_files/sales_data.xlsx", "sheet": "Sales", "index": ["Region"], "values": ["Revenue"]}}`

The server:

- Cleans the sheet and saves the cleaned version.
- Returns a JSON preview of the pivot table (total revenue per region).

---

### 11. Local LLM Demo (Ollama)

This repo includes a minimal helper (`app/llm_client.py`) for local experiments.

1. Make sure Ollama is running and the model is pulled:

```bash
ollama pull llama3
ollama serve
```

2. Use the helper in a Python shell (example sketch):

```python
from app.llm_client import build_tool_prompt, call_ollama

tools = [
    {
        "name": "create_pivot_table",
        "description": "Create pivot tables over Excel data",
        "schema": {
            "path": "str",
            "sheet": "str",
            "index": "list[str]",
            "values": "list[str]",
            "aggfunc": "str"
        }
    }
]

prompt = build_tool_prompt(
    "Clean the sales Excel file and generate a pivot of total revenue by region.",
    tools,
)

import asyncio
asyncio.run(call_ollama(prompt))
```

The LLM should respond with a JSON object describing which tool to call and with what arguments, which you can then forward to the corresponding HTTP endpoint or MCP tool.

---

### 12. Deployment on Render (Docker, Free Tier)

This project is designed to deploy on **Render** using the provided `Dockerfile`.

#### 12.1 Steps

- Push this repository to GitHub.
- In Render:
  - Create a **New Web Service**.
  - Connect your GitHub repo.
  - **Runtime**: Docker.
  - **Plan**: Free.
  - Render will detect the `Dockerfile` and build the image.
  - Ensure the **port** is set to `10000` (Render uses `PORT` env; uvicorn is configured accordingly).

Once deployed:

- Health check: `GET https://<your-service>.onrender.com/health`
- Docs: `GET https://<your-service>.onrender.com/docs`

#### 12.2 Cold-start behavior

On the free tier, Render may **spin down** your service after inactivity:

- First request after idle can take **10–60 seconds** while the container cold-starts.
- Subsequent requests are fast again until it idles out later.

---

### 13. Limitations

- **No LLM inference on Render**: By design, all LLM calls (Ollama) are **local-only**.
- **Ephemeral filesystem** on Render:
  - Excel files written in the container may be lost on redeploys.
  - For real production, you would attach durable storage or S3-like buckets.
- **Security**:
  - File operations are restricted to the `sample_files/` directory, but this is still a **demo**, not a hardened multi-tenant system.
- **LLM client**:
  - The included `llm_client.py` is intentionally minimal and not a full orchestration layer.

---

### 14. Resume-Ready Description

> Built a production-style **LLM-driven Excel Automation MCP Server** in Python, exposing deterministic Excel tools (cleaning, profiling, pivot tables, formula insertion) to LLMs via **Model Context Protocol** and **FastAPI**. Implemented typed, modular Excel operations using **pandas** and **openpyxl**, with robust validation and error handling. Containerized the service with Docker and deployed to **Render’s free tier**, documenting cold-start behavior and local **Ollama** integration for tool selection. Designed the codebase and README to be recruiter-friendly, with clear boundaries between API layer, tool layer, Excel logic, and LLM integration.

---

### 15. How to Use This Project in Interviews

- Point recruiters to:
  - The **clean repo structure** and type-annotated Python code.
  - The **Excel operations and error handling** in `app/excel_ops.py`.
  - The **MCP tool definitions** in `app/mcp_server.py`.
  - The **FastAPI integration** in `app/main.py`.
  - This **README** for architecture and deployment details.
- Talk through:
  - How the LLM chooses tools and how you guarantee deterministic behavior.
  - How you would extend this to external storage (S3), authentication, or more complex Excel workflows.


>>>>>>> 79937ee (Initial MCP Excel automation server with UI)
