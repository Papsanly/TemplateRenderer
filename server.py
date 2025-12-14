import os
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse

from renderer.config import OUTPUT_PATH
from renderer.template import render_template
from renderer.convert import convert_to_pdf

app = FastAPI()


def clean_temp_files():
    temp_filename = os.path.join(OUTPUT_PATH, "temp.html")
    output_filename = os.path.join(OUTPUT_PATH, "out.pdf")
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
    if os.path.exists(output_filename):
        os.remove(output_filename)


def map_simulator_to_gate(simulator: str) -> str:
    """Map simulator code to gate name"""
    mapping = {
        "airbus320": "Airbus A320",
        "boeing737": "Boeing 737 MAX",
        "formula1": "Formula 1"
    }
    return mapping.get(simulator.lower(), simulator)


def map_duration_to_seat_class(duration: int) -> str:
    """Map duration to seat class"""
    if duration == 30:
        return "Economy Class"
    elif duration == 60:
        return "Business Class"
    elif duration == 120:
        return "First Class"
    return "Economy Class"


@app.get("/")
async def generate_certificate(
    simulator: str, 
    duration: str, 
    code: str, 
    expiration: str = None,
    tasks: BackgroundTasks = None
):
    # Convert duration to int
    duration_int = int(duration)
    
    # Map values
    gate = map_simulator_to_gate(simulator)
    seat_class = map_duration_to_seat_class(duration_int)
    
    # Format expiration date if provided
    if expiration:
        try:
            exp_date = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
            expiration_formatted = exp_date.strftime("%m/%d/%Y")
        except:
            expiration_formatted = expiration
    else:
        expiration_formatted = "12/31/2025"
    
    # Render template
    html = render_template(
        "wefly_certificate.html",
        {
            "code": code,
            "simulator": simulator,
            "duration": duration,
            "gate": gate,
            "seat_class": seat_class,
            "expiration": expiration_formatted,
        },
    )
    
    convert_to_pdf(html, "out.pdf", "temp.html")
    
    if tasks:
        tasks.add_task(clean_temp_files)
    
    output_filename = os.path.join(OUTPUT_PATH, "out.pdf")
    return FileResponse(output_filename)
