import asyncio
import os
import subprocess
import sys

from .config import CHROME_PATH, OUTPUT_PATH, TEMPLATE_PATH

TEMP_FILE_NAME = os.path.join(TEMPLATE_PATH, 'temp.html')


def convert_to_pdf(html: str, filename: str):

    with open(TEMP_FILE_NAME, 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_shell_command(filename)

    subprocess.run(
        shell_command,
        shell=not sys.platform.startswith('win32'),
        check=True
    )

    os.remove(TEMP_FILE_NAME)


def get_shell_command(filename: str):

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    args = [
        f'"{CHROME_PATH}"',
        '--headless',
        '--disable-gpu',
        '--no-margins',
        f'--virtual-time-budget=1000',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={os.path.join(OUTPUT_PATH, filename)}',
        f'{TEMP_FILE_NAME}'
    ]

    return ' '.join(args)


async def convert_to_pdf_async(html: str, filename: str):

    with open(TEMP_FILE_NAME, 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_shell_command(filename)

    process = await asyncio.create_subprocess_shell(
        shell_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, shell_command, stderr=stderr)

    os.remove(TEMP_FILE_NAME)

    return stdout.decode().strip()
