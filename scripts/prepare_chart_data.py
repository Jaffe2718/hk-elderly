"""Build the interactive chart payload from the supplied English CSV tables."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build():
    data = {}
    for key, name in [('housing', 'housing_coverage_en'), ('districts', 'district_coverage_en'),
                      ('distance', 'distance_binary_decisions'), ('age', 'age_binary_decisions')]:
        with (ROOT / 'assets/tables' / (name + '.csv')).open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.reader(stream)
            data[key] = {'columns': next(reader), 'rows': list(reader)}
    target = ROOT / 'docs/embeds/charts/data.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print('Prepared four CSV-backed interactive chart datasets')

if __name__ == '__main__':
    build()
