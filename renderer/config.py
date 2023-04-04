import os

RENDERER_PATH = os.path.dirname(os.path.abspath(__file__))

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
OUTPUT_PATH = RENDERER_PATH

TEMPLATES = [
    {
        "name": "fixed_date",
        "context_keys": [
            ("duration", ["30", "60", "120"]),
            "code",
            "date",
            "time"
        ]
    },
    {
        "name": "variable_date",
        "context_keys": [
            ("duration", ["30", "60", "120"]),
            "code"
        ]
    }
]

TIME_BUDGET = 15000
