# One function per page — each returns the inner HTML for that page's content.
# The outer shell (sidebar + topbar) is added by components.layout() in dashboard.py.
# These functions just build strings of HTML — no rendering engine, just f-strings.

from templates.components import badge, searchable_table


def trend_chart(daily: list) -> str:
    # Builds the "Contracts posted per day" bar chart as HTML.
    # daily = list of {"date": "2026-04-05", "count": 42}, sorted oldest → newest.
    if not daily:
        return ""  # don't render anything if there's no data yet

    # Find the tallest bar so we can scale all others relative to it (max = 80px tall)
    max_count = max(d["count"] for d in daily) or 1  # avoid division by zero
    bars = ""
    labels = ""

    for i, d in enumerate(daily):
        # Scale bar height between 4px (minimum so it's always visible) and 80px
        height = max(4, int(d["count"] / max_count * 80))

        # The last bar (most recent day) gets a brighter color to stand out
        cls = "trend-bar gold" if i == len(daily) - 1 else "trend-bar"

        # Tooltip shown on hover, e.g. "42 contracts"
        tooltip = f"{d['count']} contracts"

        # Convert "2026-04-05" → "Apr 05" for the label below the bar
        short = str(d["date"])[5:]  # grab just "04-05"
        month_map = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
                     "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}
        m, day = short.split("-")
        label = f"{month_map.get(m, m)} {day}"

        bars   += f'<div class="trend-bar-wrap"><div class="{cls}" style="height:{height}px" title="{tooltip}"></div></div>'
        labels += f'<div class="trend-label">{label}</div>'

    return f"""
    <div class="trend-card">
      <div class="card-head">
        <div class="card-title">Contracts posted per day</div>
        <div class="card-action">{len(daily)}-day window</div>
      </div>
      <div class="trend-body">
        <div class="trend-bars">{bars}</div>
      </div>
      <div class="trend-divider"></div>
      <div class="trend-labels">{labels}</div>
    </div>"""


def dashboard_page(data: dict) -> str:
    # Builds the full inner HTML for the main dashboard page.
    # data is the dict assembled in dashboard.py's dashboard() route.

    # --- metrics row: 4 stat boxes across the top ---
    metrics = f"""
    <div class="metrics">
      <div class="metric">
        <div class="metric-label">Total Contracts</div>
        <!-- :, formats numbers with commas, e.g. 1000 → 1,000 -->
        <div class="metric-value">{data['total_contracts']:,}</div>
        <div class="metric-sub">from SAM.gov</div>
      </div>
      <div class="metric">
        <div class="metric-label">Agencies</div>
        <div class="metric-value">{data['total_agencies']:,}</div>
        <div class="metric-sub">unique agencies</div>
      </div>
      <div class="metric">
        <div class="metric-label">ETL Runs</div>
        <div class="metric-value">{data['etl_runs']}</div>
        <!-- metric-up applies green color styling -->
        <div class="metric-sub"><span class="metric-up">{data['success_rate']}</span> success rate</div>
      </div>
      <div class="metric">
        <div class="metric-label">Errors Logged</div>
        <div class="metric-value">{data['error_count']}</div>
        <!-- Show "needs review" in red if there are errors, otherwise "all clear" -->
        <div class="metric-sub">{'<span class="metric-down">needs review</span>' if data['error_count'] > 0 else 'all clear'}</div>
      </div>
    </div>"""

    # --- horizontal bar chart: top agencies by contract count ---
    # The first agency is always the tallest bar, so we use its count as the 100% baseline
    max_count = data['agency_data'][0]['count'] if data['agency_data'] else 1
    bars = ""
    for i, row in enumerate(data['agency_data']):
        pct = int(row['count'] / max_count * 88)  # scale to max 88% width so labels have room
        cls = "bar-fill gold" if i == 0 else "bar-fill"  # highlight the top agency
        bars += f"""
        <div class="bar-row">
          <div class="bar-label" title="{row['name']}">{row['name']}</div>
          <div class="bar-track"><div class="{cls}" style="width:{pct}%"></div></div>
          <div class="bar-count">{row['count']}</div>
        </div>"""

    chart_card = f"""
    <div class="card">
      <div class="card-head">
        <div class="card-title">Contracts by agency</div>
        <a href="/vendors" class="card-action">view all</a>
      </div>
      <div class="chart-wrap">{bars}</div>
    </div>"""

    # --- recent ETL runs mini log ---
    log_rows = ""
    for r in data['etl_log']:
        # badge() returns a green "success" or red "failed" label
        b = badge("success", "green") if r['success'] else badge("failed", "red")
        log_rows += f"""
        <div class="log-row">
          <div class="log-time">{r['time']}</div>
          <div class="log-source">{r['source']}</div>
          {b}
        </div>"""

    log_card = f"""
    <div class="card">
      <div class="card-head">
        <div class="card-title">Recent ETL runs</div>
        <a href="/applications" class="card-action">view all</a>
      </div>
      <div class="mini-log">{log_rows}</div>
    </div>"""

    # --- latest contracts table ---
    tbl_rows = ""
    for c in data['contracts']:
        # Truncate long values so they don't break the table layout
        tbl_rows += f"""
        <tr>
          <td class="notice-id">{(c['notice_id'] or '—')[:28]}</td>
          <td>{(c['title'] or 'Untitled')[:55]}</td>
          <td>{c['agency'] or '—'}</td>
          <td>{c['posted_date'] or '—'}</td>
        </tr>"""

    contracts_table = searchable_table(
        "Latest contracts",
        ["notice id", "title", "agency", "posted date"],
        tbl_rows,
        data['total_contracts'],  # shows total in the footer, not just the 50 displayed
        "dash_contracts",         # unique table ID for the JS search function
    )

    # Stack everything vertically: metrics → trend chart → two-column cards → table
    return metrics + trend_chart(data['daily_trend']) + f'<div class="grid2">{chart_card}{log_card}</div>' + contracts_table


