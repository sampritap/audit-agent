---
inclusion: always
---
# Tech Stack
## Backend
- Python 3.11, FastAPI, uvicorn
- Strands Agents SDK — always use @tool decorator
- AWS Bedrock — model: us.anthropic.claude-sonnet-4-20250514-v1:0
- BedrockModel from strands.models — temperature=0.0 for all extractors
- pdfplumber for PDF parsing (handles tables)
- SQLAlchemy + SQLite for audit storage
- boto3 for S3 (bucket: axiom-audit-documents)

## Frontend
- React 18 + Vite
- Fetch API only (no axios)
- TailwindCSS

## Rules
- Tool docstrings must be detailed — Strands uses them for reasoning
- All tools return typed dicts, never raw strings
- FastAPI always includes CORS middleware
- Never hardcode AWS credentials — use environment variables