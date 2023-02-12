import json
import os
import subprocess
import sys


def convert_to_pdf(html: str):
    with open('config.json', 'r') as f:
        chrome_path = json.load(f)['chrome_path']

    with open('templates/temp.html', 'w', encoding='utf-8') as f:
        f.write(html)

    shell_command = get_shell_command(chrome_path)

    subprocess.run(
        shell_command,
        shell=not sys.platform.startswith('win32'),
        check=True
    )

    os.remove('templates/temp.html')


def get_shell_command(chrome_path):

    abspath = os.path.dirname(os.path.abspath(__file__))

    args = [
        chrome_path,
        '--headless',
        '--disable-gpu',
        '--no-margins',
        f'--print-to-pdf={abspath}/out.pdf',
        f'{abspath}/templates/temp.html'
    ]

    return ' '.join(args)
