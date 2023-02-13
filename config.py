import os

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
OUTPUT_PATH = PROJECT_PATH

TEMPLATES = [
    {
        "name": "fixed_date",
        "context_keys": [
            "duration",
            "code",
            "date",
            "time"
        ]
    },
    {
        "name": "variable_date",
        "context_keys": [
            "duration",
            "code"
        ]
    }
]
