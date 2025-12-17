import asyncio
import os
import subprocess
import sys

from .config import CHROME_PATH, OUTPUT_PATH, TEMPLATE_PATH


def convert_to_pdf(html: str, out_basename: str, tmp_basename: str):
    tmp_filename = os.path.join(TEMPLATE_PATH, tmp_basename)
    out_filename = os.path.join(OUTPUT_PATH, out_basename)

    with open(tmp_filename, 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_pdf_command(out_filename, tmp_filename)

    subprocess.run(
        shell_command,
        shell=not sys.platform.startswith('win32'),
        check=True
    )

    os.remove(tmp_filename)


def convert_to_png(html: str, out_basename: str, tmp_basename: str):
    tmp_filename = os.path.join(TEMPLATE_PATH, tmp_basename)
    out_filename = os.path.join(OUTPUT_PATH, out_basename)

    with open(tmp_filename, 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_png_command(out_filename, tmp_filename)

    subprocess.run(
        shell_command,
        shell=not sys.platform.startswith('win32'),
        check=True
    )

    os.remove(tmp_filename)


def get_pdf_command(out_filename: str, tmp_filename: str) -> str:
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    if not CHROME_PATH:
        raise ValueError('CHROME_PATH not set')

    if not os.path.exists(CHROME_PATH):
        raise ValueError('CHROME_PATH does not exist')

    args = [
        f'"{CHROME_PATH}"',
        '--headless',
        '--no-sandbox',
        '--disable-gpu',
        '--no-margins',
        '--print-to-pdf-no-header',
        '--no-pdf-header-footer',
        '--paper-width=15.625',
        '--paper-height=6.25',
        '--virtual-time-budget=2000',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf="{out_filename}"',
        f'"{tmp_filename}"'
    ]

    return ' '.join(args)


def get_png_command(out_filename: str, tmp_filename: str) -> str:
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    if not CHROME_PATH:
        raise ValueError('CHROME_PATH not set')

    if not os.path.exists(CHROME_PATH):
        raise ValueError('CHROME_PATH does not exist')

    args = [
        f'"{CHROME_PATH}"',
        '--headless',
        '--no-sandbox',
        '--disable-gpu',
        '--window-size=1500,600',
        f'--screenshot="{out_filename}"',
        f'"{tmp_filename}"'
    ]

    return ' '.join(args)


async def convert_to_pdf_async(html: str, out_basename: str, tmp_basename: str) -> str:
    tmp_filename = os.path.join(TEMPLATE_PATH, tmp_basename)
    out_filename = os.path.join(OUTPUT_PATH, out_basename)

    with open(tmp_filename, 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_pdf_command(out_filename, tmp_filename)

    process = await asyncio.create_subprocess_shell(
        shell_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, shell_command, stderr=stderr)

    os.remove(tmp_filename)

    return stdout.decode().strip()


def merge_pdfs(front_pdf: str, back_pdf: str, output_pdf: str):
    from pypdf import PdfWriter

    writer = PdfWriter()

    if os.path.exists(front_pdf):
        writer.append(front_pdf)

    if os.path.exists(back_pdf):
        writer.append(back_pdf)

    writer.write(output_pdf)
    writer.close()

    if os.path.exists(front_pdf) and front_pdf != output_pdf:
        os.remove(front_pdf)
