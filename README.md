# Certificate Renderer

Render certificates for Aviasim

# Prerequisites

- Python version >3.11
- Chrome version >60

# Usage

Run following command inside project directory:

```shell
python main.py [--chrome-path CHROME_PATH] template [context_values ...]
```

`--chrome-path` - Optional argument to set path to your chrome executable, if it doesn't match path specified in 
`config.json`.

`template` - Template to use. All templates available are listed in `config.json`

`context_values` - Values to fill the template with. Listed for each template in `config.json`