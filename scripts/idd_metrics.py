"""idd_metrics.py — Intent Compression Ratio + token economics for the streetlights demo.

Token counts use SNOWFLAKE.CORTEX.COUNT_TOKENS (primary, requires configured snow CLI)
with tiktoken cl100k_base as offline fallback.

ICR score formula (per icr-lab): ICR = int(ops_achieved / nl_tokens * 1000)
Higher score = more operations achieved per intent token spent.

Usage:
    uv run idd-metrics                             # analyse all demo intents
    uv run idd-metrics --intent "your question"    # analyse a single custom intent
    uv run idd-metrics --model llama3.1-70b        # use a specific Cortex model
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import click

# (nl_query, routing_tool, traditional_ops, est_sql_tokens)
# traditional_ops  = discrete manual ops without this skill:
#                    SQL statements + bash commands + Python scripts + API calls
# est_sql_tokens   = approximate Cortex Analyst output size, based on observed patterns
DEMO_INTENTS: list[tuple[str, str, int, int]] = [
    ("How many street lights are currently faulty?", "Analyst", 5, 42),
    ("Which neighborhoods have the highest energy consumption?", "Analyst", 5, 58),
    ("What is the average repair cost by maintenance type?", "Analyst", 5, 54),
    ("Show me the top 5 neighborhoods by maintenance frequency", "Analyst", 4, 50),
    ("Predict energy consumption for the next 30 days", "Analyst (Forecast)", 5, 48),
    ("Find maintenance reports about exposed wires or sparking", "Search", 4, 38),
    ("What does the maintenance history say about pole integrity?", "Search", 3, 35),
    ("Tell me about maintenance issues in the busiest neighborhood", "Analyst+Search", 8, 85),
    ("What's the repair status for flickering light reports?", "Analyst+Search", 7, 78),
]

W_INTENT = 60
W_TOOL = 16
W_NL = 7
W_OPS = 9
W_SQL = 10
W_LEV = 11
W_ICR = 9


def _count_via_cortex(text: str, connection: str, model: str) -> int | None:
    safe = text.replace("'", "''")
    sql = f"SELECT SNOWFLAKE.CORTEX.COUNT_TOKENS('{model}', '{safe}') AS n;"
    try:
        result = subprocess.run(
            ["snow", "sql", "-q", sql, "-c", connection, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        return int(json.loads(result.stdout)[0]["N"])
    except Exception:
        return None


def _count_via_tiktoken(text: str) -> int:
    import tiktoken  # lazy — only if Cortex path unavailable

    return len(tiktoken.get_encoding("cl100k_base").encode(text))


def _resolve_connection() -> str | None:
    try:
        from scripts._manifest import find_project_root
        from scripts._manifest import load as load_manifest

        root = find_project_root(Path.cwd())
        manifest = load_manifest(root)
        return manifest.snowflake.connection or None
    except Exception:
        return None


def count_tokens(text: str, connection: str | None, model: str) -> tuple[int, str]:
    """Return (token_count, method_used)."""
    if connection:
        n = _count_via_cortex(text, connection, model)
        if n is not None:
            return n, "cortex"
    return _count_via_tiktoken(text), "tiktoken"


def _fmt_row(
    intent: str,
    tool: str,
    nl: int,
    ops: int | None,
    sql_est: int | None,
    icr_score: int | None,
) -> str:
    ops_str = str(ops) if ops is not None else "\u2014"
    sql_str = f"~{sql_est}" if sql_est is not None else "\u2014"
    lev_str = f"{sql_est / nl:.1f}" if sql_est else "\u2014"
    icr_str = str(icr_score) if icr_score is not None else "\u2014"
    return (
        f"  {intent:<{W_INTENT}}  {tool:<{W_TOOL}}"
        f"  {nl:>{W_NL}}  {ops_str:>{W_OPS}}"
        f"  {sql_str:>{W_SQL}}  {lev_str:>{W_LEV}}  {icr_str:>{W_ICR}}"
    )


@click.command()
@click.option("--intent", default=None, help="Single custom intent to analyse (NL query text)")
@click.option(
    "--model",
    default="mistral-large2",
    show_default=True,
    help="Cortex model for COUNT_TOKENS",
)
def main(intent: str | None, model: str) -> None:
    """Compute IDD metrics (ICR + token economics) for streetlights demo intents.

    ICR score = int(traditional_ops / nl_tokens * 1000)
    Higher score = more operations achieved per intent token spent (per icr-lab formula).
    """
    connection = _resolve_connection()
    if connection:
        method = f"SNOWFLAKE.CORTEX.COUNT_TOKENS  model={model}"
    else:
        method = (
            "tiktoken cl100k_base"
            " (offline \u2014 run '$streetlights-demo setup' for Cortex token counts)"
        )

    header = (
        f"  {'Intent':<{W_INTENT}}  {'Routes to':<{W_TOOL}}"
        f"  {'NL tok':>{W_NL}}  {'Trad ops':>{W_OPS}}"
        f"  {'SQL~est':>{W_SQL}}  {'SQL/NL tok':>{W_LEV}}  {'ICR score':>{W_ICR}}"
    )
    sep = "  " + "\u2500" * (len(header) - 2)

    click.echo()
    click.echo("  IDD Metrics \u2014 Streetlights Intelligence Demo")
    click.echo(
        "  ICR score = int(trad ops \u00d7 1000 \u00f7 NL tokens)"
        "  |  higher = more ops per intent token"
    )
    click.echo(f"  Token counter: {method}")
    click.echo()
    click.echo(header)
    click.echo(sep)

    if intent:
        nl_tokens, _ = count_tokens(intent, connection, model)
        click.echo(_fmt_row(intent[:W_INTENT], "custom", nl_tokens, None, None, None))
        click.echo()
        click.echo(
            f"  NL tokens: {nl_tokens}" "  (ops + SQL estimates require live Cortex execution)"
        )
        click.echo()
        return

    total_nl = total_ops = total_sql = total_icr = 0
    for nl_query, tool, ops, sql_est in DEMO_INTENTS:
        nl_tokens, _ = count_tokens(nl_query, connection, model)
        icr_score = int((ops / nl_tokens) * 1000)
        total_nl += nl_tokens
        total_ops += ops
        total_sql += sql_est
        total_icr += icr_score
        click.echo(_fmt_row(nl_query, tool, nl_tokens, ops, sql_est, icr_score))

    n = len(DEMO_INTENTS)
    avg_nl = total_nl // n
    avg_ops = total_ops // n
    avg_sql = total_sql // n
    avg_icr = total_icr // n
    avg_lev = total_sql / total_nl
    click.echo(sep)
    click.echo(
        f"  {'Averages (floor)':<{W_INTENT}}  {'':^{W_TOOL}}"
        f"  {avg_nl:>{W_NL}}  {avg_ops:>{W_OPS}}"
        f"  {avg_sql:>{W_SQL}}  {avg_lev:>{W_LEV - 1}.1f}  {avg_icr:>{W_ICR}}"
    )
    click.echo()
    click.echo(
        f"  Average ICR score: {avg_icr}"
        f"   Avg trad ops/invocation: {avg_ops}"
        f"   Avg SQL leverage: {avg_lev:.1f}"
    )
    click.echo()
    click.echo(
        "  Note: SQL token counts (~) are estimates based on observed Cortex Analyst patterns."
    )
    click.echo()
