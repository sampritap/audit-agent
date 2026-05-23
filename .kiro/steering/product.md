---
inclusion: always
---
# Product: AI Vendor Invoice Audit Agent

## Purpose
Autonomously audit vendor invoices against contracts.
Detect financial anomalies. Assign risk scores.

## The 5 things it detects
1. PRICE_MISMATCH — billed rate higher than contracted rate
2. VOLUME_OVERAGE — quantity exceeds contracted cap
3. PROHIBITED_CHARGE — charge type banned in contract Section 6
4. UNAPPROVED_AMENDMENT — invoice cites amendment not in contract
5. DISPUTED_QUANTITY — billed units not matching usage logs

## Sample data already exists
- Contract: CloudTech Solutions MSA-2024-CT-00892
- Invoice: INV-CT-2024-0387 for March 2024
- 5 planted overbilling issues in the invoice