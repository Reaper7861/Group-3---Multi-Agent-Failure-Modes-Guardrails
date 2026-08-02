# Interview Stories

## Student 1 — Infinite Loop Prevention



## Yifan — Structural Output Validation

**Situation:** In our Financial Trading Bot orchestrator, the Analyzer converts raw market text into structured trade instructions. A hallucinated but plausible-looking output — a missing ticker symbol or an impossible confidence score — could silently flow into Trade Execution and Risk Checks.. 

**Task:** Reject missing fields and invalid values deterministically, while allowing exactly one automated self-correction attempt. 

**Action:** I defined a Pydantic AnalysisPayload schema enforcing a literal action, non-empty symbol and rationale, a non-negative integer quantity, and bounded (0–1) confidence and risk scores. I placed a Schema Guard node after the Analyzer. On the first validation failure, the wrapper logs sanitized exception feedback, increments a shared retry counter, and routes back to the Analyzer; a second failure routes safely to the error handler. Tests inject missing structure, an empty symbol, a negative quantity, confidence 1.7, empty rationale, and risk 2.0.

**Result:** Invalid acceptance dropped from 2/2 to 0/2 — blocking 100% of unsafe downstream trades. An integration test confirms exactly two Analyzer calls and one retry.

**Technologies:** Pydantic v2, Gemini structured output, LangGraph, Python, pytest. This converts probabilistic text into a dependable interface without permitting retry storms.



## Chikezie — Rogue Tool Containment

**Situation:** In our multi-agent Financial Trading Bot, the Trade Actor receives model-generated tool requests. A compromised or hallucinating agent could request a non-approved tool such as `place_live_order`, submit an excessive quantity, or add unexpected arguments. If the orchestrator trusted that request, probabilistic model output could cross the boundary into an unauthorized financial action.

**Task:** I was responsible for ensuring that an agent could invoke only approved, side-effect-free simulation tools and that every request failed closed unless its name and arguments satisfied deterministic trading limits.

**Action:** I built a middleware guard in `chikezie_rogue/snippet.py` around an explicit registry of mock buy, sell, and hold tools. Before dispatch, it verifies the tool name, requires the exact `symbol`, `quantity`, and `price` argument set, rejects unsupported symbols and incorrect Python types, caps quantity at 100, enforces a $10,000 maximum trade notional, and requires HOLD requests to use a zero quantity. Rejected calls return concrete reasons without invoking a tool. I also created deterministic tests that compare a vulnerable executor with the guarded path, inject a rogue `place_live_order` request for 1,000 shares, confirm malformed arguments are rejected, and verify that a valid approved request still produces a simulated result.

**Result:** The vulnerable baseline accepted one unauthorized execution, while the guarded implementation accepted zero, giving us a 100% prevention rate in the failure demonstration. The guard also preserved legitimate behavior by successfully executing an approved mock purchase. This moved tool authorization out of model judgment and into a small, auditable policy boundary, ensuring that even adversarial agent output cannot trigger a live trade.

**Technologies:** Python, LangGraph tool middleware, deterministic allowlists, shared-state contracts, and pytest.



## Subhan — Cascade Failure Prevention

**Situation:** The Trade Actor (Worker B) might pass bad data to the Risk Validator (Worker C), such as the quantity being written as `"TEN THOUSAND"` instead of an integer, while the price could be `None`. If the Risk Validator (Worker C) tries to multiply these values, the program crashes.

**Task:** Stop malformed data before the Risk Validator’s (Worker C) arithmetic and preserve graph health.

**Action:** I added strict boundary validation for positive price and bounded integer quantity. Additionally, I placed a Cascade Guard between the Trade Actor and the Risk Validator. Before the Risk Validator (Worker C) performs any calculations, the guard checks that the trade is simulated, the symbol and action match, the quantity is an integer, and the price is a valid number. It also confirms that a HOLD request does not contain unnecessary trade arguments. Invalid data produced has its reasons recorded and sets both `rejection_flag` and `rollback_required`, and safely routes the workflow to the error handler instead of being consumed. The failure test captures the vulnerable `TypeError`; an integration test confirms the same payload is rejected before portfolio calculations.

**Result:** Downstream crashes decreased from one to zero, the malformed payload produced two validation errors, and crash prevention was 100%. By validating the structure first and handling financial risk separately, the system is easier to understand, test, and maintain. More importantly, a failure in one agent stays contained instead of spreading through the entire workflow.

**Technologies:** Python, Pydantic v2, LangGraph boundary nodes, shared-state validation, and pytest.


## Priyanka-Privacy-Safe Telemetry

I co-developed a multi-agent Financial Trading Bot platform using LangGraph. My core responsibility was engineering the privacy-safe telemetry layer. While LangSmith tracing was vital for observing graph state, our raw payloads contained highly sensitive data, including brokerage API keys, client account numbers, and proprietary risk-model parameters. To ensure tracing remained useful without violating strict financial data compliance, I built a centralized recursive redaction interceptor in Python. This middleware executed right before graph invocation and inside every Worker node wrapper, utilizing regex and key-matching to sanitize both input and output states before they reached external observability dashboards. During rigorous stress testing with malicious Worker injections attempting to output account details, the customized guardrail intercepted and scrubbed 100 percent of sensitive payloads. By enforcing this robust state redaction programmatically, we achieved zero data leaks across all complex routing loops while maintaining complete system observability for our necessary, strict, and routine trade audits. 

## Priyanka- Context Budget Management

In our multi-agent Financial Trading Bot built on LangGraph, I owned the context budget management layer. Because our system utilized dynamic Coordinator routing, high-frequency tasks like streaming market analysis caused the state history to bloat rapidly, driving up token costs and API latency. I engineered a Context Management Node that intercepted the graph state prior to every routing transition. This guardrail calculated token usage and, when we breached our 2,000-token limit, programmatically pruned intermediate market data outputs while summarizing older role-based messages. I also implemented a fallback estimator so the guardrail succeeds even when a provider tokenizer is unavailable. During our baseline stress tests, execution history regularly bloated to 120 messages. With the guardrail active, I reduced the context window to 13 high-signal messages. This dropped our estimated token consumption from 17,281 to 1,765 for an 89.8 percent reduction, ensuring cost-efficient trade execution without deadlocking the graph. 

