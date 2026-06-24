"""
Report generation.

Produces three artifacts from a ValidationResult:

1. An HTML report (`*.html`) -- human-readable, styled, suitable for
   emailing or opening in a browser.
2. A "dashboard data" JSON file (`*_dashboard.json`) -- a compact,
   pre-aggregated payload meant to be consumed by a BI tool or a
   front-end dashboard widget.
3. A "metrics summary" JSON file (`*_metrics.json`) -- a flat,
   machine-friendly summary suitable for time-series tracking /
   alerting pipelines (e.g. feeding into Grafana, Datadog, etc.).

No external templating library is used (no Jinja2 dependency) to keep
the framework's dependency footprint minimal -- the HTML is built with
plain Python string formatting.
"""

import json
from html import escape
from pathlib import Path
from typing import Union

from .engine import ValidationResult
from .logger import get_logger
from .scoring import score_grade

logger = get_logger(__name__)

_SEVERITY_COLORS = {
    "HIGH": "#d64545",
    "MEDIUM": "#e0a020",
    "LOW": "#3a8fd6",
}

_SCORE_COLOR_THRESHOLDS = [
    (90, "#2e7d32"),
    (80, "#558b2f"),
    (70, "#e0a020"),
    (60, "#e0701e"),
    (0, "#d64545"),
]


def _score_color(score: float) -> str:
    for threshold, color in _SCORE_COLOR_THRESHOLDS:
        if score >= threshold:
            return color
    return "#d64545"


def _render_summary_cards(result: ValidationResult) -> str:
    score = result.score
    grade = score_grade(score.overall_score)
    color = _score_color(score.overall_score)
    return f"""
    <div class="cards">
      <div class="card">
        <div class="card-label">Overall Quality Score</div>
        <div class="card-value" style="color:{color}">{score.overall_score:.1f}<span class="card-suffix">/100 ({grade})</span></div>
      </div>
      <div class="card">
        <div class="card-label">Total Rows</div>
        <div class="card-value">{result.total_rows:,}</div>
      </div>
      <div class="card">
        <div class="card-label">Total Columns</div>
        <div class="card-value">{result.total_columns:,}</div>
      </div>
      <div class="card">
        <div class="card-label">Total Issues</div>
        <div class="card-value">{len(result.issues):,}</div>
      </div>
    </div>
    """


def _render_check_breakdown(result: ValidationResult) -> str:
    rows = []
    for check_type, check_score in sorted(
        result.score.per_check_score.items(), key=lambda kv: kv[1]
    ):
        count = result.score.per_check_count.get(check_type, 0)
        opp = result.score.total_opportunities.get(check_type, 0)
        bar_color = _score_color(check_score)
        rows.append(
            f"""
            <tr>
              <td>{escape(check_type)}</td>
              <td>{count:,}</td>
              <td>{opp:,}</td>
              <td>
                <div class="bar-track">
                  <div class="bar-fill" style="width:{check_score:.1f}%;background:{bar_color}"></div>
                </div>
                <span class="bar-label">{check_score:.1f}</span>
              </td>
            </tr>
            """
        )
    return f"""
    <h2>Score Breakdown by Check Type</h2>
    <table class="data-table">
      <thead>
        <tr><th>Check</th><th>Issues Found</th><th>Opportunities</th><th>Score</th></tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    """


def _render_column_summary(result: ValidationResult) -> str:
    rows = []
    for col, summary in result.column_summary.items():
        issue_counts = ", ".join(
            f"{k}: {v}" for k, v in summary["issue_counts"].items() if v
        ) or "-"
        rows.append(
            f"""
            <tr>
              <td>{escape(col)}</td>
              <td>{escape(str(summary['type']))}</td>
              <td>{'No' if summary['nullable'] else 'Yes'}</td>
              <td>{summary['total_issues']:,}</td>
              <td>{escape(issue_counts)}</td>
            </tr>
            """
        )
    return f"""
    <h2>Column Summary</h2>
    <table class="data-table">
      <thead>
        <tr><th>Column</th><th>Type</th><th>Required</th><th>Total Issues</th><th>Breakdown</th></tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    """


