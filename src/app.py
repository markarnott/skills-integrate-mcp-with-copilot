"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import re
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

DAY_NAME_TO_INDEX = {
    "monday": 0,
    "mondays": 0,
    "tuesday": 1,
    "tuesdays": 1,
    "wednesday": 2,
    "wednesdays": 2,
    "thursday": 3,
    "thursdays": 3,
    "friday": 4,
    "fridays": 4,
    "saturday": 5,
    "saturdays": 5,
    "sunday": 6,
    "sundays": 6,
}


def parse_schedule(schedule_text: str):
    """Parse a schedule string into weekday and minute ranges."""
    schedule_text = schedule_text.strip()
    match = re.match(
        r"^(?P<days>.+),\s*(?P<start>\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(?P<end>\d{1,2}:\d{2}\s*(?:AM|PM))$",
        schedule_text,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Invalid schedule format: {schedule_text}")

    days_part = match.group("days")
    start_time = datetime.strptime(match.group("start").upper(), "%I:%M %p")
    end_time = datetime.strptime(match.group("end").upper(), "%I:%M %p")
    if end_time <= start_time:
        raise ValueError(f"Invalid schedule time range: {schedule_text}")

    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute

    days = re.split(r"\s*(?:,|and)\s*", days_part)
    parsed = []
    for day in days:
        normalized = day.strip().lower()
        if normalized not in DAY_NAME_TO_INDEX:
            raise ValueError(f"Invalid day name in schedule: {day}")
        parsed.append((DAY_NAME_TO_INDEX[normalized], start_minutes, end_minutes))

    return parsed


def schedules_conflict(schedule_a, schedule_b):
    for day_a, start_a, end_a in schedule_a:
        for day_b, start_b, end_b in schedule_b:
            if day_a != day_b:
                continue
            if start_a < end_b and start_b < end_a:
                return True
    return False


def find_conflicting_activity(activity_name: str, student_email: str, new_schedule):
    for existing_name, existing_activity in activities.items():
        if existing_name == activity_name:
            continue
        if student_email not in existing_activity["participants"]:
            continue

        existing_schedule = parse_schedule(existing_activity["schedule"])
        if schedules_conflict(new_schedule, existing_schedule):
            return existing_name, existing_activity["schedule"]

    return None, None


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Check for schedule conflicts with existing enrollments
    try:
        new_schedule = parse_schedule(activity["schedule"])
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    conflicting_activity, conflicting_schedule = find_conflicting_activity(
        activity_name,
        email,
        new_schedule,
    )

    if conflicting_activity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Schedule conflict detected with '{conflicting_activity}' "
                f"({conflicting_schedule}). Please choose a different activity or unregister first."
            )
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
