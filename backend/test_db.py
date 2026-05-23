from db.crud import save_audit, get_all_audits, get_high_risk_audits

print("Saving audit to DB...")
saved = save_audit({
    "vendor_name": "CloudTech Solutions",
    "invoice_number": "INV-CT-2024-0387",
    "risk_score": 85,
    "risk_level": "HIGH",
    "estimated_overbill_inr": 44850.0,
    "findings": [
        {
            "type": "PRICE_MISMATCH",
            "service": "Cloud Compute Premium Tier",
            "contracted_rate": 7.20,
            "billed_rate": 8.95,
            "contract_clause": "Section 2.1"
        },
        {
            "type": "UNAPPROVED_AMENDMENT",
            "amendment_refs": ["AMD-2024-01"],
            "contract_clause": "Section 9"
        }
    ]
})
print("Saved with ID:", saved.id if saved else "FAILED")

print()
print("Fetching all audits...")
all_audits = get_all_audits()
print(f"Total audits: {len(all_audits)}")

print()
print("Fetching high risk audits...")
high_risk = get_high_risk_audits()
print(f"High risk count: {len(high_risk)}")
for a in high_risk:
    print(f"  Vendor: {a['vendor_name']} | Score: {a['risk_score']} | Level: {a['risk_level']}")