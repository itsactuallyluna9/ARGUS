import uuid
from pathlib import Path
import json
from datetime import datetime

last_seen = {}

for log_file in Path(".").glob("eval*.json"):
    no_thinking = log_file.match("*no_think*") or log_file.match("*gemma*")
    log_data = json.load(log_file.open())
    log_data["thinking"] = not no_thinking
    with log_file.open('w') as f:
        json.dump(log_data, f, indent=4)
    
