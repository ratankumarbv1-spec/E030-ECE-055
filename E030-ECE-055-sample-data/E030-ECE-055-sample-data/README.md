# ECE-055 – Electronics E-Waste Collection and Recycling Credit Engine — Sample Data Pack
Prepared by 10 SECONDS for Team E030.

This pack is the input for an e-waste collection and recycling-credit engine: 20 sources (6 BULK, 14 HOUSEHOLD), a 5-category rate card and 45 pickup requests in October 2026. Your engine reads `commands.txt`, computes a credit note for every request, schedules accepted pickups into vehicle days, and prints the schedule and the monthly summary.

Pack conventions where the brief is silent: there is one vehicle; vehicle days are Monday–Saturday. Requests are processed in requests.csv order; each one is tried on the vehicle days from the day AFTER its request date onward, and goes to the first day where weight (≤ 1,200.0 kg), stops (≤ 8) and hazardous weight (≤ 300.0 kg) all still fit. A request whose hazardous weight alone is above 300.0 kg (or total weight above 1,200.0 kg) can never fit and is refused with HAZARD_OVER_LIMIT (or OVER_CAPACITY). Refused requests get a credit note with status REFUSED and no money lines. Pickup charge = Rs 12 × (ceil(distance_km) − 10) when distance_km > 10, waived when the request totals 200.0 kg or more. Line credits are weight × rate (2 decimals); the net is rounded half up to whole rupees. The monthly summary counts weight by the month of the scheduled pickup day; 500.0 kg or more earns the certificate.

## Files
| File | What it holds | Rows |
|---|---|---|
| sources.csv | Collection sources with type and depot distance | 20 |
| rate_card.csv | Credit per kg and hazard flag per category | 5 |
| requests.csv | Pickup requests in request order | 45 |
| request_items.csv | Item lines of each request | 80 |
| commands.txt | Load commands, processing and print commands | 8 |

## Column reference
Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### sources.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| source_id | string | SRC-nn | SRC-01 … SRC-20 | Primary key |
| source_name | string | - |  | Institution or household name |
| source_type | string | - | BULK, HOUSEHOLD |  |
| area | string | - |  | Not used by any rule |
| distance_km | decimal | km, 1 dp |  | Rounded UP to whole km for the charge |
| contact_mobile | string | 10 digits | starts 6–9 | Not used by any rule |

### rate_card.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| category | string | - | IT, CONSUMER, BATTERY, CABLE, CRT | Primary key |
| credit_per_kg_rs | decimal | Rs/kg, 2 dp |  |  |
| hazardous | boolean | true/false |  | BATTERY and CRT are hazardous |

### requests.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| request_id | string | PKR-nnn | unique | Processing order |
| request_date | date | YYYY-MM-DD | October 2026 |  |
| source_id | string | SRC-nn | must exist in sources.csv |  |

### request_items.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| request_id | string | PKR-nnn | must exist in requests.csv |  |
| line_no | integer | - | 1, 2, 3 … |  |
| category | string | - | must exist in rate_card.csv |  |
| item_count | integer | pieces |  | Not used by any rule |
| weight_kg | decimal | kg, 1 dp |  |  |

