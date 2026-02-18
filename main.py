from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "CHANGE_THIS_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Admin+User
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
    },
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash("user123"),
        "role": "OT Assistant",
    },
}

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   #allow all origin
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory OT storage
ots = {
    "OT-1": {
        "status": "FREE", 
        "start_time": None,
        "total_minutes": 0,
        "history": [],
        "current_doctor": None,
        "current_patient": None,
        "current_surgery_type": None,
    },
    "OT-2": {
        "status": "FREE",
        "start_time": None,
        "total_minutes": 0,
        "history": [],
        "current_doctor": None,
        "current_patient": None,
        "current_surgery_type": None,
    },
    "OT-3": {
        "status": "FREE",
        "start_time": None,
        "total_minutes": 0,
        "history": [],
        "current_doctor": None,
        "current_patient": None,
        "current_surgery_type": None,
    }
}

# GET OTs
@app.get("/ots")
def get_ots():
    return ots


#START SURGERY
@app.post("/start-surgery")
def start_surgery(
    ot_name: str = Query(...),
    doctor: str = Query(...),
    patient: str = Query(...),
    surgery_type: str = Query(...)
):
    if ot_name not in ots:
        return {"error": "OT not found"}
    
    ot = ots[ot_name]

    if ot["status"] == "BUSY":
        return {"error": "OT already busy"}

    ot["status"] = "BUSY"
    ot["start_time"] = datetime.now().isoformat()
    ot["current_doctor"] = doctor
    ot["current_patient"] = patient
    ot["current_surgery_type"] = surgery_type

    return {"message": "surgery started"}

# END SURGERY
@app.post("/end-surgery")
def end_surgery(ot_name: str = Query(...)):
    if ot_name not in ots:
        return {"error": "OT not found"}
    
    ot = ots[ot_name]

    if ot["start_time"] is None:
        return {"error": "Surgery not started"}


    start_time = datetime.fromisoformat(ot["start_time"])
    end_time = datetime.now()

    minutes_used = int((end_time - start_time).total_seconds() / 60)

    record = {
        "doctor": ot["current_doctor"],
        "patient": ot["current_patient"],
        "surgery_type": ot["current_surgery_type"],
        "start_time": ot["start_time"],
        "end_time": end_time.isoformat(),
        "minutes_used": minutes_used,
    }


    ot["history"].append(record)
    ot["total_minutes"] += minutes_used
    
    #reset OT
    ot["status"] = "FREE"
    ot["start_time"] = None
    ot["current_doctor"] = None
    ot["current_patient"] = None
    ot["current_surgery_type"] = None

    return {
        "message": "Surgery ended",
        "minutes_used": minutes_used,
    }

# SURGERY TYPE REPORT
@app.get("/surgery-type-report")
def surgery_type_report(
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=403
            detail="Admin only",
        )
    
    report = {}
    for ot in ots.values():
        for record in ot["history" ]:
            s_type = record["surgery_type"] or "Unknown"
            report[s_type] = report.get(s_type, 0) + 1


    return report

# Login Api
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    token = create_access_token(
        data={
            "sub": user["username"],
            "role": user["role"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
    }

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401)
        return {"username": username, "role": role}
    except JWTError:

        raise HTTPException(status_code=401)

