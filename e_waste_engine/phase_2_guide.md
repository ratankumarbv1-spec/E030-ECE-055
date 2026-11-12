# Phase 2 Guide

## What this phase adds

Phase 2 adds the core business calculations and one-vehicle scheduler. The sample inputs are loaded from the pack; the pack itself is not changed. Report-file generation remains for Phase 3.

## Main files

- `models.py` defines Source, Rate, Item, Request, VehicleDay, and Result records.
- `engine.py` calculates hazardous weight, credit/deductions/charges, refusals, and the pickup day.
- `main.py` executes `commands.txt`, loads CSVs, calls the engine at `PROCESS_REQUESTS`, and prints a compact summary.

## Important code landmarks

- `engine.py`, lines 9-15: rule limits and financial constants.
- `engine.py`, `calculate_money()`: line credits, household hazardous deduction, distance charge, and half-up whole-rupee net.
- `engine.py`, `next_vehicle_day()`: skips Sundays.
- `engine.py`, `schedule_one()`: minimum and impossible-request refusals, then checks stops, total weight, and hazardous weight together for each candidate date.
- `engine.py`, `process()`: processes the requests in their original file order.
- `main.py`, `PROCESS_REQUESTS` branch: starts the engine and prints scheduled/refused counts plus a compact busiest-day summary.

## Important behavior

- Each request is first tried on the day after its request date, skipping Sunday.
- A request is scheduled whole on the earliest eligible day where all three vehicle limits fit.
- A HOUSEHOLD request under 5 kg is refused; exactly 5 kg is eligible.
- Requests above the daily hazard or total-weight limit are refused as `HAZARD_OVER_LIMIT` or `OVER_CAPACITY`.
- Refused results carry no money amounts; Phase 3 will serialize these as `NONE` in the required CSV.
- Item-line credit is rounded to two decimals. Net is rounded half up to a whole rupee.

## Current phase boundary

The engine returns per-request results and daily totals in memory. It does not write the required three CSV reports yet. The sample pack has no expected-output files, so this run confirms that the supplied scenario notes are reflected in the processing flow; it is not a field-by-field comparison to an official answer file.
