#  Finance Credit Follow-Up Email Agent
> Task 2 · AI Enablement Internship · Individual Submission

An AI agent that automatically generates personalised, tone-escalating payment follow-up emails for overdue invoices — using Gemini as the LLM brain.

---

##  Project Structure

```
finance_agent/
├── agent.py              ← Core agent logic (LLM + escalation)
├── dashboard.py          ← Streamlit UI (optional)
├── data/
│   └── invoices.csv      ← Your invoice data goes here
├── logs/
│   └── audit_log.json    ← Auto-generated audit trail
├── output/
│   └── emails_output.json← Generated emails saved here
├── .env.example          ← Copy to .env and add your API key
├── .gitignore
├── requirements.txt
└── README.md
```

---

##  Quick Start (5 Steps)

### Step 1 — Clone & enter the project
```bash
git clone <your-repo-url>
cd finance_agent
```

### Step 2 — Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set your API key
```bash
cp .env.example .env
# Open .env and paste your Gemini API key
```

### Step 5 — Run the agent
```bash
# Option A: Command line (simplest)
python agent.py

# Option B: Streamlit dashboard (visual)
streamlit run dashboard.py
```

---

##  Input Data Format

Edit `data/invoices.csv` with your real invoice data:

```csv
invoice_no,client_name,amount,due_date,contact_email,follow_up_count
INV-2024-001,Rajesh Kapoor,45000,2025-04-20,rajesh@example.com,0
INV-2024-002,Priya Sharma,12000,2025-04-15,priya@example.com,1
```

| Column | Description |
|---|---|
| `invoice_no` | Unique invoice ID |
| `client_name` | Full client name |
| `amount` | Amount due (₹) |
| `due_date` | Format: DD-MM-YYYY |
| `contact_email` | Client's email address |
| `follow_up_count` | How many follow-ups sent so far |

---

##  How It Works — Agent Flow

```
invoices.csv
     │
     ▼
[1] READ & PARSE
     Agent reads CSV, computes days overdue for each invoice.
     │
     ▼
[2] DETERMINE STAGE
     days overdue → Stage 1/2/3/4 or Legal Flag (Stage 5)
     │
     ▼
[3] GENERATE EMAIL (Gemini API)
     Stage + invoice data → personalised email (subject + body)
     │
     ▼
[4] DRY RUN / SEND
     dry_run=True  → email is only logged, never sent
     dry_run=False → plug in SMTP/SendGrid here
     │
     ▼
[5] AUDIT LOG
     Every email logged to logs/audit_log.json with timestamp
     │
     ▼
[6] OUTPUT
     All generated emails saved to output/emails_output.json
```

---

##  Tone Escalation Matrix

| Stage | Days Overdue | Tone | Key Message | CTA |
|---|---|---|---|---|
| 1 | 1–7 days | 🟢 Warm & Friendly | Gentle reminder | Pay via link |
| 2 | 8–14 days | 🟡 Polite but Firm | Still pending | Confirm payment date |
| 3 | 15–21 days | 🟠 Formal & Serious | Escalating concern | Respond in 48 hrs |
| 4 | 22–30 days | 🔴 Stern & Urgent | Final reminder | Pay immediately |
| 5 | 30+ days | 🚨 Legal Flag | No email sent | Assigned to manager |

---

## 🛠️ Technical Stack & Decision Log

### LLM Chosen
| Item | Detail |
|---|---|
| **Model** | `gemini-flash-latest` (Google) |
| **Why this model?** | Strong instruction-following for structured JSON output, large context window, cost-effective, excellent tone control for email generation |
| **Output mode** | JSON-only via system prompt — no free-form text, easy to parse |

### Agent Framework
| Item | Detail |
|---|---|
| **Framework** | Custom lightweight agent (no LangChain/CrewAI) |
| **Why no heavy framework?** | For a focused single-task agent, LangChain adds complexity without benefit. A simple loop over CSV rows + one LLM call per record is cleaner, faster to debug, and easier for a fresher to understand |
| **Architecture** | Sequential: Read → Classify → Generate → Log |

### Prompt Design
**System Prompt:**
```
You are a professional finance assistant writing payment follow-up emails.
Return ONLY valid JSON with keys: subject, body.
Do not add markdown, code fences, or any extra text.
Never fabricate data — use only the fields provided.
```
**Guardrails applied:**
- Explicit "ONLY JSON" instruction prevents free-form text
- "Never fabricate" instruction prevents hallucination
- All client fields injected explicitly — LLM cannot invent data
- Output parsed with `json.loads()` + error handling

---

##  Security Risk Mitigations

| Risk | Mitigation Applied |
|---|---|
| **Prompt Injection** | `sanitise()` function strips `{}` and backticks from all CSV fields before injecting into prompt. Malicious CSV values cannot break prompt structure. |
| **Data Privacy / PII** | `dry_run=True` by default — no real emails sent. Logs store invoice numbers & names but NOT full email bodies by default in production. |
| **API Key Exposure** | Key stored in `.env` file via `python-dotenv`. `.env` is in `.gitignore`. `.env.example` (no real key) committed instead. |
| **Hallucination Risk** | System prompt forces JSON-only output. All invoice fields are explicitly provided — LLM has no reason to invent data. `json.loads()` validation catches malformed responses. |
| **Unauthorised Access** | No public endpoint exposed. Agent runs locally. For production: add API key auth or OAuth before exposing any endpoint. |
| **Email Spoofing (Stage 2)** | Dry-run mode is default. For real sending: use verified sender domain with SPF/DKIM/DMARC configured on your email provider. |
| **Escalation Cap** | Stage 5 (30+ days) never sends email — flags for human/legal review only. Hard-coded cap prevents infinite auto-emails. |

---

##  Output Files

### `output/emails_output.json`
```json
[
  {
    "invoice": "INV-2024-001",
    "client": "Rajesh Kapoor",
    "days_overdue": 23,
    "stage": 4,
    "tone": "Stern & Urgent",
    "subject": "FINAL NOTICE – Invoice #INV-2024-001 – Immediate Action Required",
    "body": "Dear Mr. Kapoor, This is our final reminder...",
    "status": "DRY_RUN"
  }
]
```

### `logs/audit_log.json`
```json
[
  {
    "timestamp": "2025-05-13T10:30:00",
    "invoice_no": "INV-2024-001",
    "client": "Rajesh Kapoor",
    "days_overdue": 23,
    "stage": 4,
    "tone": "Stern & Urgent",
    "subject": "FINAL NOTICE...",
    "send_status": "DRY_RUN"
  }
]
```

---

##  Adding Real Email Sending (Optional)

When ready to go live, replace the mock send section in `agent.py`:

```python
# Using smtplib (Gmail example)
import smtplib
from email.mime.text import MIMEText

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.getenv("SENDER_EMAIL")
    msg["To"] = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("SENDER_EMAIL"), os.getenv("SMTP_PASSWORD"))
        smtp.send_message(msg)
```

Add to `.env`:
```
SENDER_EMAIL=finance@yourcompany.com
SMTP_PASSWORD=your_app_password
```


- [ ] Run `python agent.py` — show console output
- [ ] Show `output/emails_output.json` — all 4 tone stages visible
- [ ] Show `logs/audit_log.json` — audit trail complete
- [ ] Open `streamlit run dashboard.py` — show dashboard
- [ ] Point out Stage 5 legal flag in results
- [ ] Show `.env.example` vs `.gitignore` (security)

---

## 👤 Author
Amritanshi Singh · AI Enablement Internship · Task 2
