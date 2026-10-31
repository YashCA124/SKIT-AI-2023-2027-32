"""
Combined Weekly Progress Report Merger

This script:
1. Checks that weekly reports exist.
2. Verifies that 9 weekly reports are available.
3. Merges all weekly PDFs into one combined PDF in the weekly_reports folder.
4. Keeps the same report format as the original weekly reports.

Requirements:
    pip install pypdf
"""

import datetime
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pypdf/PyPDF2 is required. Install with: pip install pypdf"
        ) from exc


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
WEEKLY_REPORT_DIR = BASE_DIR / "weekly_reports"
EXPECTED_REPORTS = 9


# --------------------------------------------------
# CHECK WEEKLY REPORTS
# --------------------------------------------------

def check_weekly_reports():
    print("\nChecking weekly reports...")

    if not WEEKLY_REPORT_DIR.exists():
        raise FileNotFoundError("weekly_reports directory does not exist.")

    reports = sorted(
        WEEKLY_REPORT_DIR.glob("*_Weekly_Progress_Report_Form-3_*.pdf")
    )

    print(f"Weekly reports found: {len(reports)}")
    for report in reports:
        print(f" - {report.name}")

    if len(reports) < EXPECTED_REPORTS:
        raise ValueError(
            f"Expected at least {EXPECTED_REPORTS} weekly reports, "
            f"but found only {len(reports)}."
        )

    print("\nAll required weekly reports are available.")
    return reports


# --------------------------------------------------
# MERGE WEEKLY REPORTS INTO ONE FILE
# --------------------------------------------------

def merge_weekly_reports(reports):
    print("\nMerging weekly PDFs into one combined report...")

    writer = PdfWriter()

    for report in reports:
        reader = PdfReader(str(report))
        for page in reader.pages:
            writer.add_page(page)

    stamp = datetime.date.today().strftime("%Y-%m-%d")
    repo_name = BASE_DIR.name
    combined_name = (
        f"{repo_name}_Combined_Weekly_Progress_Report_Form-3_{stamp}.pdf"
    )
    output_path = WEEKLY_REPORT_DIR / combined_name

    if output_path.exists():
        output_path.unlink()

    with output_path.open("wb") as target:
        writer.write(target)

    print("\nCombined report created successfully.")
    print(f"Location: {output_path}")
    return output_path


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

def main():
    print("=" * 60)
    print("COMBINED WEEKLY REPORT MERGER")
    print("=" * 60)

    try:
        reports = check_weekly_reports()
        merge_weekly_reports(reports)

        print("\n" + "=" * 60)
        print("WEEKLY REPORTS COMBINED SUCCESSFULLY")
        print("=" * 60)

    except Exception as error:
        print("\nERROR:", str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
