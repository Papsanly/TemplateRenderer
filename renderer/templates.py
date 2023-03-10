from dataclasses import dataclass
from django.template import Context, Engine

from .config import TEMPLATES, RENDERER_PATH


@dataclass
class TemplateConfig:
    name: str
    context_keys: list[str | tuple[str, list[str]]]
    _context_values: list[str] = None

    @property
    def context(self):
        if self.context_values is None:
            raise ValueError("'context_values' not specified")
        return Context(dict([
            (key[0] if isinstance(key, tuple) else key, value)
            for key, value in zip(self.context_keys, self.context_values)
        ]))

    @property
    def context_values(self) -> list[str] | None:
        return self._context_values

    @context_values.setter
    def context_values(self, value: list[str]):
        if len(value) != len(self.context_keys):
            raise ValueError(f"'context_values' should contain {len(self.context_keys)} value(s)")

        for context_value, context_key in zip(value, self.context_keys):
            if isinstance(context_key, tuple):
                possible_values = context_key[1]
                if context_value not in possible_values:
                    raise ValueError(f"Context value '{context_key[0]}' should only be one of these: {possible_values}")

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


def get_template(template, context_values) -> TemplateConfig:
    template = find_template(template)
    template.context_values = context_values
    return template


def render_template(template: TemplateConfig) -> str:
    template_engine = Engine(dirs=[f'{RENDERER_PATH}/templates'])
    django_template = template_engine.get_template(template.filename)
    html = django_template.render(template.context)
    return html
