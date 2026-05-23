---
inclusion: always
---
# Project Structure
audit-agent/
  backend/
    main.py                      # FastAPI, CORS, /audit /query endpoints
    agent_app.py                 # BedrockAgentCoreApp entrypoint for deployment
    agent/
      audit_agent.py             # Strands Agent wiring all 3 tools
      tools/
        contract_extractor.py    # @tool — extract contract terms via Bedrock
        invoice_extractor.py     # @tool — extract invoice line items via Bedrock
        drift_scorer.py          # @tool — compute risk score + findings
    parsers/
      pdf_parser.py              # pdfplumber bytes → text
    storage/
      s3_manager.py              # S3 upload/download/save
    db/
      models.py                  # SQLAlchemy AuditResult model
      crud.py                    # save_audit, get_all_audits
  frontend/
    src/
      App.jsx
      AuditDashboard.jsx         # Complete UI — already built
```

---

## 🟣 PHASE 2 — Create the Spec

**Step 9** — In Kiro's left sidebar, click **"Specs"** → **"New Spec"** → name it `invoice-audit-agent`.

**Step 10** — In Kiro chat panel, switch to **Spec mode** (dropdown at top of chat). Paste this exactly:
```
Build an AI vendor invoice audit agent.

WHEN a user uploads a contract PDF and invoice PDF
THEN the system shall:
  - Extract structured billing terms from the contract using Claude on Bedrock
  - Extract all line items and charges from the invoice using Claude on Bedrock
  - Compare them to detect:
      * Price mismatches (billed rate vs contracted rate)
      * Volume overages (quantity exceeds contracted cap)
      * Prohibited charges (banned in contract Section 6)
      * Unapproved amendment references (no signed amendment exists)
  - Compute a risk score from 0-100
  - Return risk level: HIGH (>=50), MEDIUM (>=20), LOW (<20)
  - List each finding with the exact contract clause it violates
  - Store PDFs in S3 bucket: axiom-audit-documents
  - Save audit result JSON to S3 audit-results folder
  - Store result summary in SQLite via SQLAlchemy

WHEN a user types a natural language query
THEN the Strands agent shall query the SQLite database and answer

The FastAPI backend exposes:
  POST /audit   — accepts contract + invoice PDF files
  POST /query   — accepts { "query": "string" }
  GET  /audits  — returns all past audit results

The React frontend has:
  - Drag-and-drop PDF upload for contract and invoice
  - Animated risk score ring (0-100)
  - Expandable finding cards with contract clause references
  - AI chat panel for natural language queries
  - Demo mode toggle (works without backend)
```

**Step 11** — Kiro generates 3 files. **Review and approve each one:**
- `requirements.md` — click **Approve**
- `design.md` — click **Approve**
- `tasks.md` — click **Approve**

---

## 🟣 PHASE 3 — Set Up Hooks

**Step 12** — In Kiro sidebar → **Hooks** → **New Hook**. Describe it:
```
When any Python file in backend/agent/tools/ is saved,
generate pytest tests for that tool file.
Mock all AWS Bedrock calls using unittest.mock.
Test success case, empty input, and malformed JSON response.
Save tests to backend/tests/test_{filename}.py
```

**Step 13** — Create a second hook:
```
When main.py is saved,
check that CORS middleware is present,
all endpoints have proper error handling with try/except,
and update the API section of README.md with current endpoints.
```

---

## 🟣 PHASE 4 — Implement Each Task in Kiro Agent Mode

Switch Kiro chat to **Agent mode**. Run these one by one — **wait for each to complete before the next**.

---

**Step 14 — Task 1: PDF Parser**
```
Implement backend/parsers/pdf_parser.py

Use pdfplumber to extract text from PDF bytes (not file path).
Handle both text-based and table-based PDFs.
Return a single clean string combining all pages and tables.
Function signature: extract_text_from_bytes(pdf_bytes: bytes) -> str
```

---

**Step 15 — Task 2: Contract Extractor Tool**
```
Implement backend/agent/tools/contract_extractor.py

Use the @tool decorator from strands.
Use BedrockModel with claude-sonnet-4, temperature=0.0.
Create a nested Agent inside the tool for extraction.

The tool function extract_contract_terms(contract_text: str) -> dict
must return this exact structure:
{
  "vendor_name": str,
  "contract_ref": str,
  "effective_date": str,
  "expiry_date": str,
  "unit_prices": [{"service": str, "unit": str, "price": float}],
  "volume_caps": [{"service": str, "cap": float, "unit": str, "overage_rate": float}],
  "billing_cycle": str,
  "payment_terms_days": int,
  "prohibited_charges": [str],
  "amendment_refs": [str],
  "confidence": float
}

Strip any markdown backticks before JSON parsing.
The docstring must clearly explain what the tool does —
Strands uses it for reasoning.
```

---

**Step 16 — Task 3: Invoice Extractor Tool**
```
Implement backend/agent/tools/invoice_extractor.py