def _render_issue_log(result: ValidationResult, max_rows: int = 500) -> str:
    rows = []
    for issue in result.issues[:max_rows]:
        color = _SEVERITY_COLORS.get(issue.severity, "#888")
        rows.append(
            f"""
            <tr>
              <td><span class="badge" style="background:{color}">{escape(issue.severity)}</span></td>
              <td>{escape(issue.check_type)}</td>
              <td>{escape(str(issue.column))}</td>
              <td>{escape(str(issue.row_index))}</td>
              <td>{escape(issue.message)}</td>
              <td>{escape(str(issue.value)) if issue.value is not None else ''}</td>
            </tr>
            """
        )
    truncated_note = ""
    if len(result.issues) > max_rows:
        truncated_note = (
            f"<p class='note'>Showing first {max_rows:,} of "
            f"{len(result.issues):,} issues. See the JSON metrics export "
            f"for the full list.</p>"
        )
    return f"""
    <h2>Issue Log</h2>
    {truncated_note}
    <table class="data-table">
      <thead>
        <tr><th>Severity</th><th>Check</th><th>Column</th><th>Row</th><th>Message</th><th>Value</th></tr>
      </thead>
      <tbody>
        {''.join(rows) if rows else '<tr><td colspan="6">No issues found.</td></tr>'}
      </tbody>
    </table>
    """


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Report - {dataset_name}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    margin: 0; padding: 0; background: #f4f6f8; color: #1f2933;
  }}
  header {{
    background: #1f2933; color: #fff; padding: 24px 32px;
  }}
  header h1 {{ margin: 0 0 4px 0; font-size: 22px; }}
  header p {{ margin: 0; color: #cbd2d9; font-size: 13px; }}
  main {{ padding: 24px 32px 48px; max-width: 1100px; margin: 0 auto; }}
  .cards {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px;
  }}
  .card {{
    background: #fff; border-radius: 10px; padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .card-label {{ font-size: 12px; color: #7b8794; text-transform: uppercase; letter-spacing: .04em; }}
  .card-value {{ font-size: 28px; font-weight: 700; margin-top: 6px; }}
  .card-suffix {{ font-size: 14px; font-weight: 400; color: #7b8794; margin-left: 4px; }}
  h2 {{ font-size: 16px; margin: 32px 0 12px; color: #1f2933; }}
  table.data-table {{
    width: 100%; border-collapse: collapse; background: #fff;
    border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  table.data-table th, table.data-table td {{
    text-align: left; padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #e4e7eb;
  }}
  table.data-table th {{ background: #f4f6f8; color: #52606d; font-weight: 600; }}
  .bar-track {{ background: #e4e7eb; border-radius: 4px; height: 8px; width: 140px; display: inline-block; vertical-align: middle; }}
  .bar-fill {{ height: 8px; border-radius: 4px; }}
  .bar-label {{ margin-left: 8px; font-weight: 600; }}
  .badge {{
    color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;
  }}
  .note {{ color: #7b8794; font-size: 12px; font-style: italic; }}
  footer {{ text-align: center; color: #9aa5b1; font-size: 12px; padding: 24px; }}
</style>
</head>
<body>
<header>
  <h1>Data Quality Report &mdash; {dataset_name}</h1>
  <p>Generated {run_timestamp}</p>
</header>
<main>
  {summary_cards}
  {check_breakdown}
  {column_summary}
  {issue_log}
</main>
<footer>Generated by the Data Quality Framework</footer>
</body>
</html>
"""


def generate_html_report(result: ValidationResult, output_path: Union[str, Path]) -> Path:
    """Render a ValidationResult into a styled, standalone HTML report."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = _HTML_TEMPLATE.format(
        dataset_name=escape(result.dataset_name),
        run_timestamp=escape(result.run_timestamp),
        summary_cards=_render_summary_cards(result),
        check_breakdown=_render_check_breakdown(result),
        column_summary=_render_column_summary(result),
        issue_log=_render_issue_log(result),
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info("HTML report written to %s", output_path)
    return output_path


def generate_dashboard_data(result: ValidationResult, output_path: Union[str, Path]) -> Path:
    """Write a compact JSON payload intended for dashboard widgets/BI tools."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "dataset_name": result.dataset_name,
        "run_timestamp": result.run_timestamp,
        "overall_score": round(result.score.overall_score, 2),
        "grade": score_grade(result.score.overall_score),
        "total_rows": result.total_rows,
        "total_columns": result.total_columns,
        "total_issues": len(result.issues),
        "check_scores": {
            k: round(v, 2) for k, v in result.score.per_check_score.items()
        },
        "check_issue_counts": result.score.per_check_count,
        "issues_by_severity": {
            sev: sum(1 for i in result.issues if i.severity == sev)
            for sev in ("HIGH", "MEDIUM", "LOW")
        },
        "top_problem_columns": sorted(
            (
                {"column": col, "total_issues": s["total_issues"]}
                for col, s in result.column_summary.items()
            ),
            key=lambda x: x["total_issues"],
            reverse=True,
        )[:10],
    }

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Dashboard data written to %s", output_path)
    return output_path


def generate_metrics_summary(result: ValidationResult, output_path: Union[str, Path]) -> Path:
    """Write the full machine-readable metrics summary (includes every issue)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    logger.info("Metrics summary written to %s", output_path)
    return output_path