## Command file format
`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored.

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_SOURCES / LOAD_RATE_CARD / LOAD_REQUESTS / LOAD_REQUEST_ITEMS | file | Load the input files |
| PROCESS_REQUESTS | (none) | Price and schedule every request in order |
| PRINT_CREDIT_NOTES | (none) | Print one credit note per request |
| PRINT_SCHEDULE | (none) | Print the vehicle-day schedule |
| MONTHLY_SUMMARY | YYYY-MM | Print the per-source monthly summary |

`status` SCHEDULED or REFUSED; `reason` NONE, BELOW_MINIMUM, HAZARD_OVER_LIMIT or OVER_CAPACITY. `net_rs` is a whole number (no decimals) and never negative: `net_type` says CREDIT or AMOUNT_PAYABLE. Money columns are NONE on REFUSED rows; `pickup_date` NONE when refused. `certificate` is RECYCLING_CERTIFICATE or NONE.

## Planted scenarios
Line numbers count the header row as line 1, so the first data row of a CSV is line 2. For commands.txt the line number is the physical line in the file (comment lines included).

- **Source at exactly 10 km** — requests.csv line 3 (PKR-002, SRC-07 HOUSEHOLD, 10.0 km, 15.7 kg): the source is exactly 10.0 km from the depot → free pickup. Compare requests.csv line 5 (PKR-004, SRC-13 HOUSEHOLD, 10.1 km, 10.0 kg): 10.1 km rounds up to 11 km → 1 km × Rs 12 = Rs 12.
- **Pickup weighing exactly 200 kg** — requests.csv line 7 (PKR-006, SRC-03 BULK, 23.6 km, 200.0 kg): total weight exactly 200.0 kg → the distance charge is waived. The same source later sends requests.csv line 39 (PKR-038, SRC-03 BULK, 23.6 km, 199.9 kg): 199.9 kg → charged (ceil(distance) − 10) × Rs 12.
- **Household request of exactly 5 kg** — requests.csv line 10 (PKR-009, SRC-19 HOUSEHOLD, 25.2 km, 5.0 kg): a household request of exactly 5.0 kg → accepted. requests.csv line 11 (PKR-010, SRC-12 HOUSEHOLD, 5.6 km, 4.9 kg): 4.9 kg → refused with BELOW_MINIMUM.
- **Vehicle day already holding 7 stops and 1,150 kg** — Requests PKR-015, PKR-016, PKR-017, PKR-018, PKR-019, PKR-020, PKR-021 (all dated 2026-10-13) fill the vehicle day 2026-10-14 to 7 stops and 1,150.0 kg. requests.csv line 23 (PKR-022, SRC-15 HOUSEHOLD, 28.8 km, 50.0 kg) weighs 50.0 kg → it is the 8th stop and brings the day to exactly 1,200.0 kg (allowed). requests.csv line 24 (PKR-023, SRC-18 HOUSEHOLD, 17.9 km, 12.5 kg) finds no stop left on 2026-10-14 → it moves to the next vehicle day.
- **Request that is 100% batteries weighing 350 kg** — requests.csv line 27 (PKR-026, SRC-04 BULK, 25.3 km, 350.0 kg) is 100% BATTERY, 350.0 kg → more than the 300 kg hazard limit of any vehicle day, so it can never be scheduled → refused (HAZARD_OVER_LIMIT). Its credit note has status REFUSED and no money lines.

Extra traps (realistic things your validation should catch):

- **Hazard room on a partly loaded day** — requests.csv line 41 (PKR-040, SRC-02 BULK, 18.9 km, 300.0 kg) puts 90.0 kg of batteries on its vehicle day; requests.csv line 42 (PKR-041, SRC-06 BULK, 20.0 km, 250.0 kg) (250.0 kg of batteries, same request date) fits by weight but not by hazard room (90 + 250 > 300) → it moves to a later day.
- **Household hazardous deduction** — requests.csv line 15 (PKR-014, SRC-15 HOUSEHOLD, 28.8 km, 28.8 kg): a household hands over a 28 kg CRT TV → CRT is hazardous → Rs 15/kg deduction instead of a credit; the net is negative → AMOUNT_PAYABLE.
- **Certificate at exactly 500 kg** — SRC-01 collects 180.0 + 195.5 + 124.5 = 500.0 kg in October (requests.csv line 6 (PKR-005, SRC-01 BULK, 25.7 km, 180.0 kg), requests.csv line 33 (PKR-032, SRC-01 BULK, 25.7 km, 195.5 kg), requests.csv line 44 (PKR-043, SRC-01 BULK, 25.7 km, 124.5 kg)) → reaches 500 kg → RECYCLING_CERTIFICATE.
- **No Sunday pickups** — Vehicle days run Monday to Saturday; a request dated Saturday is first tried on Monday.

## What is NOT in this pack
Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-07). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation
Produce these files (CSV, header row, same conventions as above). Column order matters.

### credit_notes.csv
One row per request in request order.

Columns in order: `request_id`, `source_id`, `status`, `reason`, `total_kg`, `hazardous_kg`, `credit_rs`, `deduction_rs`, `pickup_charge_rs`, `net_rs`, `net_type`, `pickup_date`

### pickup_schedule.csv
One row per scheduled request, ordered by pickup_date then request order.

Columns in order: `pickup_date`, `stop_no`, `request_id`, `source_id`, `kg`, `hazardous_kg`, `day_kg_after`, `day_hazardous_kg_after`

### monthly_summary.csv
One row per source with at least one request, ordered by source_id, then certificate lines.

Columns in order: `month`, `source_id`, `requests`, `collected_kg`, `net_credit_rs`, `net_payable_rs`, `certificate`
