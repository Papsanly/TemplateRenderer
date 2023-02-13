from dataclasses import dataclass
from django.template import Context, Engine

from config import TEMPLATES


@dataclass
class TemplateConfig:
    name: str
    context_keys: list[str]
    _context_values: list[str] = None

    @property
    def context(self):
        if self.context_values is None:
            raise ValueError("'context_values' not specified")
        return Context(dict(zip(self.context_keys, self.context_values)))

    @property
    def context_values(self) -> list[str] | None:
        return self._context_values

    @context_values.setter
    def context_values(self, value: list[str]):
        if len(value) != len(self.context_keys):
            raise ValueError(f"'context_values' should contain {len(self.context_keys)} value(s)")
        self._context_values = value

    @property
    def filename(self):
        return f'{self.name}.html'


def load_templates_config():
    return [TemplateConfig(**template_config) for template_config in TEMPLATES]


def find_template(name: str) -> TemplateConfig:

    result = [template for template in load_templates_config() if template.name == name]
    if not result:
        raise ValueError('Template does not exist')
    elif len(result) != 1:
        raise ValueError('Template names should be unique')

    return result[0]


def get_template(args) -> TemplateConfig:
    template = find_template(args.template)
    template.context_values = args.context_values
    return template


def render_template(template: TemplateConfig) -> str:
    template_engine = Engine(dirs=['templates'])
    django_template = template_engine.get_template(template.filename)
    html = django_template.render(template.context)
    return html
