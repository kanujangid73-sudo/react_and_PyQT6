from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI(title="Enterprise Inquiry Management System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Direct Bearer Security Scheme (Creates Authorize button without Auth Endpoints)
security = HTTPBearer()

# Hardcoded API Secret Key for verification
SECRET_API_KEY = "mysecrettoken123"

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != SECRET_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing Secret API Key"
        )
    return credentials.credentials

# In-Memory Database
inquiries_db = {}
inq_id_counter = 1

# Pydantic Schemas
class InquiryData(BaseModel):
    client_name: str
    subject: str
    description: str

class StatusUpdate(BaseModel):
    status: str

# Root UI Landing Page
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Inquiry Management API</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white min-h-screen flex items-center justify-center p-6">
        <div class="max-w-xl w-full bg-slate-800 rounded-2xl shadow-2xl p-8 border border-slate-700 text-center">
            <h1 class="text-3xl font-bold mb-2">Inquiry Management API</h1>
            <p class="text-slate-400 mb-6">Status: <span class="text-emerald-400 font-semibold">● Live & Ready</span></p>
            <a href="/docs" class="inline-block w-full py-3 px-6 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition">
                Explore Swagger Documentation →
            </a>
        </div>
    </body>
    </html>
    """

# ==================== THE 5 CRUD REST DECORATORS ====================

# 1. GET - Fetch All Inquiries
@app.get("/inquiries", tags=["Inquiries"], summary="Get All Inquiries")
def get_inquiries(token: str = Depends(verify_token)):
    return {"inquiries": list(inquiries_db.values())}

# 2. POST - Create Inquiry
@app.post("/inquiries", tags=["Inquiries"], summary="Create Inquiry")
def create_inquiry(data: InquiryData, token: str = Depends(verify_token)):
    global inq_id_counter
    new_item = {
        "id": inq_id_counter,
        "client_name": data.client_name,
        "subject": data.subject,
        "description": data.description,
        "status": "Pending"
    }
    inquiries_db[inq_id_counter] = new_item
    inq_id_counter += 1
    return {"message": "Inquiry created successfully", "data": new_item}

# 3. PUT - Full Update / Replace
@app.put("/inquiries/{inquiry_id}", tags=["Inquiries"], summary="Full Update Inquiry")
def replace_inquiry(inquiry_id: int, data: InquiryData, token: str = Depends(verify_token)):
    if inquiry_id in inquiries_db:
        inquiries_db[inquiry_id].update({
            "client_name": data.client_name,
            "subject": data.subject,
            "description": data.description
        })
        return {"message": "Inquiry fully updated", "data": inquiries_db[inquiry_id]}
    raise HTTPException(status_code=404, detail="Inquiry not found")

# 4. PATCH - Partial Update (Status Only)
@app.patch("/inquiries/{inquiry_id}", tags=["Inquiries"], summary="Partial Update Status")
def update_status(inquiry_id: int, data: StatusUpdate, token: str = Depends(verify_token)):
    if inquiry_id in inquiries_db:
        inquiries_db[inquiry_id]["status"] = data.status
        return {"message": "Status updated successfully", "data": inquiries_db[inquiry_id]}
    raise HTTPException(status_code=404, detail="Inquiry not found")

# 5. DELETE - Remove Inquiry
@app.delete("/inquiries/{inquiry_id}", tags=["Inquiries"], summary="Delete Inquiry")
def delete_inquiry(inquiry_id: int, token: str = Depends(verify_token)):
    if inquiry_id in inquiries_db:
        del inquiries_db[inquiry_id]
        return {"message": "Inquiry deleted successfully"}
    raise HTTPException(status_code=404, detail="Inquiry not found")