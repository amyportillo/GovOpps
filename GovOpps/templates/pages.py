# One function per page — each returns the inner content HTML.
# The layout shell (sidebar + topbar) is added by components.layout() in dashboard.py.

from templates.components import badge, searchable_table


def trend_chart(daily: list) -> str:
    # daily is a list of {"date": "2026-04-05", "count": 42} sorted oldest → newest
    if not daily:
        return ""

    max_count = max(d["count"] for d in daily) or 1
    bars = ""
    labels = ""
    for i, d in enumerate(daily):
        height = max(4, int(d["count"] / max_count * 80))  # min 4px so bar is always visible
        cls = "trend-bar gold" if i == len(daily) - 1 else "trend-bar"
        tooltip = f"{d['count']} contracts"
        # Show shortened date: "Apr 05"
        short = str(d["date"])[5:]  # "04-05"
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
    # --- metrics row ---
    metrics = f"""
    <div class="metrics">
      <div class="metric">
        <div class="metric-label">Total Contracts</div>
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
        <div class="metric-sub"><span class="metric-up">{data['success_rate']}</span> success rate</div>
      </div>
      <div class="metric">
        <div class="metric-label">Errors Logged</div>
        <div class="metric-value">{data['error_count']}</div>
        <div class="metric-sub">{'<span class="metric-down">needs review</span>' if data['error_count'] > 0 else 'all clear'}</div>
      </div>
    </div>"""

    # --- agency bar chart ---
    max_count = data['agency_data'][0]['count'] if data['agency_data'] else 1
    bars = ""
    for i, row in enumerate(data['agency_data']):
        pct = int(row['count'] / max_count * 88)
        cls = "bar-fill gold" if i == 0 else "bar-fill"
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

    # --- etl log ---
    log_rows = ""
    for r in data['etl_log']:
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
        data['total_contracts'],
        "dash_contracts",
    )

    return metrics + trend_chart(data['daily_trend']) + f'<div class="grid2">{chart_card}{log_card}</div>' + contracts_table


def contracts_page(contracts: list, total: int) -> str:
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
    max_count = vendors[0]['count'] if vendors else 1

    # vendor cards grid
    cards = ""
    for v in vendors:
        pct = int(v['count'] / max_count * 100)
        cards += f"""
        <div class="vendor-card">
          <div class="vendor-name" title="{v['name']}">{v['name']}</div>
          <div class="vendor-label">contracts</div>
          <div class="vendor-count">{v['count']:,}</div>
          <div class="mini-bar-track"><div class="mini-bar-fill" style="width:{pct}%"></div></div>
        </div>"""

    # also a full table below
    rows = ""
    for i, v in enumerate(vendors, 1):
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
    rows = ""
    for r in runs:
        b = badge("success", "green") if r['success'] else badge("failed", "red")
        rows += f"""
        <tr>
          <td>{r['time']}</td>
          <td>{r['source']}</td>
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
          <td>{badge(e['context'], 'amber')}</td>
          <td style="color:var(--red)">{e['message'][:120]}</td>
        </tr>"""

    return searchable_table(
        "Error log",
        ["logged at", "context", "message"],
        rows,
        len(errors),
        "errors_tbl",
    )
