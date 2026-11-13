# E-Waste Credit Engine — Phase 2

This package is the actual ECE-055 capstone implementation. It loads the sample inputs, computes request financials, applies refusal rules, schedules accepted requests, and writes the three required CSV reports.

## Run

From the repository root:

```powershell
python -m e_waste_engine.main
```

To use another command file:

```powershell
python -m e_waste_engine.main --commands "path/to/commands.txt"
```

The default command file is in `E030-ECE-055-sample-data/E030-ECE-055-sample-data/commands.txt`. Reports are written to that pack folder's `output/` directory. The supplied input files are read in place and are not modified.

## Files

- `models.py` — typed records for sources, rates, item lines, requests, vehicle-day totals, and processing results.
- `main.py` — reads the command file and CSVs, checks data references, connects item lines to requests, and prints run progress and summary.
- `engine.py` — calculates hazardous weight and money, applies request refusals, and assigns accepted requests to vehicle days.
- `reports.py` — writes credit notes, ordered vehicle stops, and the requested month's per-source summary.
- `phase_2_guide.md` — student-focused explanation of the Phase 2 workflow and important code locations.

The learning demo in the sibling `learning_demo/` folder is a separate teaching implementation. Its outputs are not official expected outputs.
