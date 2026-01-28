from dotenv import load_dotenv
import os
from groq import Groq
import json
import re
import time
from tqdm import tqdm
from prompts import PROMPT_V3
from schemas import EmailExtraction

load_dotenv()
client=Groq(api_key=os.getenv('GROQ_API_KEY'))


PORT_ALIAS_MAP = {
    "madras": "chennai",
    "maa": "chennai",
    "maa icd": "chennai icd",

    "blr": "bangalore",
    "blr icd": "bangalore icd",

    "hyd": "hyderabad",
    "hyd icd": "hyderabad icd",
}


def normalize(text):
    if not text:
        return ""
    
    text=text.lower()

    for alias, canonical in PORT_ALIAS_MAP.items():
        if alias in text:
            text=text.replace(alias,canonical)

    text=re.sub(r"[^a-z\s]","",text.lower())
    
    return text.strip()


def build_port_index(ports_data):
    index_dict={}

    for p in ports_data:
        key=normalize(p['name'])
        index_dict.setdefault(key,[]).append(p)

    return index_dict


def infer_origin_from_text(text, port_index):
    text = text.lower()

    COUNTRY_KEYWORDS = {
        "japan": "japan",
        "japanese": "japan",
        "korea": "korea",
        "korean": "korea",
        "china": "china",
        "chinese": "china",
    }

    for word, canonical in COUNTRY_KEYWORDS.items():
        if word in text:
            key = normalize(canonical)
            if key in port_index:
                ports = port_index[key]
                return ports[0]["code"], ports[0]["name"]

    return None, None


def resolve_port(port_name,port_index,body,subject):
    if not port_name:
        return None,None
    
    key=normalize(port_name)
    body = body.lower()
    subject=subject.lower()

    candidates=[]

    if key in port_index:
        condidates=port_index[key]

    if not candidates:
        for name,ports in port_index.items():
            if name in key or key in name:
                candidates.extend(ports)

    if not candidates:
        return None, None
    
    indian_ports=[port for port in candidates if port['code'].startswith('IN')]

    if indian_ports:
        candidates=indian_ports

    multi_route = (
        body.count("→") > 1
        or body.count(";") > 1
    )
    
    if "icd" in body:
        if multi_route:
            for port in candidates:
                if 'icd' in port['name'].lower() and '/' in port['name']:
                    return port['code'],port['name']
        else:
            for port in candidates:
                if 'icd' in port['name'].lower() and '/' not in port['name']:
                    return port['code'],port['name']
    if multi_route:        
        for port in candidates:
            if '/' in port['name'] and 'icd' not in port['name'].lower():
                return port['code'],port['name']
        
    for port in candidates:
        if '/' not in port['name'] and 'icd' not in port['name'].lower():
            return port['code'],port['name']
            
    if "india" in body or "india" in subject:
        for port in candidates:
            if "india" in port["name"].lower():
                return port["code"], port["name"]
            
    return candidates[0]['code'],candidates[0]['name']


def parse_weight(text):
    kg=re.search(r"([\d,\.]+)\s*(kg|kgs)",text,re.I)
    if kg:
        return round(float(kg.group(1).replace(",","")),2)

    lb=re.search(r"([\d,\.]+)\s*(lb|lbs)",text,re.I)
    if lb:
        return round(float(lb.group(1))*0.453592,2)
    
    mt=re.search(r"([\d,\.]+)\s*(mt|tonnes?)",text,re.I)
    if mt:
        return round(float(mt.group(1))*1000,2)
    
    return None

def parse_cbm(text):
    m=re.search(r"([\d\.]+)\s*cbm",text,re.I)

    return round(float(m.group(1)),2) if m else None


def detect_dg(text):
    text=text.lower()

    if any(x in text for x in ["non-dg", "non dg", "non-hazardous","non hazardous", "not dangerous"]):
        return False
    
    if any(x in text for x in ["dg", "dangerous", "hazardous", "imo", "imdg"]):
        return True
    
    if re.search(r"\bclass\s*\d+\b",text,re.I):
        return True

    return False

def extract_json(raw):
    raw=raw.strip()

    if raw.startswith("```"):
        raw=raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)


def call_llm(prompt,retries=3):
    for i in range(retries):
        try:
            res=client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
            )
            return res.choices[0].message.content
        except Exception as e:
            print(f"LLM attempt {i+1} failed:", repr(e))
            time.sleep(2**i)
    raise RuntimeError('LLM failed after retries')

emails=json.load(open('emails_input.json'))
ports=json.load(open('port_codes_reference.json'))
port_index=build_port_index(ports)
# print('\n ports:\n\n')
# print(port_index,">>>>>>\n\n")

# city_tokens = build_city_tokens(ports)


results=[]

for email in tqdm(emails):
    print("\n==============================")
    print("EMAIL ID:", email["id"])
    print("SUBJECT:", email["subject"])
    print("BODY:", email["body"])
    try:
        full_text=f"{email['subject']} {email['body']}"
        prompt=PROMPT_V3.format(
            subject=email['subject'],
            body=email['body']
            )
    
        raw=call_llm(prompt)

        print("\n--- RAW LLM OUTPUT ---")
        print(raw)

        parsed=extract_json(raw)

        print("\n--- PARSED JSON ---")
        print(parsed)

        origin_raw = parsed.get("origin_port")

        if origin_raw:
            o_code,o_name=resolve_port(parsed.get('origin_port'),port_index,email['body'],email['subject'])
        else:
            o_code, o_name = infer_origin_from_text(full_text,port_index)

        d_code,d_name=resolve_port(parsed.get('destination_port'),port_index,email['body'],email['subject'])

        print("\n--- RESOLVED PORTS ---")
        print("Origin:", parsed.get("origin_port"), "→", o_code, o_name)
        print("Destination:", parsed.get("destination_port"), "→", d_code, d_name)


        product_line=None

        if o_code and o_code.startswith('IN'):
            product_line='pl_sea_export_lcl'
        elif d_code and d_code.startswith('IN'):
            product_line='pl_sea_import_lcl'

        incoterm=(parsed.get('incoterm') or 'FOB').upper()

        if "insist" in full_text.lower():
            incoterm = "FOB"
        elif incoterm not in {"FOB","CIF","CFR","EXW","DDP","DAP","FCA","CPT","CIP","DPU"}:
            incoterm = "FOB"

        result=EmailExtraction(
            id=email['id'],
            product_line=product_line,
            incoterm=incoterm,
            origin_port_code=o_code, 
            origin_port_name=o_name,
            destination_port_code=d_code,
            destination_port_name=d_name,
            cargo_weight_kg=parse_weight(full_text),
            cargo_cbm=parse_cbm(full_text),
            is_dangerous=detect_dg(full_text) 
        )

        print("\n--- FINAL RESULT ---")
        print(result.model_dump())

    except Exception:
        result=EmailExtraction(
            id=email["id"],
            product_line=None,
            incoterm=None,
            origin_port_code=None,
            origin_port_name=None,
            destination_port_code=None,
            destination_port_name=None,
            cargo_weight_kg=None,
            cargo_cbm=None,
            is_dangerous=None
        )

    results.append(result.model_dump())

with open('output.json','w') as f:
    json.dump(results,f,indent=2)







