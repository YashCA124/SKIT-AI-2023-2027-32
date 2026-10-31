"""
Consolidate weekly progress reports by team member.

The generated PDF groups all commit logs for each student together instead of
appending the weekly PDFs unchanged.

Requirements:
    pip install pypdf reportlab
"""

import datetime
import html
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pypdf/PyPDF2 is required. Install with: pip install pypdf"
        ) from exc

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        LongTable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "reportlab is required. Install with: pip install reportlab"
    ) from exc


BASE_DIR = Path(__file__).resolve().parent
WEEKLY_REPORT_DIR = BASE_DIR / "weekly_reports"
EXPECTED_REPORTS = 9

STUDENT_HEADER = re.compile(
    r"^Student:\s*(.*?)\s+(?:—|–|-|�)\s+(\d+)\s+commit\(s\)\s*$"
)
DATE_LINE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH_LINE = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)
MENTOR_MARK_LINE = re.compile(r"^(?:_+|\d+(?:\.\d+)?)\s*/\s*10$")


def check_weekly_reports():
    print("\nChecking weekly reports...")

    if not WEEKLY_REPORT_DIR.exists():
        raise FileNotFoundError("weekly_reports directory does not exist.")

    reports = sorted(
        report
        for report in WEEKLY_REPORT_DIR.glob("*_Weekly_Progress_Report_Form-3_*.pdf")
        if "_Combined_Weekly_Progress_Report_Form-3_" not in report.name
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


def extract_student_logs(report):
    reader = PdfReader(str(report))
    lines = []
    for page in reader.pages:
        lines.extend((page.extract_text() or "").splitlines())

    logs = []
    current_student = None
    commit_date = None
    commit_hash = None
    message_parts = []
    found_log_section = False
    found_empty_log_message = False
    expected_commits = None
    current_commit_count = 0

    def save_commit():
        nonlocal current_commit_count
        if commit_date and commit_hash and current_student:
            message = " ".join(message_parts).strip() or "(No commit message)"
            logs.append((current_student, commit_date, commit_hash, message))
            current_commit_count += 1

    def finish_student():
        save_commit()
        if (
            current_student
            and expected_commits is not None
            and current_commit_count != expected_commits
        ):
            raise ValueError(
                f"{report.name}: expected {expected_commits} commit log(s) for "
                f"{current_student}, but parsed {current_commit_count}."
            )

    for raw_line in lines:
        line = raw_line.strip()

        if line.startswith("3. Detailed Commit Logs"):
            found_log_section = True
            continue

        if not found_log_section:
            continue

        if line == "No commit logs found for this timeframe.":
            found_empty_log_message = True
            continue

        student_match = STUDENT_HEADER.match(line)
        if student_match:
            finish_student()
            current_student = student_match.group(1).strip()
            expected_commits = int(student_match.group(2))
            current_commit_count = 0
            commit_date = None
            commit_hash = None
            message_parts = []
            continue

        if line.startswith("Name:"):
            finish_student()
            current_student = None
            expected_commits = None
            current_commit_count = 0
            commit_date = None
            commit_hash = None
            message_parts = []
            continue

        if not current_student:
            continue

        if line in {
            "Date",
            "Hash",
            "Commit Message",
            "Mentor Marks (/10)",
        } or MENTOR_MARK_LINE.match(line):
            continue

        if DATE_LINE.match(line):
            save_commit()
            commit_date = line
            commit_hash = None
            message_parts = []
        elif commit_date and commit_hash is None and HASH_LINE.match(line):
            commit_hash = line
        elif commit_date and commit_hash:
            message_parts.append(line)

    finish_student()

    if not found_log_section:
        raise ValueError(
            f"{report.name} does not contain a detailed commit log section."
        )
    if not logs and not found_empty_log_message:
        raise ValueError(f"{report.name} does not contain any student commit logs.")

    return logs


def collect_student_logs(reports):
    logs_by_student = {}
    seen_commits = defaultdict(set)
    display_names = {}

    for report in reports:
        for student_name, commit_date, commit_hash, message in extract_student_logs(
            report
        ):
            student_key = student_name.casefold()
            display_name = display_names.setdefault(student_key, student_name)
            if commit_hash in seen_commits[student_key]:
                continue

            seen_commits[student_key].add(commit_hash)
            logs_by_student.setdefault(display_name, []).append(
                (commit_date, commit_hash, message)
            )

    return {
        student: sorted(logs, key=lambda log: (log[0], log[1]))
        for student, logs in sorted(
            logs_by_student.items(), key=lambda item: item[0].casefold()
        )
    }


def create_report(reports):
    print("\nCollecting commit logs by team member...")
    logs_by_student = collect_student_logs(reports)

    stamp = datetime.date.today().strftime("%Y-%m-%d")
    repo_name = BASE_DIR.name
    output_path = WEEKLY_REPORT_DIR / (
        f"{repo_name}_Combined_Weekly_Progress_Report_Form-3_{stamp}.pdf"
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=12,
    )
    student_style = ParagraphStyle(
        "StudentHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )
    message_style = ParagraphStyle(
        "CommitMessage",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
    )
    cell_style = ParagraphStyle(
        "CommitCell",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
    )

    story = [
        Paragraph("Project Contributions by Team Member", title_style),
        Paragraph(
            f"Consolidated from {len(reports)} weekly reports "
            f"&nbsp;|&nbsp; Generated {datetime.date.today():%B %d, %Y}",
            subtitle_style,
        ),
    ]

    summary_data = [["Team member", "Commits"]]
    summary_data.extend(
        [student, str(len(logs))]
        for student, logs in logs_by_student.items()
    )
    if not logs_by_student:
        summary_data.append(["No commit logs found", "0"])

    summary_table = Table(summary_data, colWidths=[390, 100], repeatRows=1)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 10)])

    for student, logs in logs_by_student.items():
        story.append(
            Paragraph(
                f"{html.escape(student)} - {len(logs)} commit(s)",
                student_style,
            )
        )
        table_data = [
            [
                "Date",
                "Commit",
                "Work / commit message",
            ]
        ]
        table_data.extend(
            [
                Paragraph(commit_date, cell_style),
                Paragraph(commit_hash, cell_style),
                Paragraph(html.escape(message), message_style),
            ]
            for commit_date, commit_hash, message in logs
        )
        commit_table = LongTable(
            table_data,
            colWidths=[75, 65, 350],
            repeatRows=1,
        )
        commit_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(commit_table)

    document.build(story)
    print("\nConsolidated report created successfully.")
    print(f"Location: {output_path}")
    return output_path


def main():
    print("=" * 60)
    print("CONSOLIDATED TEAM CONTRIBUTION REPORT")
    print("=" * 60)

    try:
        reports = check_weekly_reports()
        create_report(reports)

        print("\n" + "=" * 60)
        print("TEAM CONTRIBUTIONS CONSOLIDATED SUCCESSFULLY")
        print("=" * 60)

    except Exception as error:
        print("\nERROR:", str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
