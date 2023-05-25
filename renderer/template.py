import glob
from dataclasses import dataclass
from typing import Callable

from jinja2 import Environment, meta, FileSystemLoader, TemplateRuntimeError

from config import TEMPLATE_PATH
import filters


@dataclass
class TemplateVarFilter:
    name: Callable
    args: list[str]

    def __init__(self, name: str, args: list[str]):
        self.args = args
        self.name = getattr(filters, name)


@dataclass
class TemplateVar:
    name: str
    filter: TemplateVarFilter | None

    def is_valid(self, value) -> bool:
        if not self.filter:
            return True
        try:
            self.filter.name(value, *self.filter.args)
        except TemplateRuntimeError:
            return False
        else:
            return True


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
                    filter=TemplateVarFilter(variable.name, list(map(lambda x: str(x.value), variable.args)))
                ))
    return template_variables


def validate_context(context_keys: list[TemplateVar], context: dict[str, str]):
    notset_keys = set([key.name for key in context_keys]) - context.keys()
    if notset_keys:
        raise ValueError(f"Not set context keys: {notset_keys}")

    for key, value in zip(context_keys, context.values()):
        if not key.is_valid(value):
            if key.filter.name == filters.limit_to:
                raise ValueError(f"Variable '{key.name}' can only be one of these: {key.filter.args}")


def register_filters():
    env.filters['limit_to'] = filters.limit_to


def render_template(template_name: str, context: dict[str, str]) -> str:
    register_filters()
    template = env.get_template(template_name)
    context_keys = get_context_keys(template_name)
    validate_context(context_keys, context)
    return template.render(context)
