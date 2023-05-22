from subprocess import CalledProcessError
from jinja2 import TemplateNotFound, TemplateRuntimeError
from args import parse
from renderer.template import render_template, get_context_keys, get_env
from renderer.convert import convert_to_pdf


def main():
    try:
        args = parse()
        if args.get_context:
            print(get_context_keys(get_env(), args.template))
        else:
            html = render_template(args.template, args.context_values)
            convert_to_pdf(html, args.output_file_name)
            print('Render Successful')
    except (ValueError, CalledProcessError, TemplateRuntimeError) as e:
        print(f'Error: {e}')
    except TemplateNotFound as e:
        print(f"Error: Template '{e}' not found")


if __name__ == '__main__':
    main()
