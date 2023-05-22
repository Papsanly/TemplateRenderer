from argparse import ArgumentParser


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='python main.py',
        description='Render jinja2 templates to PDF',
    )
    parser.add_argument('template')
    parser.add_argument('-o', default='out.pdf', dest='output_file_name')
    return parser


def parse():
    parser = get_parser()
    args, remaining_args = parser.parse_known_args()
    args.context_values = {
        remaining_args[i][2:]: remaining_args[i + 1]
        for i in range(0, len(remaining_args), 2)
    }

    return args
