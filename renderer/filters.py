from jinja2 import TemplateRuntimeError


def limit_to(value: str, *allowed: str) -> str:
    if value in allowed:
        return value
    else:
        raise TemplateRuntimeError
