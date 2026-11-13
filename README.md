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
python main.py [-h] [-o] template <context key-value pairs ...>
```

Example
```shell
python main.py -o result.pdf template_name.html --ctx_key1 ctx_val1 --ctx_key2 ctx_val2
```

You can also see context keys required for a template with `--ctx` argument
```shell
python main.py template_name.html --ctx
```

# WeFly gift card server

`server.py` renders the gift card wefly.aero attaches to gift emails. Every endpoint takes
`code`, `simulator`, `duration`, and optionally `expiration` (ISO date) and `is_birthday`.

| Endpoint | Output | Templates |
| --- | --- | --- |
| `/a4` | 2-page A4 PDF: card + simulator rules | `wefly_certificate_a4.html`, `wefly_back_a4.html` |
| `/a4-single` | A4 PDF, card page only | `wefly_certificate_a4.html` |
| `/back` | A4 PDF, rules page only (`?simulator=formula1` for the racing rules) | `wefly_back_a4.html` |
| `/` | 1500x600 PDF of the boarding pass | `wefly_certificate.html` |
| `/png` | 1500x600 PNG of the boarding pass | `wefly_certificate.html` |

One template per format serves all simulators: the copy, photo and artwork switch on the gate, so
a Formula 1 code gets the racing version. The QR code links to
`https://wefly.aero/activate/<code>`. Shared styles live in
`renderer/templates/partials/wefly_gift.css`; the Manrope font and the photos are bundled under
`renderer/templates/`, so rendering needs no network access.

Run it locally by pointing `CHROME_PATH` at your Chrome:
```shell
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" fastapi dev server.py
python -m unittest test_seat_classes test_gift_card
```

`python scripts/switch_theme.py christmas|default` turns the Christmas greeting on the pass on
and off.

# [Telegram Bot](https://core.telegram.org/bots/api)

The `bot` directory contains a simple telegram bot. 

Provides user with a form to fill in the context values for the templates and sends the rendered
pdf file.

To run the bot reset CHROME_PATH to default value. Then build and run the docker image:
```shell
docker build -t bot:latest .
docker run --name bot --env BOT_TOKEN=<your:bot-token> bot:latest
```
