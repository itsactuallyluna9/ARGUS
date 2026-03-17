import json
import csv
from pathlib import Path
from datetime import datetime

def main():
    with open(f"logs/consolidated_summary_{datetime.now().isoformat()}.csv", "w") as f:
        writer = csv.writer(f)
        first = True
        for log in Path("logs").glob("summary_*.json"):
            with open(log, "r") as f:
                data = json.load(f)
                if first:
                    writer.writerow(data.keys())
                    first = False
                writer.writerow(data.values())
                
    with open(f"logs/consolidated_evaluation_{datetime.now().isoformat()}.csv", "w") as f:
        writer = csv.writer(f)
        first = True
        for log in Path("logs").glob("evaluation_*.json"):
            with open(log, "r") as f:
                data = json.load(f)
                if first:
                    writer.writerow(data.keys())
                    first = False
                writer.writerow(data.values())

if __name__ == "__main__":
    main()
