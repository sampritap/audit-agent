"""
Mock responses for local testing without AWS Bedrock access.
These simulate the AI extraction results.
"""

MOCK_CONTRACT_DATA = {
    "vendor_name": "CloudTech Solutions",
    "contract_ref": "MSA-2024-CT-00892",
    "effective_date": "2024-01-01",
    "expiry_date": "2025-12-31",
    "unit_prices": [
        {"service": "Cloud Compute Premium Tier", "unit": "instance-hour", "price": 7.20},
        {"service": "Object Storage", "unit": "GB-month", "price": 2.80},
        {"service": "Data Transfer Out", "unit": "GB", "price": 0.85},
        {"service": "Database Managed Service", "unit": "instance-hour", "price": 12.50}
    ],
    "volume_caps": [
        {"service": "Cloud Compute Premium Tier", "cap": 2000.0, "unit": "instance-hours", "overage_rate": 8.50},
        {"service": "Object Storage", "cap": 10000.0, "unit": "GB-month", "overage_rate": 3.20}
    ],
    "billing_cycle": "monthly",
    "payment_terms_days": 30,
    "prohibited_charges": [
        "platform maintenance fees",
        "infrastructure levies",
        "administrative surcharges",
        "consulting fees not pre-approved"
    ],
    "amendment_refs": [],
    "confidence": 0.95
}

MOCK_INVOICE_DATA = {
    "vendor_name": "CloudTech Solutions",
    "invoice_number": "INV-CT-2024-0387",
    "invoice_date": "2024-03-31",
    "billing_period": "March 2024",
    "line_items": [
        {
            "description": "Cloud Compute Premium Tier",
            "unit": "instance-hour",
            "quantity": 2050.0,
            "unit_price": 8.95,  # PRICE_MISMATCH: should be 7.20
            "amount": 18347.50,
            "looks_unusual": True
        },
        {
            "description": "Object Storage",
            "unit": "GB-month",
            "quantity": 11400.0,  # VOLUME_OVERAGE: cap is 10000
            "unit_price": 2.80,
            "amount": 31920.00,
            "looks_unusual": True
        },
        {
            "description": "Data Transfer Out",
            "unit": "GB",
            "quantity": 850.0,
            "unit_price": 0.85,
            "amount": 722.50,
            "looks_unusual": False
        },
        {
            "description": "Database Managed Service",
            "unit": "instance-hour",
            "quantity": 720.0,
            "unit_price": 12.50,
            "amount": 9000.00,
            "looks_unusual": False
        },
        {
            "description": "Platform Infrastructure Levy",  # PROHIBITED_CHARGE
            "unit": "flat-fee",
            "quantity": 1.0,
            "unit_price": 18500.00,
            "amount": 18500.00,
            "looks_unusual": True
        }
    ],
    "subtotal": 78490.00,
    "tax_amount": 14128.20,
    "total": 92618.20,
    "amendment_refs": ["AMD-2024-01"],  # UNAPPROVED_AMENDMENT
    "vendor_notes": [
        "New pricing per Amendment AMD-2024-01",
        "Infrastructure levy covers Q1 2024 platform upgrades"
    ],
    "confidence": 0.92
}
