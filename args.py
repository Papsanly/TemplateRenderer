from argparse import ArgumentParser, Namespace


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='python main.py',
        description='Render jinja2 templates to PDF',
    )
    parser.add_argument('template')
    parser.add_argument('-o', default='out.pdf', dest='output_file_name')
    parser.add_argument('--ctx', required=False, dest='get_context', action='store_true')

    return parser


def parse() -> Namespace:
    parser = get_parser()
    args, remaining_args = parser.parse_known_args()

    if len(remaining_args) % 2:
        raise ValueError('Invalid arguments')

    args.context_values = {}
    for i in range(0, len(remaining_args), 2):
        arg_key = remaining_args[i]
        arg_value = remaining_args[i + 1]
        if arg_key[:2] != '--':
            raise ValueError('Invalid arguments')
        args.context_values[arg_key[2:]] = arg_value

    return args
