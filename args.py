from argparse import ArgumentParser


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='python main.py',
        description='Render jinja2 templates to PDF',
    )
    parser.add_argument('template')
    parser.add_argument('context_values', nargs='*')
    parser.add_argument('-o', default='out.pdf', dest='output_file_name')
    return parser


def parse():
    return get_parser().parse_args()
