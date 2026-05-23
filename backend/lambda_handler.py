"""
AWS Lambda handler for FastAPI application.
Uses Mangum to adapt ASGI app to Lambda.
"""
from mangum import Mangum
from main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")

# For testing locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
