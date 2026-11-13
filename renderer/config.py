import os

RENDERER_PATH = os.path.dirname(os.path.abspath(__file__))

# Override with the CHROME_PATH environment variable to render outside the Docker image.
CHROME_PATH = os.environ.get('CHROME_PATH', '/usr/bin/google-chrome')
OUTPUT_PATH = os.path.join(RENDERER_PATH, 'output')
TEMPLATE_PATH = os.path.join(RENDERER_PATH, 'templates')
