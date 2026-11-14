import base64
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import quote

import qrcode
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
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


@contextmanager
def request_files():
    """A folder under the output path and an HTML file name that belong to one request.

    Two people can buy a gift in the same second. With shared names (temp.html, front.pdf,
    out.pdf) and a clean-up after each response, one request deleted or overwrote the file the
    other was about to send: a download cut short, or somebody else's code on the gift card.
    The folder is removed when the block ends, so the caller reads the result inside it.
    """
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUTPUT_PATH) as folder:
        name = os.path.basename(folder)
        yield name, f"temp-{name}.html"


def download(path: str, filename: str, media_type: str) -> Response:
    """The file as a response that no longer needs it on disk."""
    with open(path, "rb") as f:
        content = f.read()
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content, media_type=media_type, headers=headers)


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
):
    """Generate front certificate only (original size)"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)
    template = get_template_name(a4=False)
    html = render_template(template, params)

    with request_files() as (folder, temp_html):
        front = os.path.join(folder, "front.pdf")
        convert_to_pdf(html, front, temp_html, a4=False)
        return download(
            os.path.join(OUTPUT_PATH, front), "WeFly-Gift-Card.pdf", "application/pdf"
        )


@app.get("/a4")
async def generate_certificate_a4(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
):
    """Generate 2-page A4 PDF (front + back) for printing"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)
    template = get_template_name(a4=True)
    html_front = render_template(template, params)

    with request_files() as (folder, temp_html):
        front = os.path.join(folder, "front_a4.pdf")
        convert_to_pdf(html_front, front, temp_html, a4=True)

        # Merge front + back A4
        output_path = os.path.join(OUTPUT_PATH, folder, "out.pdf")
        merge_pdfs(os.path.join(OUTPUT_PATH, front), get_back_cover_a4(simulator), output_path)
        return download(output_path, "WeFly-Gift-Card.pdf", "application/pdf")


@app.get("/a4-single")
async def generate_certificate_a4_single(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
):
    """Generate single-page A4 PDF (for physical gift cards, no back cover)"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)

    # Generate front A4 only (no back page)
    template = get_template_name(a4=True)
    html_front = render_template(template, params)

    with request_files() as (folder, temp_html):
        front = os.path.join(folder, "front_a4.pdf")
        convert_to_pdf(html_front, front, temp_html, a4=True)
        return download(
            os.path.join(OUTPUT_PATH, front), "WeFly-Gift-Card.pdf", "application/pdf"
        )


@app.get("/png")
async def generate_certificate_png(
    simulator: str,
    duration: str,
    code: str,
    expiration: str = None,
    is_birthday: bool = False,
):
    """Generate front certificate as PNG (1500x600, for physical gift cards)"""
    params = get_template_params(simulator, duration, code, expiration, is_birthday)

    # Use original 1500x600 template for PNG
    template = get_template_name(a4=False)
    html = render_template(template, params)

    with request_files() as (folder, temp_html):
        front = os.path.join(folder, "front.png")
        convert_to_png(html, front, temp_html)
        return download(
            os.path.join(OUTPUT_PATH, front), "WeFly-Gift-Card.png", "image/png"
        )


@app.get("/back")
async def get_back_cover(simulator: str = None):
    """Get static back cover A4 PDF (pass simulator=formula1 for the racing rules)"""
    return FileResponse(
        get_back_cover_a4(simulator), filename="WeFly-Back.pdf", media_type="application/pdf"
    )
