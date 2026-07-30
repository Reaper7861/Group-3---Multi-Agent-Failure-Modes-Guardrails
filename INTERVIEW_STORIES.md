# Interview Stories

## Student 1 — Infinite Loop Prevention



## Student 2 — Structural Output Validation



## Student 3 — Rogue Tool Containment



## Subhan — Cascade Failure Prevention

**Situation:** The Trade Actor (Worker B) might pass bad data to the Risk Validator (Worker C), such as the quantity being written as `"TEN THOUSAND"` instead of an integer, while the price could be `None`. If the Risk Validator (Worker C) tries to multiply these values, the program crashes.

**Task:** Stop malformed data before the Risk Validator’s (Worker C) arithmetic and preserve graph health.

**Action:** I added strict boundary validation for positive price and bounded integer quantity. Additionally, I placed a Cascade Guard between the Trade Actor and the Risk Validator. Before the Risk Validator (Worker C) performs any calculations, the guard checks that the trade is simulated, the symbol and action match, the quantity is an integer, and the price is a valid number. It also confirms that a HOLD request does not contain unnecessary trade arguments. Invalid data produced has its reasons recorded and sets both `rejection_flag` and `rollback_required`, and safely routes the workflow to the error handler instead of being consumed. The failure test captures the vulnerable `TypeError`; an integration test confirms the same payload is rejected before portfolio calculations.

**Result:** Downstream crashes decreased from one to zero, the malformed payload produced two validation errors, and crash prevention was 100%. By validating the structure first and handling financial risk separately, the system is easier to understand, test, and maintain. More importantly, a failure in one agent stays contained instead of spreading through the entire workflow.

**Technologies:** Python, Pydantic v2, LangGraph boundary nodes, shared-state validation, and pytest.


## Student 5 — Privacy-Safe Telemetry



## Student 6 — Context Budget Management


