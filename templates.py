from dataclasses import dataclass


@dataclass
class Template:
    name: str
    context_keys: list[str]
    _context_values: list[str] = None

    @property
    def context(self):
        if self.context_values is None:
            raise ValueError("'context_values' not specified")
        return dict(zip(self.context_keys, self.context_values))

    @property
    def context_values(self) -> list[str] | None:
        return self._context_values

    @context_values.setter
    def context_values(self, value: list[str]):
        if len(value) != len(self.context_keys):
            raise ValueError(f"'context_values' should contain {len(self.context_keys)} value(s)")
        self._context_values = value

    @property
    def path_name(self):
        return f'templates/{self.name}.html'


def get_template(name: str) -> Template:

    result = [template for template in templates if template.name == name]
    if not result:
        raise ValueError('Template does not exist')
    elif len(result) != 1:
        raise ValueError('Templates name should be unique')

    return result[0]


templates = [
    Template(
        name='fixed_date',
        context_keys=['code', 'date', 'time']
    ),
    Template(
        name='variable_date',
        context_keys=['code']
    )
]
