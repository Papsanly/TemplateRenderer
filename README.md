# Template Renderer

Render jinja2 templates to PDF

# Prerequisites

- Python 3.10 or higher
- Chrome 60 or higher

# Usage

Configure your chrome executable path in `config.py`
```python
CHROME_PATH = 'your/path/to/chrome'
```

Output and templates path can also be configured in `config.py`.

Create and activate python virtual environment
```shell
python -m venv venv
source venv/bin/activate
```

Install dependencies
```shell
pip install -r requirements.txt
```

Run main.py
```shell
python main.py [-h] [-o] template [--context_values ...]
```

Example
```shell
python main.py -o result.pdf template_name --foo foo1 --bar bar2
```

# [Telegram Bot](https://core.telegram.org/bots/api)

The `bot` directory contains a simple telegram bot. 

The `/render` command will provide a user with a form to fill in the context values for the templates and will send the
rendered pdf file.