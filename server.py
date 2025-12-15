import os
import qrcode
import base64
from io import BytesIO
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse

from renderer.config import OUTPUT_PATH
from renderer.template import render_template
from renderer.convert import convert_to_pdf, merge_pdfs

app = FastAPI()

# Path to WeFlyBack.pdf
BACK_COVER_PATH = os.path.join(os.path.dirname(__file__), 'WeFlyBack.pdf')


def clean_temp_files():
    temp_filename = os.path.join(OUTPUT_PATH, "temp.html")
    output_filename = os.path.join(OUTPUT_PATH, "out.pdf")
    front_filename = os.path.join(OUTPUT_PATH, "front.pdf")
    
    for filename in [temp_filename, output_filename, front_filename]:
        if os.path.exists(filename):
            os.remove(filename)


def generate_qr_code(code: str) -> str:
    """Generate QR code as base64 data URI"""
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(f"https://wefly.aero/activate/{code}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    return f"data:image/png;base64,{img_base64}"


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
    occasion: str = "christmas",
    tasks: BackgroundTasks = None
):
    # Convert duration to int
    duration_int = int(duration)
    
    # Map values
    gate = map_simulator_to_gate(simulator)
    seat_class = map_duration_to_seat_class(duration_int)
    
    # Generate QR code
    qr_code_data = generate_qr_code(code)
    
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
            "qr_code": qr_code_data,
            "occasion": occasion
        },
    )
    
    # Generate front page PDF
    front_filename = os.path.join(OUTPUT_PATH, "front.pdf")
    convert_to_pdf(html, "front.pdf", "temp.html")
    
    # Merge with back cover if exists
    output_filename = os.path.join(OUTPUT_PATH, "out.pdf")
    if os.path.exists(BACK_COVER_PATH):
        merge_pdfs(front_filename, BACK_COVER_PATH, output_filename)
    else:
        # If back cover doesn't exist, just rename front to out
        os.rename(front_filename, output_filename)
    
    if tasks:
        tasks.add_task(clean_temp_files)
    
    return FileResponse(output_filename, filename="WeFly-Gift-Card.pdf", media_type="application/pdf")
