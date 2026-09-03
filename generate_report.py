import subprocess
from collections import defaultdict
import datetime
import io
import os
import sys
import html

import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# ============================================================
# CONFIGURATION
# ============================================================

COLLEGE_NAME = (
    "Swami Keshvanand Institute of Technology, "
    "Management & Gramothan, Jaipur"
)

DEPARTMENT_NAME = "Department of Computer Science & Engineering"


# ============================================================
# GET REPOSITORY INFORMATION
# ============================================================

def get_repo_info():
    """
    Extracts the repository name and current Git branch.
    """

    repo_name = "Project-Repository"
    branch_name = "main"

    # --------------------------------------------------------
    # Get repository root
    # --------------------------------------------------------
    try:
        root_path = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            encoding="utf-8",
            errors="replace",
        ).strip()

        repo_name = os.path.basename(root_path)

    except Exception:

        # ----------------------------------------------------
        # Fallback: Get repository name from remote URL
        # ----------------------------------------------------
        try:
            remote_url = subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                encoding="utf-8",
                errors="replace",
            ).strip()

            repo_name = (
                remote_url.rstrip("/")
                .split("/")[-1]
                .replace(".git", "")
            )

        except Exception:
            repo_name = os.path.basename(os.getcwd())

    # --------------------------------------------------------
    # Get current branch
    # --------------------------------------------------------
    try:
        branch_name = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            encoding="utf-8",
            errors="replace",
        ).strip()

    except Exception:
        pass

    return repo_name, branch_name


# ============================================================
# GET GIT METRICS
# ============================================================

def get_git_metrics(interval="weekly"):
    """
    Parses Git commit logs.

    Supported intervals:
        weekly
        monthly
        final
    """

    today = datetime.date.today()

    # --------------------------------------------------------
    # Base Git command
    # --------------------------------------------------------

    git_args = [
        "git",
        "log",
        "--no-merges",
        "--pretty=format:COMMIT|||%h|||%an|||%ad|||%s",
        "--date=short",
        "--numstat",
    ]

    # --------------------------------------------------------
    # Determine time period
    # --------------------------------------------------------

    if interval == "weekly":

        since_date = (
            today - datetime.timedelta(days=7)
        ).strftime("%Y-%m-%d")

        git_args.append(f"--since={since_date}")

        scope_title = (
            f"Last 7 Days (Since {since_date})"
        )

    elif interval == "monthly":

        since_date = (
            today - datetime.timedelta(days=30)
        ).strftime("%Y-%m-%d")

        git_args.append(f"--since={since_date}")

        scope_title = (
            f"Last 30 Days (Since {since_date})"
        )

    elif interval == "final":

        scope_title = "Complete Project Lifecycle (All Commits)"

    else:

        print(
            "[ERROR] Invalid interval. "
            "Use: weekly, monthly, or final."
        )

        return None, None, None, scope_title

    # --------------------------------------------------------
    # Execute Git command
    # --------------------------------------------------------

    try:

        raw_output = subprocess.check_output(
            git_args,
            encoding="utf-8",
            errors="replace",
        )

    except subprocess.CalledProcessError:

        print(
            "[ERROR] Git command failed. "
            "Please ensure you are inside a Git repository."
        )

        return None, None, None, scope_title

    # --------------------------------------------------------
    # Data structures
    # --------------------------------------------------------

    students = defaultdict(
        lambda: {
            "commits": 0,
            "added": 0,
            "deleted": 0,
            "active_days": set(),
        }
    )

    timeline_activity = defaultdict(
        lambda: defaultdict(int)
    )

    student_logs = defaultdict(list)

    current_author = None
    current_date_str = None

    # --------------------------------------------------------
    # Parse Git output
    # --------------------------------------------------------

    for line in raw_output.strip().split("\n"):

        line = line.strip()

        if not line:
            continue

        # ----------------------------------------------------
        # New commit
        # ----------------------------------------------------

        if line.startswith("COMMIT|||"):

            parts = line.split("|||")

            if len(parts) < 5:
                continue

            sha = parts[1].strip()
            author = parts[2].strip()
            date_str = parts[3].strip()
            msg = parts[4].strip()

            # ------------------------------------------------
            # Ignore automated bots
            # ------------------------------------------------

            if (
                "bot" in author.lower()
                or "github-actions" in author.lower()
                or "dependabot" in author.lower()
            ):

                current_author = None
                current_date_str = None
                continue

            # ------------------------------------------------
            # Store commit information
            # ------------------------------------------------

            current_author = author
            current_date_str = date_str

            students[current_author]["commits"] += 1

            students[current_author]["active_days"].add(
                current_date_str
            )

            student_logs[current_author].append(
                (
                    date_str,
                    sha,
                    msg,
                )
            )

            # ------------------------------------------------
            # Add commit to timeline
            # ------------------------------------------------

            try:

                dt = datetime.datetime.strptime(
                    current_date_str,
                    "%Y-%m-%d",
                ).date()

                if interval == "weekly":

                    period_key = dt.strftime(
                        "%a (%b %d)"
                    )

                elif interval == "monthly":

                    period_key = (
                        f"{dt.isocalendar()[0]}"
                        f"-W{dt.isocalendar()[1]:02d}"
                    )

                else:

                    period_key = dt.strftime("%Y-%m")

                timeline_activity[
                    period_key
                ][current_author] += 1

            except Exception:
                pass

        # ----------------------------------------------------
        # Numstat line
        # ----------------------------------------------------

        elif (
            current_author
            and not line.startswith("COMMIT|||")
        ):

            parts = line.split()

            if len(parts) >= 2:

                # Git numstat:
                # additions deletions filename

                if (
                    parts[0].isdigit()
                    and parts[1].isdigit()
                ):

                    students[current_author][
                        "added"
                    ] += int(parts[0])

                    students[current_author][
                        "deleted"
                    ] += int(parts[1])

    return (
        students,
        timeline_activity,
        student_logs,
        scope_title,
    )


