# Guarded Multi-Agent Financial Trading Orchestrator

## Team Setup

This is a Multi-Agent Failure Modes &
Guardrails assignment. Each student owns one guardrail layer, and all six
layers are integrated into one shared orchestrator.

## Domain Introduction

The project uses financial trading as its high-stakes domain. A coordinator
routes work between an analyst, simulated trade actor, risk validator, and
reporter. Market data is real and live when the market-data API is available,
but all trades are simulated and the system never places real orders.

## Chosen Language Stack

- Python 3.12
- LangGraph and LangChain Core
- Pydantic
- LangSmith
- Google Gemini
- Streamlit
- Pytest

## Setup

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add the respective API keys to `.env`, then run either interface:

```powershell
# CLI
python main_system.py

# Local Dashboard
streamlit run dashboard/streamlit_app.py
```

Run the tests with:

```powershell
python -m pytest -q -s
```

## Repository Layout

```text
├── .streamlit/              # Streamlit theme and configuration
├── dashboard/
│   └── streamlit_app.py     # Streamlit dashboard
├── orchestrator/            # Shared data, tools, and guardrail helpers
├── chidimma_loop/           # Student 1: loop guardrail
├── Yifan_silent/            # Student 2: schema guardrail
├── chikezie_rogue/          # Student 3: tool guardrail
├── subhan_cascade/          # Student 4: cascade guardrail
├── priyanka_trace/          # Student 5: privacy guardrail
├── priyanka_token/          # Student 6: context guardrail
├── diagram/                 # Architecture diagram (PNG)
├── main_system.py           # CLI and integrated graph
├── contract.py              # Shared frozen state contract
├── DESIGN_DOCS.md           # System architecture and design decisions
├── README.md                # Project introduction and setup
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
├── .env.example             # API-key environment template
└── .gitignore               # Files excluded from Git
```
## Individual Failure Demo Videos
- **Student 2 (Yifan) — Silent Hallucination Guardrail:** [Watch Demo](./Yifan_silent/student2_silent_demo.mp4)
- 
