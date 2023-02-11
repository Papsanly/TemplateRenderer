from argparse import ArgumentParser
from templates import get_template


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='python main.py',
        description='Render certificates for Aviasim',
        epilog='Rendered pdf file is saved as "out.pdf"'
    )
    parser.add_argument('template')
    parser.add_argument('context_values', nargs='*')
    return parser


def main():
    args = get_parser().parse_args()

    try:
        template = get_template(args.template)
        template.context_values = args.context_values
    except ValueError as e:
        print(f'An error occured: {e}')
    else:
        print(template)


if __name__ == '__main__':
    main()
