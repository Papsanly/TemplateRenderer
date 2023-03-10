import asyncio
import os
import subprocess
import sys

from .config import CHROME_PATH, OUTPUT_PATH, RENDERER_PATH, TIME_BUDGET


def convert_to_pdf(html: str, filename: str):

    with open(f'{RENDERER_PATH}/templates/temp.html', 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_shell_command(filename)

    subprocess.run(
        shell_command,
        shell=not sys.platform.startswith('win32'),
        check=True
    )

    os.remove(f'{RENDERER_PATH}/templates/temp.html')


def get_shell_command(filename: str):

    if not os.path.exists(OUTPUT_PATH):
        raise FileNotFoundError('OUTPUT_PATH does not exist')

    args = [
        f'"{CHROME_PATH}"',
        '--headless',
        '--disable-gpu',
        '--no-margins',
        f'--virtual-time-budget={TIME_BUDGET}',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={OUTPUT_PATH}/{filename}.pdf',
        f'{RENDERER_PATH}/templates/temp.html'
    ]

    return ' '.join(args)


async def convert_to_pdf_async(html: str, filename: str):

    with open(f'{RENDERER_PATH}/templates/temp.html', 'w', encoding='utf-8') as f:
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

    os.remove(f'{RENDERER_PATH}/templates/temp.html')

    return stdout.decode().strip()
