import base64
import os
from datetime import datetime
from io import BytesIO

import qrcode
from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse
from renderer.config import OUTPUT_PATH
from renderer.convert import convert_to_pdf, convert_to_png, merge_pdfs
from renderer.template import render_template

app = FastAPI()

BACK_COVER_A4_PATH = os.path.join(OUTPUT_PATH, "back_cover_a4.pdf")


def generate_back_cover_a4():
    html = render_template("wefly_back_a4.html", {})
    convert_to_pdf(html, "back_cover_a4.pdf", "back_temp.html", a4=True)


@app.on_event("startup")
async def startup_event():
    generate_back_cover_a4()


def clean_temp_files():
    for fname in ["temp.html", "front.pdf", "front_a4.pdf", "out.pdf", "front.png"]:
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
    mapping = {
        "airbus320": "Airbus A320",
        "boeing737": "Boeing 737 MAX",
        "formula1": "Formula 1",
    }
    return mapping.get(simulator.lower(), simulator)


def map_duration_to_seat_class(duration: int) -> str:
    if duration == 30:
        return "Economy Class"
    elif duration == 60:
        return "Business Class"
    elif duration == 120:
        return "First Class"
    return "Economy Class"


def get_template_params(
    simulator: str, duration: str, code: str, expiration: str, is_birthday: bool
):
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

    return {
        "code": code,
        "simulator": simulator,
        "duration": duration,
        "gate": gate,
        "seat_class": seat_class,
        "expiration": expiration_formatted,
        "qr_code": qr_code_data,
        "is_birthday": is_birthday,
    }


@app.get("/")
async def generate_certificate(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
    tasks: BackgroundTasks = None,
):
    """Generate front certificate only (original size)"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)
    html = render_template("wefly_certificate.html", params)
    convert_to_pdf(html, "front.pdf", "temp.html", a4=False)

    front_path = os.path.join(OUTPUT_PATH, "front.pdf")

    if tasks:
        tasks.add_task(clean_temp_files)

    return FileResponse(
        front_path, filename="WeFly-Gift-Card.pdf", media_type="application/pdf"
    )


@app.get("/a4")
async def generate_certificate_a4(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
    tasks: BackgroundTasks = None,
):
    """Generate 2-page A4 PDF (front + back) for printing"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)

    # Generate front A4
    html_front = render_template("wefly_certificate_a4.html", params)
    convert_to_pdf(html_front, "front_a4.pdf", "temp.html", a4=True)

    front_path = os.path.join(OUTPUT_PATH, "front_a4.pdf")
    output_path = os.path.join(OUTPUT_PATH, "out.pdf")

    # Merge front + back A4
    merge_pdfs(front_path, BACK_COVER_A4_PATH, output_path)

    if tasks:
        tasks.add_task(clean_temp_files)

    return FileResponse(
        output_path, filename="WeFly-Gift-Card.pdf", media_type="application/pdf"
    )


@app.get("/png")
async def generate_certificate_png(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
    tasks: BackgroundTasks = None,
):
    """Generate front certificate as PNG (1500x600, for physical gift cards)"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)

    # Use original 1500x600 template for PNG
    html = render_template("wefly_certificate.html", params)
    convert_to_png(html, "front.png", "temp.html")

    front_path = os.path.join(OUTPUT_PATH, "front.png")

    if tasks:
        tasks.add_task(clean_temp_files)

    return FileResponse(
        front_path, filename="WeFly-Gift-Card.png", media_type="image/png"
    )


@app.get("/back")
async def get_back_cover():
    """Get static back cover A4 PDF"""
    if not os.path.exists(BACK_COVER_A4_PATH):
        generate_back_cover_a4()
    return FileResponse(
        BACK_COVER_A4_PATH, filename="WeFly-Back.pdf", media_type="application/pdf"
    )
