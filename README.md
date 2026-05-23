# AI Vendor Invoice Audit Agent

An intelligent system that detects overbilling and contract drift in vendor invoices using AI and machine learning.

## Project Structure

```
audit-agent/
├── backend/          # FastAPI Python backend
├── frontend/         # React + Vite frontend
└── generated-diagrams/
```

## Prerequisites

- **Python 3.9+** (for backend)
- **Node.js 16+** and **npm** (for frontend)
- AWS credentials configured (for Bedrock/S3 access)
- Required API keys in `.env` file

## Setup Instructions

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```

Create a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory with your credentials:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

### 2. Frontend Setup

Navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

## Running the Project

### Start Backend Server

From the `backend/` directory:
```bash
# With virtual environment activated
python main.py
```

The backend will start on **http://localhost:8000**

API Documentation available at: **http://localhost:8000/docs**

### Start Frontend Dev Server

From the `frontend/` directory:
```bash
npm run dev
```

The frontend will start on **http://localhost:5173**

## Available Scripts

### Backend
- `python main.py` - Start the FastAPI server
- `python -m pytest` - Run tests

### Frontend
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

## API Endpoints

- `POST /audit` - Perform an audit on a contract and invoice
- `GET /audits` - Get all audit results
- `GET /audits/vendor/{vendor_name}` - Get audits by vendor
- `GET /audits/high-risk` - Get high-risk audits

(See http://localhost:8000/docs for complete API documentation)

## Troubleshooting

### Virtual Environment Issues
```bash
# Deactivate current environment
deactivate

# Remove and recreate
rmdir venv /s /q  # Windows
rm -rf venv       # macOS/Linux

# Recreate
python -m venv venv
```

### Frontend Port Already in Use
```bash
npm run dev -- --port 3000
```

### Backend Connection Issues
- Ensure both backend and frontend are running
- Check CORS settings in `backend/main.py` match your frontend URL
- Verify `.env` file has correct credentials

## Project Features

- AI-powered invoice analysis
- Contract drift detection
- Vendor overbilling detection
- Audit trail and reporting
- Dashboard visualization
- AWS S3 integration
- Database persistence

## Contributing

1. Create a new branch for features
2. Make your changes
3. Test thoroughly
4. Commit with clear messages
5. Push and create a pull request

## License

[Add your license here]
