# v1 – basic extraction
PROMPT_V1 = """
Extract shipment details from the email and return JSON.
"""

# v2 – added rules
PROMPT_V2 = """
Extract LCL shipment details.
Rules:
- Body overrides subject
- First shipment only
- Default incoterm FOB
Return JSON.
"""

# v3 – final strict prompt
PROMPT_V3 = """
You are extracting LCL sea freight shipment details from an email.

Rules:
- Body overrides subject
- Extract ONLY the first shipment
- Default incoterm = FOB if missing or ambiguous
- Missing values → null
- Extract PORT NAMES only (not codes)

Dangerous goods:
- DG / dangerous / hazardous / IMO / IMDG / Class <number> → true
- non-DG / non hazardous / not dangerous → false
- no mention → false

Return ONLY valid JSON with keys:
origin_port
destination_port
incoterm
cargo_weight_kg
cargo_cbm
is_dangerous

Email:
Subject: {subject}
Body: {body}
"""
