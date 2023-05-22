from jinja2 import Environment, PackageLoader, meta, TemplateNotFound


def get_context_keys(parsed_content):
    template_variables = []
    for variable in parsed_content.body[0].nodes:
        if isinstance(variable, meta.nodes.Name):
            template_variables.append(variable.name)
    return template_variables


def render_template(template_name: str, context_values: list[str]) -> str:
    env = Environment(loader=PackageLoader('renderer'))

    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise TemplateNotFound(f'Template {e} not found')

    source = env.loader.get_source(env, template_name)[0]
    parsed_content = env.parse(source)
    context_keys = get_context_keys(parsed_content)

    if len(context_keys) != len(context_values):
        raise ValueError(f"'context_values' should contain {len(context_keys)} value(s)")

    return template.render(zip(context_keys, context_values))
