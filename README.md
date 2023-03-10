# Certificate Renderer

Render certificates for [Aviasim](https://aviasim.com.ua)

# Prerequisites

- Python version 3.10 or higher
- Chrome version 60 or higher

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
python main.py [-h] template [context_values ...]
```

All available templates, as well as their context keys, which are the values to fill the template with, are listed in
`renderer/config.py`. Output and chrome executable path also can be configured there. TIME_BUDGET setting controls the delay in
milliseconds of PDF creation process. The bigger the value - the less likely the result will contain not loaded images, 
fonts etc.