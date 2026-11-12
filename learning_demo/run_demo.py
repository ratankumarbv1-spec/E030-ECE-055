"""Run the command-file-driven sample pack through the learning demo."""

import argparse
from pathlib import Path

from .data_loader import DataError, attach_request_items, load_rates, load_request_headers, load_sources
from .engine import process_requests
from .reports import day_totals, write_credit_notes, write_monthly_summary, write_schedule


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DEFAULT_COMMANDS = PROJECT_ROOT / "E030-ECE-055-sample-data" / "E030-ECE-055-sample-data" / "commands.txt"


def parse_args():
    parser = argparse.ArgumentParser(description="Run the sample pack with a teaching-focused Python demo.")
    parser.add_argument("--commands", type=Path, default=DEFAULT_COMMANDS,
                        help="Path to the supplied commands.txt file")
    parser.add_argument("--output-dir", type=Path, default=HERE / "output",
                        help="Folder for the three generated CSV reports")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    commands_file = args.commands.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = None
    rates = None
    requests = None
    results = None
    days = None

    try:
        for line_number, raw_line in enumerate(commands_file.read_text(encoding="utf-8-sig").splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split("|")]
            command, *arguments = parts
            pack_dir = commands_file.parent

            if command == "LOAD_SOURCES" and len(arguments) == 1:
                sources = load_sources(pack_dir / arguments[0])
                print(f"Loaded {len(sources)} sources from {arguments[0]}")
            elif command == "LOAD_RATE_CARD" and len(arguments) == 1:
                rates = load_rates(pack_dir / arguments[0])
                print(f"Loaded {len(rates)} categories from {arguments[0]}")
            elif command == "LOAD_REQUESTS" and len(arguments) == 1:
                requests_file = pack_dir / arguments[0]
                if sources is None:
                    raise DataError("Load sources before requests")
                requests = load_request_headers(requests_file, sources)
                print(f"Loaded {len(requests)} request headers from {arguments[0]}")
            elif command == "LOAD_REQUEST_ITEMS" and len(arguments) == 1:
                if not isinstance(requests, list) or sources is None or rates is None:
                    raise DataError("Load sources, rate card, and requests before request items")
                requests = attach_request_items(requests, pack_dir / arguments[0], rates)
                print(f"Attached item lines from {arguments[0]} to {len(requests)} requests")
            elif command == "PROCESS_REQUESTS" and not arguments:
                if not isinstance(requests, list) or sources is None or rates is None:
                    raise DataError("All four input files must be loaded before PROCESS_REQUESTS")
                results, days = process_requests(requests, sources, rates)
                refused = sum(result.status == "REFUSED" for result in results)
                print(f"Processed {len(results)} requests: {len(results) - refused} scheduled, {refused} refused")
                print("Vehicle-day totals:")
                for line in day_totals(days):
                    print(f"  {line}")
            elif command == "PRINT_CREDIT_NOTES" and not arguments:
                if results is None:
                    raise DataError("Run PROCESS_REQUESTS before PRINT_CREDIT_NOTES")
                path = write_credit_notes(output_dir, results)
                print(f"Wrote {len(results)} credit-note rows to {path}")
            elif command == "PRINT_SCHEDULE" and not arguments:
                if results is None:
                    raise DataError("Run PROCESS_REQUESTS before PRINT_SCHEDULE")
                path = write_schedule(output_dir, results)
                count = sum(result.status == "SCHEDULED" for result in results)
                print(f"Wrote {count} scheduled-pickup rows to {path}")
            elif command == "MONTHLY_SUMMARY" and len(arguments) == 1:
                if results is None or sources is None:
                    raise DataError("Run PROCESS_REQUESTS before MONTHLY_SUMMARY")
                path = write_monthly_summary(output_dir, arguments[0], results, sources)
                print(f"Wrote {arguments[0]} summary to {path}")
            else:
                raise DataError(f"commands.txt line {line_number}: unknown command or wrong arguments: {line}")
    except (OSError, DataError) as exc:
        print(f"Demo stopped: {exc}")
        return 2

    print("Demo complete. The generated CSVs are teaching outputs, not official expected answers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
