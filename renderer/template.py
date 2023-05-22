from jinja2 import Environment, PackageLoader, meta


def get_context_keys(parsed_content):
    template_variables = []
    for variable in parsed_content.body[0].nodes:
        if isinstance(variable, meta.nodes.Name):
            template_variables.append(variable.name)
    return template_variables


def render_template(template_name: str, context_values: list[str]) -> str:
    env = Environment(loader=PackageLoader('renderer'))
    template = env.get_template(template_name)
    source = env.loader.get_source(env, template_name)[0]
    parsed_content = env.parse(source)
    context_keys = get_context_keys(parsed_content)
    return template.render(zip(context_keys, context_values))
