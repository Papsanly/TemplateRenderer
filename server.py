import os

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


@app.get("/")
async def generate_certificate(
    simulator: str, duration: str, code: str, print_template: bool, tasks: BackgroundTasks
):
    html = render_template(
        "print.html" if print_template else "variable_date.html",
        {"type": simulator, "duration": duration, "code": code},
    )
    print(html)
    convert_to_pdf(html, "out.pdf", "temp.html")
    tasks.add_task(clean_temp_files)
    output_filename = os.path.join(OUTPUT_PATH, "out.pdf")
    return FileResponse(output_filename)