def contracts_page(contracts: list, total: int) -> str:
    # Builds the full contracts table with all columns.
    rows = ""
    for c in contracts:
        rows += f"""
        <tr>
          <td class="notice-id">{(c['notice_id'] or '—')}</td>
          <td>{c['title'] or 'Untitled'}</td>
          <td>{c['agency'] or '—'}</td>
          <td>{c['sol_num'] or '—'}</td>
          <td>{c['posted_date'] or '—'}</td>
        </tr>"""

    return searchable_table(
        "All contracts",
        ["notice id", "title", "agency", "solicitation #", "posted date"],
        rows,
        total,
        "all_contracts",
    )


def vendors_page(vendors: list) -> str:
    # Builds the vendors page — a grid of agency cards at the top,
    # then a full searchable table below.

    # The first vendor has the most contracts — use it as the 100% reference for bar widths
    max_count = vendors[0]['count'] if vendors else 1

    # Agency cards grid (top section)
    cards = ""
    for v in vendors:
        pct = int(v['count'] / max_count * 100)  # proportional bar width
        cards += f"""
        <div class="vendor-card">
          <!-- title attribute shows full name on hover if it's truncated -->
          <div class="vendor-name" title="{v['name']}">{v['name']}</div>
          <div class="vendor-label">contracts</div>
          <div class="vendor-count">{v['count']:,}</div>
          <!-- thin progress bar showing this agency's share of total contracts -->
          <div class="mini-bar-track"><div class="mini-bar-fill" style="width:{pct}%"></div></div>
        </div>"""

    # Full table below the cards (same data, different view)
    rows = ""
    for i, v in enumerate(vendors, 1):  # start=1 so rank numbers begin at 1
        rows += f"""
        <tr>
          <td>{i}</td>
          <td>{v['name']}</td>
          <td>{v['count']:,}</td>
        </tr>"""

    table = searchable_table(
        "All agencies",
        ["#", "agency name", "contracts"],
        rows,
        len(vendors),
        "vendors_tbl",
    )

    return f'<div class="vendor-grid">{cards}</div>' + table


def applications_page(runs: list) -> str:
    # Builds the ETL run history table.
    rows = ""
    for r in runs:
        b = badge("success", "green") if r['success'] else badge("failed", "red")
        rows += f"""
        <tr>
          <td>{r['time']}</td>
          <td>{r['source']}</td>
          <!-- Shows the date range that was requested, e.g. "03/29/2026 → 04/05/2026" -->
          <td>{r['posted_from']} → {r['posted_to']}</td>
          <td>{r['status_code']}</td>
          <td>{b}</td>
        </tr>"""

    return searchable_table(
        "ETL run history",
        ["fetched at", "source", "date range", "status code", "result"],
        rows,
        len(runs),
        "apps_tbl",
    )


def errors_page(errors: list) -> str:
    # Builds the error log table. Shows a friendly "all clear" message if there are no errors.
    if not errors:
        return """
        <div class="table-card" style="padding:40px;text-align:center;color:var(--text3)">
          No errors logged — everything looks good.
        </div>"""

    rows = ""
    for e in errors:
        rows += f"""
        <tr>
          <td>{e['time']}</td>
          <!-- amber badge for the error context (where it happened) -->
          <td>{badge(e['context'], 'amber')}</td>
          <!-- red text for the error message, truncated to 120 chars to avoid huge rows -->
          <td style="color:var(--red)">{e['message'][:120]}</td>
        </tr>"""

    return searchable_table(
        "Error log",
        ["logged at", "context", "message"],
        rows,
        len(errors),
        "errors_tbl",
    )