# ============================================================
# CREATE CHARTS
# ============================================================

def create_charts(
    students,
    timeline_activity,
    interval,
):
    """
    Generates:
        1. Commit timeline chart
        2. Net LOC chart
    """

    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(11, 3.8),
    )

    authors = list(students.keys())

    # Sort periods properly
    periods = sorted(timeline_activity.keys())

    # ========================================================
    # CHART 1: COMMIT TIMELINE
    # ========================================================

    if periods and authors:

        for author in authors:

            counts = [
                timeline_activity[period].get(
                    author,
                    0,
                )
                for period in periods
            ]

            ax1.plot(
                periods,
                counts,
                marker="o",
                linewidth=2,
                label=author,
            )

        ax1.set_title(
            f"Commit Timeline ({interval.capitalize()})",
            fontsize=10,
            fontweight="bold",
        )

        ax1.set_ylabel("Commits")

        ax1.tick_params(
            axis="x",
            rotation=30,
        )

        ax1.grid(
            True,
            linestyle="--",
            alpha=0.5,
        )

        ax1.legend(
            fontsize=8,
            loc="best",
        )

    else:

        ax1.text(
            0.5,
            0.5,
            "No commits found in this interval",
            ha="center",
            va="center",
        )

        ax1.set_axis_off()

    # ========================================================
    # CHART 2: NET LOC
    # ========================================================

    if authors:

        net_loc = [
            students[author]["added"]
            - students[author]["deleted"]
            for author in authors
        ]

        ax2.bar(
            authors,
            net_loc,
            width=0.45,
        )

        ax2.set_title(
            "Net Lines of Code Written",
            fontsize=10,
            fontweight="bold",
        )

        ax2.set_ylabel(
            "LOC (Added - Deleted)"
        )

        ax2.grid(
            axis="y",
            linestyle="--",
            alpha=0.5,
        )

        ax2.tick_params(
            axis="x",
            rotation=30,
        )

    else:

        ax2.text(
            0.5,
            0.5,
            "No LOC changes recorded",
            ha="center",
            va="center",
        )

        ax2.set_axis_off()

    # ========================================================
    # Save chart into memory
    # ========================================================

    plt.tight_layout()

    img_buffer = io.BytesIO()

    plt.savefig(
        img_buffer,
        format="png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    img_buffer.seek(0)

    return Image(
        img_buffer,
        width=500,
        height=170,
    )


# ============================================================
# GENERATE PDF
# ============================================================

def generate_pdf(interval="weekly"):

    # --------------------------------------------------------
    # Get Git information
    # --------------------------------------------------------

    (
        repo_name,
        branch_name,
    ) = get_repo_info()

    (
        students,
        timeline_activity,
        student_logs,
        scope_title,
    ) = get_git_metrics(interval)

    if students is None:
        return

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    date_stamp = datetime.date.today().strftime(
        "%Y-%m-%d"
    )

    # --------------------------------------------------------
    # Report title and filename
    # --------------------------------------------------------

    if interval == "weekly":

        report_title = (
            "Weekly Progress Report (Form-3)"
        )

        doc_name = (
            f"{repo_name}_"
            f"Weekly_Progress_Report_Form-3_"
            f"{date_stamp}.pdf"
        )

    elif interval == "monthly":

        report_title = (
            "Monthly Progress Report (Form-3)"
        )

        doc_name = (
            f"{repo_name}_"
            f"Monthly_Progress_Report_Form-3_"
            f"{date_stamp}.pdf"
        )

    else:

        report_title = (
            "Final Project Evaluation Report"
        )

        doc_name = (
            f"{repo_name}_"
            f"Final_Report_"
            f"{date_stamp}.pdf"
        )

    # ========================================================
    # PDF DOCUMENT
    # ========================================================

    doc = SimpleDocTemplate(
        doc_name,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=30,
        bottomMargin=30,
    )

    # ========================================================
    # STYLES
    # ========================================================

    styles = getSampleStyleSheet()

    college_style = ParagraphStyle(
        "CollegeStyle",
        parent=styles["Heading1"],
        fontSize=13.5,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        spaceAfter=2,
    )

    dept_style = ParagraphStyle(
        "DeptStyle",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=6,
    )

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1A365D"),
        alignment=1,
        spaceAfter=5,
    )

    repo_style = ParagraphStyle(
        "RepoStyle",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )

    meta_style = ParagraphStyle(
        "MetaStyle",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=8,
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=7,
        spaceAfter=4,
    )

    sub_section_style = ParagraphStyle(
        "SubSectionStyle",
        parent=styles["Heading3"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=5,
        spaceAfter=2,
    )

    msg_style = ParagraphStyle(
        "MsgStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
    )

    meta_cell_style = ParagraphStyle(
        "MetaCellStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )

    marks_style = ParagraphStyle(
        "MarksStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )

    sig_block_style = ParagraphStyle(
        "SigBlockStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
        alignment=0,
    )

    # ========================================================
    # STORY
    # ========================================================

    story = []

    # ========================================================
    # 1. HEADER
    # ========================================================

    story.append(
        Paragraph(
            f"<b>{html.escape(COLLEGE_NAME)}</b>",
            college_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>{html.escape(DEPARTMENT_NAME)}</b>",
            dept_style,
        )
    )

    story.append(
        Paragraph(
            f"<u><b>{html.escape(report_title)}</b></u>",
            title_style,
        )
    )

    story.append(
        Spacer(1, 3)
    )

    # ========================================================
    # 2. METADATA
    # ========================================================

    story.append(
        Paragraph(
            f"<b>Project Repository:</b> "
            f"<font color='#2563EB'><b>"
            f"{html.escape(repo_name)}"
            f"</b></font> "
            f"&nbsp;|&nbsp; "
            f"<b>Branch:</b> "
            f"<code>{html.escape(branch_name)}</code>",
            repo_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Evaluation Window:</b> "
            f"{html.escape(scope_title)} "
            f"&nbsp;|&nbsp; "
            f"<b>Generated On:</b> "
            f"{datetime.date.today().strftime('%B %d, %Y')}",
            meta_style,
        )
    )

    # ========================================================
    # 3. INDIVIDUAL CONTRIBUTION TABLE
    # ========================================================

    story.append(
        Paragraph(
            "1. Individual Contribution Breakdown",
            section_style,
        )
    )

    total_commits = sum(
        data["commits"]
        for data in students.values()
    )

    table_data = [
        [
            "Student Name",
            "Commits (%)",
            "Lines Added",
            "Lines Deleted",
            "Net LOC",
            "Active Days",
        ]
    ]

    if students:

        for name, data in students.items():

            pct = (
                data["commits"]
                / total_commits
                * 100
                if total_commits > 0
                else 0
            )

            net = (
                data["added"]
                - data["deleted"]
            )

            table_data.append(
                [
                    html.escape(name),
                    f"{data['commits']} ({pct:.1f}%)",
                    f"+{data['added']:,}",
                    f"-{data['deleted']:,}",
                    f"{net:,}",
                    f"{len(data['active_days'])} days",
                ]
            )

    else:

        table_data.append(
            [
                "No commits found in this period.",
                "-",
                "-",
                "-",
                "-",
                "-",
            ]
        )

    table = Table(
        table_data,
        colWidths=[
            120,
            80,
            80,
            80,
            80,
            100,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1E293B"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "LEFT",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3.5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3.5,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ],
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 6)
    )

    # ========================================================
    # 4. VISUAL TRENDS
    # ========================================================

    story.append(
        Paragraph(
            "2. Visual Trends & Volume",
            section_style,
        )
    )

    chart_image = create_charts(
        students,
        timeline_activity,
        interval,
    )

    story.append(chart_image)

    story.append(
        Spacer(1, 6)
    )

    # ========================================================
    # 5. DETAILED COMMIT LOGS
    # ========================================================

    story.append(
        Paragraph(
            f"3. Detailed Commit Logs & Mentor Evaluation "
            f"({interval.capitalize()})",
            section_style,
        )
    )

    if not student_logs:

        story.append(
            Paragraph(
                "<i>No commit logs found for this timeframe.</i>",
                styles["Normal"],
            )
        )

    else:

        for student_name, logs in student_logs.items():

            student_section = []

            student_section.append(
                Paragraph(
                    f"<b>Student:</b> "
                    f"{html.escape(student_name)} "
                    f"— <i>{len(logs)} commit(s)</i>",
                    sub_section_style,
                )
            )

            # ------------------------------------------------
            # Table Header
            # ------------------------------------------------

            log_table_data = [
                [
                    "Date",
                    "Hash",
                    "Commit Message",
                    "Mentor Marks (/10)",
                ]
            ]

            # ------------------------------------------------
            # First commit
            # ------------------------------------------------

            first_date, first_sha, first_msg = logs[0]

            safe_msg = (
                html.escape(first_msg)
                if first_msg
                else "(No commit message)"
            )

            log_table_data.append(
                [
                    Paragraph(
                        first_date,
                        meta_cell_style,
                    ),
                    Paragraph(
                        f"<code>{html.escape(first_sha)}</code>",
                        meta_cell_style,
                    ),
                    Paragraph(
                        safe_msg,
                        msg_style,
                    ),
                    Paragraph(
                        "<b>_____ / 10</b>",
                        marks_style,
                    ),
                ]
            )

            # ------------------------------------------------
            # Remaining commits
            # ------------------------------------------------

            for (
                date_val,
                sha_val,
                msg_val,
            ) in logs[1:]:

                safe_msg = (
                    html.escape(msg_val)
                    if msg_val
                    else "(No commit message)"
                )

                log_table_data.append(
                    [
                        Paragraph(
                            date_val,
                            meta_cell_style,
                        ),
                        Paragraph(
                            f"<code>{html.escape(sha_val)}</code>",
                            meta_cell_style,
                        ),
                        Paragraph(
                            safe_msg,
                            msg_style,
                        ),
                        "",
                    ]
                )

            # ------------------------------------------------
            # Create commit table
            # ------------------------------------------------

            num_rows = len(log_table_data)

            log_table = Table(
                log_table_data,
                colWidths=[
                    65,
                    50,
                    335,
                    90,
                ],
            )

            table_style = [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#475569"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "LEFT",
                ),
                (
                    "ALIGN",
                    (3, 0),
                    (3, -1),
                    "CENTER",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2.5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2.5,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (2, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ],
                ),
            ]

            # ------------------------------------------------
            # Merge mentor marks column
            # ------------------------------------------------

            if num_rows > 1:

                table_style.extend(
                    [
                        (
                            "SPAN",
                            (3, 1),
                            (3, num_rows - 1),
                        ),
                        (
                            "VALIGN",
                            (3, 1),
                            (3, num_rows - 1),
                            "MIDDLE",
                        ),
                        (
                            "BACKGROUND",
                            (3, 1),
                            (3, num_rows - 1),
                            colors.HexColor("#FEF3C7"),
                        ),
                    ]
                )

            log_table.setStyle(
                TableStyle(table_style)
            )

            student_section.append(log_table)

            student_section.append(
                Spacer(1, 5)
            )

            story.append(
                KeepTogether(student_section)
            )

    # ========================================================
    # 6. SIGNATURES
    # ========================================================

    story.append(
        Spacer(1, 16)
    )

    mentor_cell = [
        Paragraph(
            "<b>Name:</b> ___________________________",
            sig_block_style,
        ),
        Paragraph(
            "<b>Designation:</b> Project Mentor",
            sig_block_style,
        ),
        Spacer(1, 6),
        Paragraph(
            "<b>Signature:</b> ________________________",
            sig_block_style,
        ),
    ]

    coordinator_cell = [
        Paragraph(
            "<b>Name:</b> ___________________________",
            sig_block_style,
        ),
        Paragraph(
            "<b>Designation:</b> Lab Coordinator",
            sig_block_style,
        ),
        Spacer(1, 6),
        Paragraph(
            "<b>Signature:</b> ________________________",
            sig_block_style,
        ),
    ]

    sig_table = Table(
        [
            [
                mentor_cell,
                coordinator_cell,
            ]
        ],
        colWidths=[
            270,
            270,
        ],
    )

    sig_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (0, -1),
                    0,
                ),
                (
                    "LEFTPADDING",
                    (1, 0),
                    (1, -1),
                    40,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(
        KeepTogether(sig_table)
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(story)

    # ========================================================
    # SUCCESS MESSAGE
    # ========================================================

    print(
        f"\n[SUCCESS] Generated: {doc_name}"
    )

    print(
        f" -> Found {len(students)} student(s) "
        f"and {total_commits} total commits."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) > 1:

        chosen_interval = (
            sys.argv[1].lower()
        )

    else:

        chosen_interval = "weekly"

    if chosen_interval not in [
        "weekly",
        "monthly",
        "final",
    ]:

        print(
            "Invalid option."
        )

        print(
            "Usage:"
        )

        print(
            "  python report.py weekly"
        )

        print(
            "  python report.py monthly"
        )

        print(
            "  python report.py final"
        )

        sys.exit(1)

    generate_pdf(chosen_interval)