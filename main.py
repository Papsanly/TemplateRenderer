from args import parse
from templates import get_template, render_template
from convert import convert_to_pdf


def main():

    try:
        args = parse()
        template = get_template(args)
        html = render_template(template)
        convert_to_pdf(html)
    except ValueError as e:
        print(f'An error occured: {e}')


if __name__ == '__main__':
    main()
