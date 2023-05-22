from subprocess import CalledProcessError

from args import parse
from renderer.template import render_template
from renderer.convert import convert_to_pdf


def main():
    try:
        args = parse()
        html = render_template(f'{args.template}.html', args.context_values)
        convert_to_pdf(html, args.output_file_name)
    except (ValueError, CalledProcessError, FileNotFoundError) as e:
        print(f'An error occured: {e}')
    else:
        print('Render Successful')


if __name__ == '__main__':
    main()
