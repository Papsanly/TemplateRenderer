import sys


def parse_arguments() -> tuple[str, tuple[str, ...]]:
    template = sys.argv[1]
    if template not in ('fixed_date', 'variable_date'):
        raise ValueError("Template can only be 'fixed_date' or 'variable_date'")

    template_args = tuple(sys.argv[2:])
    if template == 'fixed_date' and len(template_args) != 1:
        raise ValueError("Template 'fixed_date' requires 1 argument: code")
    elif template == 'variable_date' and len(template_args) != 3:
        raise ValueError("Template 'variable_date' requires 3 arguments: code, date, time")

    return template, template_args


def main():
    try:
        template, template_args = parse_arguments()
    except ValueError as e:
        print(f'An error occured: {e}')



if __name__ == '__main__':
    main()
