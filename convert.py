import os
import webbrowser


def convert_to_pdf(html: str):

    with open('templates/temp.html', 'w', encoding='utf-8') as f:
        f.write(html)

    webbrowser.open(f'file:///{os.path.abspath("templates/temp.html")}')
