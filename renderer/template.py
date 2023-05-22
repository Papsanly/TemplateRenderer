from jinja2 import Environment, meta, FileSystemLoader, TemplateRuntimeError

from .config import TEMPLATE_PATH


def get_env() -> Environment:
    return Environment(loader=FileSystemLoader(TEMPLATE_PATH))


def get_context_keys(env: Environment, template_name: str) -> list[str]:
    source = env.loader.get_source(env, template_name)[0]
    body = env.parse(source).body[0]
    template_variables = []
    if hasattr(body, 'nodes'):
        for variable in body.nodes:
            if isinstance(variable, meta.nodes.Name):
                template_variables.append(variable.name)
            elif isinstance(variable, meta.nodes.Filter) and isinstance(variable.node, meta.nodes.Name):
                template_variables.append(variable.node.name)
    return template_variables


def validate_context(context_keys: list[str], context: dict[str, str]):
    notset_keys = set(context_keys) - context.keys()
    if notset_keys:
        raise ValueError(f"Not set context keys: {notset_keys}")


def limit_to(value: str, *allowed) -> str:
    if value in allowed:
        return value
    else:
        raise TemplateRuntimeError('undefined error')


def render_template(template_name: str, context: dict[str, str]) -> str:
    env = get_env()
    env.filters['limit_to'] = limit_to
    template = env.get_template(template_name)
    context_keys = get_context_keys(env, template_name)
    validate_context(context_keys, context)
    return template.render(context)
