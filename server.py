import base64
import os
from datetime import datetime
from urllib.parse import quote

import qrcode
from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse
from renderer.config import OUTPUT_PATH
from renderer.convert import convert_to_pdf, convert_to_png, merge_pdfs
from renderer.template import render_template

app = FastAPI()

ACTIVATION_URL = "https://wefly.aero/activate"


def is_formula1(simulator: str | None) -> bool:
    return "formula" in (simulator or "").lower()


def back_cover_a4_path(simulator: str | None = None) -> str:
    """The rules page differs for Formula 1, so each variant gets its own cached PDF."""
    name = "back_cover_a4_f1.pdf" if is_formula1(simulator) else "back_cover_a4.pdf"
    return os.path.join(OUTPUT_PATH, name)


def generate_back_cover_a4(simulator: str | None = None) -> str:
    path = back_cover_a4_path(simulator)
    gate = map_simulator_to_gate(simulator) if simulator else ""
    html = render_template("wefly_back_a4.html", {"gate": gate})
    convert_to_pdf(html, os.path.basename(path), "back_temp.html", a4=True)
    return path


def get_back_cover_a4(simulator: str | None = None) -> str:
    path = back_cover_a4_path(simulator)
    if not os.path.exists(path):
        generate_back_cover_a4(simulator)
    return path


@app.on_event("startup")
async def startup_event():
    # Always re-render on startup so a deploy never serves a back page from the previous design.
    generate_back_cover_a4()
    generate_back_cover_a4("formula1")


def clean_temp_files():
    for fname in ["temp.html", "front.pdf", "front_a4.pdf", "out.pdf", "front.png"]:
        path = os.path.join(OUTPUT_PATH, fname)
        if os.path.exists(path):
            os.remove(path)


def build_activation_url(code: str) -> str:
    """Link that opens the activation page with this gift code already filled in."""
    return f"{ACTIVATION_URL}/{quote(code.strip(), safe='')}"


def generate_qr_code(code: str) -> str:
    """QR code for the gift code's activation link, as an SVG data URI.

    Vector, so it stays sharp at any print size. The standard 4-module quiet zone is part of the
    image, so the code scans wherever a template places it.
    """
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(build_activation_url(code))
    qr.make(fit=True)
    matrix = qr.get_matrix()  # includes the quiet zone
    size = len(matrix)

    # One path of horizontal runs: a single fill leaves no hairline seams between modules.
    runs = []
    for y, row in enumerate(matrix):
        x = 0
        while x < size:
            if not row[x]:
                x += 1
                continue
            start = x
            while x < size and row[x]:
                x += 1
            runs.append(f"M{start} {y}h{x - start}v1h{start - x}z")

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'shape-rendering="crispEdges"><rect width="{size}" height="{size}" fill="#fff"/>'
        f'<path fill="#000" d="{"".join(runs)}"/></svg>'
    )
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


def map_simulator_to_gate(simulator: str) -> str:
    mapping = {
        "airbus320": "Airbus A320",
        "boeing737": "Boeing 737 MAX",
        "formula1": "Formula 1",
    }
    return mapping.get(simulator.lower(), simulator)


def map_duration_to_seat_class(duration: int) -> str:
    """Map current plans and legacy gift-card durations to their purchased class."""
    if duration == 30:
        return "Economy Class"
    elif duration in (50, 60):
        return "Business Class"
    elif duration in (110, 120):
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


def get_template_name(a4: bool = False) -> str:
    """One template per format; each switches its copy and artwork on the gate (simulator)."""
    return "wefly_certificate_a4.html" if a4 else "wefly_certificate.html"


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
    template = get_template_name(a4=False)
    html = render_template(template, params)
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
    template = get_template_name(a4=True)
    html_front = render_template(template, params)
    convert_to_pdf(html_front, "front_a4.pdf", "temp.html", a4=True)

    front_path = os.path.join(OUTPUT_PATH, "front_a4.pdf")
    output_path = os.path.join(OUTPUT_PATH, "out.pdf")

    # Merge front + back A4
    merge_pdfs(front_path, get_back_cover_a4(simulator), output_path)

    if tasks:
        tasks.add_task(clean_temp_files)

    return FileResponse(
        output_path, filename="WeFly-Gift-Card.pdf", media_type="application/pdf"
    )


@app.get("/a4-single")
async def generate_certificate_a4_single(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
    tasks: BackgroundTasks = None,
):
    """Generate single-page A4 PDF (for physical gift cards, no back cover)"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)

    # Generate front A4 only (no back page)
    template = get_template_name(a4=True)
    html_front = render_template(template, params)
    convert_to_pdf(html_front, "front_a4.pdf", "temp.html", a4=True)

    front_path = os.path.join(OUTPUT_PATH, "front_a4.pdf")

    if tasks:
        tasks.add_task(clean_temp_files)

    return FileResponse(
        front_path, filename="WeFly-Gift-Card.pdf", media_type="application/pdf"
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
    template = get_template_name(a4=False)
    html = render_template(template, params)
    convert_to_png(html, "front.png", "temp.html")

    front_path = os.path.join(OUTPUT_PATH, "front.png")

    if tasks:
        tasks.add_task(clean_temp_files)

    return FileResponse(
        front_path, filename="WeFly-Gift-Card.png", media_type="image/png"
    )


@app.get("/back")
async def get_back_cover(simulator: str = None):
    """Get static back cover A4 PDF (pass simulator=formula1 for the racing rules)"""
    return FileResponse(
        get_back_cover_a4(simulator), filename="WeFly-Back.pdf", media_type="application/pdf"
    )
