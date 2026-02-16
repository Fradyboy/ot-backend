from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

app = FastAPI()

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
def surgery_type_report():
    report = {}

    for ot in ots.values():
        for record in ot["history" ]:
            s_type = record["surgery_type"] or "Unknown"
            report[s_type] = report.get(s_type, 0) + 1


    return report