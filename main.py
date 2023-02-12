from subprocess import CalledProcessError

from args import parse
from templates import get_template, render_template
from convert import set_chrome_path, convert_to_pdf


def main():

    try:
        args = parse()
        if args.chrome_path is not None:
            set_chrome_path(args.chrome_path)
        template = get_template(args)
        html = render_template(template)
        convert_to_pdf(html)
    except (ValueError, CalledProcessError, FileNotFoundError) as e:
        print(f'An error occured: {e}')
    else:
        print('Render Successful')


if __name__ == '__main__':
    main()
