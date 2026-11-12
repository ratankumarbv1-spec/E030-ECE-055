# E-Waste Credit Engine — Phase 2

This package is the actual ECE-055 capstone implementation. It currently loads the sample inputs, computes request financials, applies refusal rules, and schedules accepted requests. The final CSV report writers are planned for Phase 3.

## Run

From the repository root:

```powershell
python -m e_waste_engine.main
```

To use another command file:

```powershell
python -m e_waste_engine.main --commands "path/to/commands.txt"
```

The default command file is in `E030-ECE-055-sample-data/E030-ECE-055-sample-data/commands.txt`. The sample pack is read in place and is not modified.

## Files

- `models.py` — typed records for sources, rates, item lines, requests, vehicle-day totals, and processing results.
- `main.py` — reads the command file and CSVs, checks data references, connects item lines to requests, and prints run progress and summary.
- `engine.py` — calculates hazardous weight and money, applies request refusals, and assigns accepted requests to vehicle days.
- `phase_2_guide.md` — student-focused explanation of the Phase 2 workflow and important code locations.

Run output is currently a summary only. The learning demo in the sibling `learning_demo/` folder writes example reports; those files are not official expected outputs.