Same pattern as contract_extractor — @tool decorator,
BedrockModel temperature=0.0, nested Agent.

Function extract_invoice_data(invoice_text: str) -> dict
must return:
{
  "vendor_name": str,
  "invoice_number": str,
  "invoice_date": str,
  "billing_period": str,
  "line_items": [
    {
      "description": str,
      "unit": str,
      "quantity": float,
      "unit_price": float,
      "amount": float,
      "looks_unusual": bool
    }
  ],
  "subtotal": float,
  "tax_amount": float,
  "total": float,
  "amendment_refs": [str],
  "vendor_notes": [str],
  "confidence": float
}
```

---

**Step 17 — Task 4: Drift Scorer Tool**
```
Implement backend/agent/tools/drift_scorer.py

Function compute_drift_score(contract_data: dict, invoice_data: dict) -> dict

Logic:
1. Build lookup maps from contract unit_prices and volume_caps
2. For each invoice line item:
   - Check price mismatch: if billed > contracted by >1%, score += proportional (max 40), add PRICE_MISMATCH finding
   - Check volume overage: if quantity > cap, score += 20, add VOLUME_OVERAGE finding
   - Check prohibited charges: match description against contract prohibited_charges list, score += 30, add PROHIBITED_CHARGE finding
3. Check unapproved amendments: invoice amendment_refs not in contract amendment_refs, score += 15 each, add UNAPPROVED_AMENDMENT finding
4. Cap score at 100
5. Create a nested Agent with BedrockModel to write a 2-sentence reasoning summary about the findings
6. Return:
{
  "risk_score": int,
  "risk_level": "HIGH"|"MEDIUM"|"LOW",
  "findings": [...],
  "estimated_overbill_inr": float,
  "reasoning": str,
  "total_findings": int
}
```

---

**Step 18 — Task 5: Wire Strands Agent**
```
Implement backend/agent/audit_agent.py

Import all 3 tools and create the audit_agent using strands.Agent.
Use BedrockModel with claude-sonnet-4, temperature=0.0.

System prompt must instruct the agent to:
1. ALWAYS call extract_contract_terms() first
2. ALWAYS call extract_invoice_data() second
3. ALWAYS call compute_drift_score() third
4. Return a complete audit report

Set max_parallel_tools=1 for sequential execution.
```

---

**Step 19 — Task 6: S3 Manager**
```
Implement backend/storage/s3_manager.py

Functions needed:
- upload_contract(file_bytes, vendor_name, contract_ref) -> str (returns S3 key)
- upload_invoice(file_bytes, vendor_name, period) -> str
- download_pdf(s3_key) -> bytes
- save_audit_result(contract_ref, period, result_dict) -> str
- list_vendor_invoices(vendor_name) -> list

Bucket name: axiom-audit-documents
Region: us-east-1
Use boto3 s3 client.
Add metadata tags to each upload.
```

---

**Step 20 — Task 7: Database**
```
Implement backend/db/models.py and backend/db/crud.py

models.py — SQLAlchemy AuditResult table with columns:
id, vendor_name, invoice_number, audit_date,
contract_unit_price, billed_unit_price, price_variance_pct,
estimated_overbill, risk_score, risk_level,
findings (JSON), amendment_detected, s3_contract_key,
s3_invoice_key, s3_result_key, extraction_confidence

crud.py — functions:
- save_audit(result_dict) -> AuditResult
- get_all_audits() -> list
- get_audits_by_vendor(vendor_name) -> list
- get_high_risk_audits() -> list (risk_score >= 50)
```

---

**Step 21 — Task 8: FastAPI Backend**
```
Implement backend/main.py

Include:
- CORS middleware allowing http://localhost:5173
- POST /audit endpoint accepting contract + invoice files as multipart/form-data
  also accepting vendor_name, contract_ref, billing_period as form fields
  Flow: read bytes → upload to S3 → extract text → run audit_agent → save to DB + S3 → return result
- POST /query endpoint accepting JSON { "query": str }
  passes query to audit_agent and returns result
- GET /audits endpoint returning all audit results from DB
- Proper try/except on all endpoints with HTTP 500 on error
```

---

**Step 22 — Task 9: AgentCore App**
```
Implement backend/agent_app.py

Wrap the existing audit_agent with BedrockAgentCoreApp.

The @app.entrypoint function invoke(payload) should handle two modes:
1. If payload has "prompt" key → pass to audit_agent directly
2. If payload has "contract_s3_key" and "invoice_s3_key" keys:
   → download both PDFs from S3
   → extract text
   → run audit_agent
   → save result to S3
   → return result dict

Add: if __name__ == "__main__": app.run()
```

---

**Step 23 — Task 10: Frontend**
```
Copy the AuditDashboard.jsx file I already have into frontend/src/AuditDashboard.jsx

Then update frontend/src/App.jsx to:
import AuditDashboard from "./AuditDashboard"
export default function App() { return <AuditDashboard /> }