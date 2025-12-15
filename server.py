import os
import qrcode
import base64
from io import BytesIO
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse

from renderer.config import OUTPUT_PATH
from renderer.template import render_template
from renderer.convert import convert_to_pdf

app = FastAPI()

BACK_COVER_PATH = os.path.join(OUTPUT_PATH, "back_cover.pdf")


def generate_back_cover():
    # Always regenerate to pick up template changes
    html = render_template("wefly_back.html", {})
    convert_to_pdf(html, "back_cover.pdf", "back_temp.html")


@app.on_event("startup")
async def startup_event():
    generate_back_cover()


def clean_temp_files():
    for fname in ["temp.html", "front.pdf"]:
        path = os.path.join(OUTPUT_PATH, fname)
        if os.path.exists(path):
            os.remove(path)


def generate_qr_code(code: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(f"https://wefly.aero/activate/{code}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"


def map_simulator_to_gate(simulator: str) -> str:
    mapping = {"airbus320": "Airbus A320", "boeing737": "Boeing 737 MAX", "formula1": "Formula 1"}
    return mapping.get(simulator.lower(), simulator)


def map_duration_to_seat_class(duration: int) -> str:
    if duration == 30: return "Economy Class"
    elif duration == 60: return "Business Class"
    elif duration == 120: return "First Class"
    return "Economy Class"


@app.get("/")
async def generate_certificate(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
    tasks: BackgroundTasks = None
):
    """Generate front certificate only"""
    duration_int = int(duration)
    gate = map_simulator_to_gate(simulator)
    seat_class = map_duration_to_seat_class(duration_int)
    qr_code_data = generate_qr_code(code)

    if expiration:
        try:
            exp_date = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
            expiration_formatted = exp_date.strftime("%m/%d/%Y")
        except:
            expiration_formatted = expiration
    else:
        expiration_formatted = "12/31/2025"

    html = render_template(
        "wefly_certificate.html",
        {"code": code, "simulator": simulator, "duration": duration, "gate": gate,
         "seat_class": seat_class, "expiration": expiration_formatted,
         "qr_code": qr_code_data, "is_birthday": is_birthday},
    )

    convert_to_pdf(html, "front.pdf", "temp.html")
    front_path = os.path.join(OUTPUT_PATH, "front.pdf")

    if tasks:
        tasks.add_task(clean_temp_files)

    return FileResponse(front_path, filename="WeFly-Gift-Card.pdf", media_type="application/pdf")


@app.get("/back")
async def get_back_cover():
    """Get static back cover"""
    if not os.path.exists(BACK_COVER_PATH):
        generate_back_cover()
    return FileResponse(BACK_COVER_PATH, filename="WeFly-Back.pdf", media_type="application/pdf")
