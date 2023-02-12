# Certificate Renderer

Render certificates for Aviasim

# Prerequisites

- Python version >3.10
- Chrome version >60

# Usage

Create and activate python virtual environment
```shell
python -m venv venv
venv\Scripts\activate
```

Install dependencies
```shell
pip install -r requirements.txt
```

Run main.py
```shell
python main.py [--chrome-path CHROME_PATH] template [context_values ...]
```

`--chrome-path` - Optional argument to set path to your chrome executable, if it doesn't match path specified in 
`config.json`. You don't need to use this multiple times

`template` - Template to use. All templates available are listed in `config.json`

`context_values` - Values to fill the template with. Listed for each template in `config.json`