import json

FIELDS = [
    "product_line",
    "origin_port_code",
    "origin_port_name",
    "destination_port_code",
    "destination_port_name",
    "incoterm",
    "cargo_weight_kg",
    "cargo_cbm",
    "is_dangerous",
]

def norm(v):
    if isinstance(v, str):
        return v.strip().lower()
    return v

preds = {x["id"]: x for x in json.load(open("output.json"))}
truths = {x["id"]: x for x in json.load(open("ground_truth.json"))}

total = correct = 0
field_correct = {f: 0 for f in FIELDS}

for eid, truth in truths.items():
    pred = preds[eid]
    for f in FIELDS:
        total += 1
        if norm(truth[f]) == norm(pred[f]):
            correct += 1
            field_correct[f] += 1

print("Field-wise accuracy:")
for f in FIELDS:
    print(f"{f}: {field_correct[f] / len(truths):.2%}")

print(f"\nOverall accuracy: {correct / total:.2%}")

