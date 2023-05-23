import glob
from dataclasses import dataclass

from jinja2 import Environment, meta, FileSystemLoader, TemplateRuntimeError
from .config import TEMPLATE_PATH


@dataclass
class TemplateVarFilter:
    name: str
    args: list


@dataclass
class TemplateVar:
    name: str
    filter: TemplateVarFilter | None


TEMPLATES = glob.glob(TEMPLATE_PATH + '/*.html')
env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))


def get_context_keys(template_name: str) -> list[TemplateVar]:
    source = env.loader.get_source(env, template_name)[0]
    body = env.parse(source).body[0]
    template_variables = []
    if hasattr(body, 'nodes'):
        for variable in body.nodes:
            if isinstance(variable, meta.nodes.Name):
                template_variables.append(TemplateVar(name=variable.name, filter=None))
            elif isinstance(variable, meta.nodes.Filter) and isinstance(variable.node, meta.nodes.Name):
                template_variables.append(TemplateVar(
                    name=variable.node.name,
                    filter=TemplateVarFilter(variable.name, variable.args)
                ))
    return template_variables


def validate_context(context_keys: list[TemplateVar], context: dict[str, str]):
    notset_keys = set([key.name for key in context_keys]) - context.keys()
    if notset_keys:
        raise ValueError(f"Not set context keys: {notset_keys}")


def limit_to(value: str, *allowed) -> str:
    if value in allowed:
        return value
    else:
        raise TemplateRuntimeError(
            f"Variable to which you passed value '{value}' can only be one of these: {allowed}"
        )


def render_template(template_name: str, context: dict[str, str]) -> str:
    env.filters['limit_to'] = limit_to
    template = env.get_template(template_name)
    context_keys = get_context_keys(template_name)
    validate_context(context_keys, context)
    return template.render(context)
