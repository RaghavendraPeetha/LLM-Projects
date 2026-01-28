# LLM-Powered Freight Email Extraction System  
**Backend / AI Engineer Assessment – Task Harmony**

---

## Overview

This project implements an **LLM-powered email extraction system** for freight forwarding **LCL pricing enquiries**.  
It converts unstructured customer emails into structured shipment data using a combination of **LLM intelligence and deterministic business rules**.

The solution is designed for **high accuracy, reproducibility, and robustness**, strictly following all business rules provided by Task Harmony.

---

## Setup Instructions

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run extraction
```bash
python extract.py
```

This generates:
```
output.json
```

### 4. Run evaluation
```bash
python evaluate.py
```

---

## Project Structure

```
.
├── extract.py                  # Main extraction pipeline
├── evaluate.py                 # Accuracy calculator
├── prompts.py                  # Prompt versions (v1 → v3)
├── schemas.py                  # Pydantic models
├── port_codes_reference.json   # UN/LOCODE reference
├── emails_input.json           # 50 sample emails
├── ground_truth.json           # Expected outputs
├── output.json                 # Generated results
├── requirements.txt
├── .env.example
└── README.md
```

---

## Extraction Approach

### Pipeline

#### 1. LLM Extraction (Groq – llama-3.3-70b-versatile)
The LLM is used **only for semantic understanding**, extracting:
- origin_port
- destination_port
- incoterm
- cargo_weight_kg
- cargo_cbm
- is_dangerous

#### 2. Deterministic Post-Processing
All business logic is handled in Python:
- Port resolution using port_codes_reference.json
- Alias normalization (Madras → Chennai, MAA → Chennai)
- ICD vs non-ICD disambiguation
- Multi-route detection
- Business rule enforcement

#### 3. Validation
- Pydantic schema validation
- Missing values explicitly set to null

---

## Prompt Evolution

### v1 – Basic Extraction
- Accuracy: ~62%
- Issues:
  - Port names instead of UN/LOCODE
  - Missing incoterms
- Example:
  - EMAIL_007 extracted “Madras” instead of “INMAA”

### v2 – UN/LOCODE Awareness
- Added explicit UN/LOCODE examples
- Improved India detection
- Accuracy: ~78%
- Issues:
  - Multi-route confusion
  - ICD ambiguity

### v3 – Business-Rule Driven (Final)
- Explicit handling of:
  - Subject vs body precedence
  - Multi-shipment detection
  - Incoterm ambiguity
- LLM limited to semantic extraction
- Deterministic logic handled in Python
- Final Accuracy: **91.33%**

---

## Accuracy Metrics

```
product_line:           98.00%
origin_port_code:       92.00%
origin_port_name:       82.00%
destination_port_code:  90.00%
destination_port_name:  78.00%
incoterm:               98.00%
cargo_weight_kg:        92.00%
cargo_cbm:              92.00%
is_dangerous:          100.00%

Overall accuracy:       91.33%
```

---

## Edge Cases Handled

### Alias Mapping
- Madras, MAA, MAA ICD → Chennai / Chennai ICD

### Multi-Route Emails
- Detected using routing symbols (→, ;)
- Combined ICD ports selected where applicable
- First shipment extracted per business rules

### Country-Only Mentions
- “Japan” → JPUKB
- “India” → INMAA (Chennai)

---

## Business Rules Implemented

### Product Line
- Destination in India → pl_sea_import_lcl
- Origin in India → pl_sea_export_lcl

### Incoterm
- Default: FOB
- Invalid or ambiguous → FOB

### Dangerous Goods
- Detects DG, IMDG, IMO, Class numbers
- Negations override positives

### Null Handling
- Missing values → null
- Explicit zero preserved

---

## System Design Answers

### 1. Scale (10,000 emails/day)

- Async queue-based architecture
- Batched LLM calls with rate limiting
- Stateless Python workers
- Cached port resolution
- Manual review for low-confidence cases

### 2. Monitoring Accuracy Drop

- Rolling field-level accuracy metrics
- Null-rate monitoring
- Regression testing on failed samples
- Prompt and alias map updates

### 3. Multilingual Emails

- Language detection
- Multilingual prompt variants
- Same deterministic post-processing
- Per-language accuracy tracking

---

## Key Design Decisions

- LLM for semantic understanding, rules for business logic
- Canonical UN/LOCODE enforcement
- Explicit null handling
- temperature = 0 for reproducibility

---

## Submission Notes

- Retry logic with exponential backoff implemented
- Script never crashes on malformed inputs
- All failures return null fields
- Output strictly follows required schema

---

**Author:** P. Raghavendra  
**Assessment:** Task Harmony – Backend / AI Engineer
