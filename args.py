from argparse import ArgumentParser


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='python main.py',
        description='Render certificates for Aviasim',
    )
    parser.add_argument('template')
    parser.add_argument('context_values', nargs='*')
    parser.add_argument('--chrome-path', dest='chrome_path', required=False)
    return parser


def parse():
    return get_parser().parse_args()
