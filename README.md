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

## LangSmith Trace

View an example end-to-end LangGraph execution (shown in technical demo video):

[Open the shared LangSmith trace](https://smith.langchain.com/public/bd263ee1-679e-4bf6-8a39-91f091457019/r/019fc0e0-4626-7c11-836c-34927dd6ec4f?start_time=2026-08-02T05%3A09%3A11.333787Z)

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
├── demo/                    # 5-minute technical demo video (MP4)
├── main_system.py           # CLI and integrated graph
├── contract.py              # Shared frozen state contract
├── DESIGN_DOCS.md           # System architecture and design decisions
├── README.md                # Project introduction and setup
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
├── .env.example             # API-key environment template
└── .gitignore               # Files excluded from Git

```

## 5-Minute Technical Demo Video
[Watch Demo](./demo/Group%203_Multi-Agent_Demo.mp4)

## Individual Failure Demo Videos
- **Student 1 (Chidimma) - Infinite Graph Loops:** [Watch Demo](./chidimma_loop/chidimma_loop_demo.mp4)
- **Student 2 (Yifan) — Silent Hallucinations & Structural Failures:** [Watch Demo](./Yifan_silent/yifan_silent_demo.mp4)
- **Student 3 (Chikezie) - Rogue Tool Execution:** [Watch Demo](./chikezie_rogue/Project.mp4)
- **Student 4 (Subhan) - Downstream Cascade Failure:** [Watch Demo](./subhan_cascade/subhan_cascade_demo.mp4)
- **Student 5 (Priyanka) - Data Privacy Leak via Telemetry:** [Watch Demo](priyanka_trace/priyanka_trace_demo.mp4)
- **Student 6 (Priyanka) - Context Window Explosion & Token Burn:** [Watch Demo](priyanka_token/priyanka_token_demo.mp4)
