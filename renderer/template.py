from jinja2 import Environment, meta, TemplateNotFound, FileSystemLoader

from .config import TEMPLATE_PATH


def get_context_keys(parsed_content):
    template_variables = []
    for variable in parsed_content.body[0].nodes:
        if isinstance(variable, meta.nodes.Name):
            template_variables.append(variable.name)
    return template_variables


def validate_context(context_keys, context: dict[str, str]):
    notset_keys = set(context_keys) - set(context.keys())
    if notset_keys:
        raise ValueError(f"Not set context keys: {notset_keys}")


def render_template(template_name: str, context: dict[str, str]) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))

    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise TemplateNotFound(f'Template {e} not found')

    source = env.loader.get_source(env, template_name)[0]
    parsed_content = env.parse(source)
    context_keys = get_context_keys(parsed_content)

    validate_context(context_keys, context)

    return template.render(context)
