from templates import get_template, render_template


def main():

    template = get_template()
    print(render_template(template))


if __name__ == '__main__':
    main()
