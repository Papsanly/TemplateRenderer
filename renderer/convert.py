import asyncio
import os
import subprocess
import sys

from .config import CHROME_PATH, OUTPUT_PATH, TEMPLATE_PATH


def convert_to_pdf(html: str, out_basename: str, tmp_basename: str, a4: bool = False):
    tmp_filename = os.path.join(TEMPLATE_PATH, tmp_basename)
    out_filename = os.path.join(OUTPUT_PATH, out_basename)

    with open(tmp_filename, "w", encoding="utf-8") as f:
        f.write(html)

    shell_command = get_pdf_command(out_filename, tmp_filename, a4)

    subprocess.run(
        shell_command, shell=not sys.platform.startswith("win32"), check=True
    )

    os.remove(tmp_filename)


def convert_to_png(html: str, out_basename: str, tmp_basename: str):
    """Convert HTML to PNG using Chrome headless screenshot (1500x600 native size)"""
    tmp_filename = os.path.join(TEMPLATE_PATH, tmp_basename)
    out_filename = os.path.join(OUTPUT_PATH, out_basename)

    with open(tmp_filename, "w", encoding="utf-8") as f:
        f.write(html)

    shell_command = get_png_command(out_filename, tmp_filename)

    subprocess.run(
        shell_command, shell=not sys.platform.startswith("win32"), check=True
    )

    os.remove(tmp_filename)


async def convert_to_pdf_async(
    html: str, out_basename: str, tmp_basename: str, a4: bool = False
):
    tmp_filename = os.path.join(TEMPLATE_PATH, tmp_basename)
    out_filename = os.path.join(OUTPUT_PATH, out_basename)

    with open(tmp_filename, "w", encoding="utf-8") as f:
        f.write(html)

    shell_command = get_pdf_command(out_filename, tmp_filename, a4)

    process = await asyncio.create_subprocess_shell(
        shell_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

    os.remove(tmp_filename)


def get_pdf_command(out_filename: str, tmp_filename: str, a4: bool = False) -> str:
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    if not CHROME_PATH:
        raise ValueError("CHROME_PATH not set")

    if not os.path.exists(CHROME_PATH):
        raise ValueError("CHROME_PATH does not exist")

    if a4:
        paper_width = "8.27"
        paper_height = "11.69"
    else:
        # Custom: 1500px / 96dpi = 15.625 inches, 600px / 96dpi = 6.25 inches
        paper_width = "15.625"
        paper_height = "6.25"

    args = [
        f'"{CHROME_PATH}"',
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--no-margins",
        "--print-to-pdf-no-header",
        "--no-pdf-header-footer",
        f"--paper-width={paper_width}",
        f"--paper-height={paper_height}",
        "--virtual-time-budget=2000",
        "--run-all-compositor-stages-before-draw",
        f'--print-to-pdf="{out_filename}"',
        f'"{tmp_filename}"',
    ]

    return " ".join(args)


def get_png_command(out_filename: str, tmp_filename: str) -> str:
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    if not CHROME_PATH:
        raise ValueError("CHROME_PATH not set")

    if not os.path.exists(CHROME_PATH):
        raise ValueError("CHROME_PATH does not exist")

    # Native template size: 1500x600px
    # Add small buffer for rendering
    args = [
        f'"{CHROME_PATH}"',
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--window-size=1500,600",
        "--hide-scrollbars",
        "--default-background-color=00000000",
        "--virtual-time-budget=2000",
        "--run-all-compositor-stages-before-draw",
        f'--screenshot="{out_filename}"',
        f'"{tmp_filename}"',
    ]

    return " ".join(args)


def merge_pdfs(front_pdf: str, back_pdf: str, output_pdf: str):
    from pypdf import PdfWriter

    writer = PdfWriter()

    if os.path.exists(front_pdf):
        writer.append(front_pdf)

    if os.path.exists(back_pdf):
        writer.append(back_pdf)

    writer.write(output_pdf)
    writer.close()
