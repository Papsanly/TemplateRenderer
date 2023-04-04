from subprocess import CalledProcessError

from args import parse
from renderer.templates import get_template, render_template
from renderer.convert import convert_to_pdf


def main():

    try:
        args = parse()
        template = get_template(args.template, args.context_values)
        html = render_template(template)
        convert_to_pdf(html, args.context_values[1])
    except (ValueError, CalledProcessError, FileNotFoundError) as e:
        print(f'An error occured: {e}')
    else:
        print('Render Successful')


if __name__ == '__main__':
    main()
