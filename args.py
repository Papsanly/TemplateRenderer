from argparse import ArgumentParser


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='python main.py',
        description='Render certificates for Aviasim',
        epilog='Rendered pdf file is saved as "out.pdf"'
    )
    parser.add_argument('template')
    parser.add_argument('context_values', nargs='*')
    return parser
