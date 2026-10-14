from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# --- Security Setup ---
SECRET_KEY = "super_secret_jwt_key_change_this_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title="Portal Manage API",
    description="FastAPI Backend with JWT Auth and Attendance CRUD",
    version="1.0"
)

# --- In-Memory Storage ---
USERS_DB = {}
EMPLOYEES_DB = {
    "101": {"name": "Alice Smith", "department": "Engineering", "status": "Active"},
    "102": {"name": "Bob Jones", "department": "HR", "status": "Active"}
}
ATTENDANCE_LOGS = []

# --- Pydantic Models ---
class UserRegister(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="password123")
    role: str = Field("admin", example="admin")

class Token(BaseModel):
    access_token: str
    token_type: str

class ClockRequest(BaseModel):
    employee_id: str

class EmployeeCreate(BaseModel):
    employee_id: str = Field(..., example="103")
    name: str = Field(..., example="Charlie Day")
    department: str = Field(..., example="Finance")
    status: str = Field("Active", example="Active")

class EmployeeFullUpdate(BaseModel):
    name: str
    department: str
    status: str

class EmployeePartialUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None


# --- Helper Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in USERS_DB:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return USERS_DB[username]


# --- Authentication Routes ---
@app.post("/register", status_code=status.HTTP_201_CREATED, summary="Register User")
def register_user(user: UserRegister):
    if user.username in USERS_DB:
        raise HTTPException(status_code=400, detail="Username already exists")
    USERS_DB[user.username] = {
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "role": user.role
    }
    return {"message": f"User '{user.username}' registered successfully"}

@app.post("/token", response_model=Token, summary="Login for Access Token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Public Root ---
@app.get("/")
def read_root():
    return {"status": "MVP Server Running"}


# --- Protected Endpoints ---
@app.get("/employees")
def get_all_employees(current_user: dict = Depends(get_current_user)):
    return {"count": len(EMPLOYEES_DB), "data": EMPLOYEES_DB}

@app.get("/employees/{employee_id}")
def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    if employee_id not in EMPLOYEES_DB:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"employee_id": employee_id, "data": EMPLOYEES_DB[employee_id]}

@app.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(emp: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    if emp.employee_id in EMPLOYEES_DB:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    EMPLOYEES_DB[emp.employee_id] = {
        "name": emp.name,
        "department": emp.department,
        "status": emp.status
    }
    return {"message": "Employee created successfully", "data": EMPLOYEES_DB[emp.employee_id]}

@app.put("/employees/{employee_id}")
def update_employee_full(employee_id: str, emp_data: EmployeeFullUpdate, current_user: dict = Depends(get_current_user)):
    if employee_id not in EMPLOYEES_DB:
        raise HTTPException(status_code=404, detail="Employee not found")
    EMPLOYEES_DB[employee_id] = emp_data.dict()
    return {"message": f"Employee {employee_id} updated completely", "data": EMPLOYEES_DB[employee_id]}

@app.patch("/employees/{employee_id}")
def update_employee_partial(employee_id: str, emp_data: EmployeePartialUpdate, current_user: dict = Depends(get_current_user)):
    if employee_id not in EMPLOYEES_DB:
        raise HTTPException(status_code=404, detail="Employee not found")
    record = EMPLOYEES_DB[employee_id]
    if emp_data.name is not None: record["name"] = emp_data.name
    if emp_data.department is not None: record["department"] = emp_data.department
    if emp_data.status is not None: record["status"] = emp_data.status
    return {"message": f"Employee {employee_id} updated partially", "data": record}

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    if employee_id not in EMPLOYEES_DB:
        raise HTTPException(status_code=404, detail="Employee not found")
    removed = EMPLOYEES_DB.pop(employee_id)
    return {"message": f"Employee {employee_id} ({removed['name']}) deleted"}

@app.post("/clock-in")
def clock_in(data: ClockRequest, current_user: dict = Depends(get_current_user)):
    emp_id = data.employee_id.strip()
    if emp_id not in EMPLOYEES_DB:
        raise HTTPException(status_code=404, detail="Employee ID not found")
    ATTENDANCE_LOGS.append({"employee_id": emp_id, "action": "IN", "by": current_user["username"]})
    return {"message": f"Clocked IN: {EMPLOYEES_DB[emp_id]['name']}"}

@app.post("/clock-out")
def clock_out(data: ClockRequest, current_user: dict = Depends(get_current_user)):
    emp_id = data.employee_id.strip()
    if emp_id not in EMPLOYEES_DB:
        raise HTTPException(status_code=404, detail="Employee ID not found")
    ATTENDANCE_LOGS.append({"employee_id": emp_id, "action": "OUT", "by": current_user["username"]})
    return {"message": f"Clocked OUT: {EMPLOYEES_DB[emp_id]['name']}"}