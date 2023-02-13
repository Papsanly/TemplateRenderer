import os
import subprocess
import sys

from config import CHROME_PATH, OUTPUT_PATH, PROJECT_PATH


def convert_to_pdf(html: str, filename: str):

    with open('templates/temp.html', 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_shell_command(CHROME_PATH, filename)

    subprocess.run(
        shell_command,
        shell=not sys.platform.startswith('win32'),
        check=True
    )

    os.remove('templates/temp.html')


def get_shell_command(chrome_path: str, filename: str):

    args = [
        chrome_path,
        '--headless',
        '--disable-gpu',
        '--no-margins',
        f'--print-to-pdf={OUTPUT_PATH}/{filename}.pdf',
        f'{PROJECT_PATH}/templates/temp.html'
    ]

    return ' '.join(args)
