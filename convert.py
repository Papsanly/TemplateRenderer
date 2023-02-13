import os
import subprocess
import sys

from config import CHROME_PATH, OUTPUT_PATH, PROJECT_PATH, TIME_BUDGET


def convert_to_pdf(html: str, filename: str):

    with open('templates/temp.html', 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_shell_command(filename)

    subprocess.run(
        shell_command,
        shell=not sys.platform.startswith('win32'),
        check=True
    )

    os.remove('templates/temp.html')


def get_shell_command(filename: str):

    if not os.path.exists(OUTPUT_PATH):
        raise FileNotFoundError('OUTPUT_PATH does not exist')

    args = [
        CHROME_PATH,
        '--headless',
        '--disable-gpu',
        '--no-margins',
        f'--virtual-time-budget={TIME_BUDGET}',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={os.path.join(OUTPUT_PATH, filename)}.pdf',
        f'{PROJECT_PATH}/templates/temp.html'
    ]

    return ' '.join(args)
