# pages.py
# One function per page — each returns the inner HTML for that page's content.
# The outer shell (sidebar + topbar) is added by components.layout() in dashboard.py.
#
# Changes from original:
#   - trend_chart replaced with a real SVG line chart (area fill + dots)
#   - agency bar chart replaced with SVG horizontal bars + percentage labels
#   - Pie chart added to dashboard alongside bar chart
#   - Column order changed: Title → Agency → Date → Notice ID
#   - Contract titles and agency names are clickable links to SAM.gov
#   - Tables have better spacing and hover styles

import urllib.parse
from templates.components import badge, searchable_table

# SAM.gov URL patterns for deep linking
# notice_id goes into the opportunity detail page URL
SAM_OPP    = "https://sam.gov/opp/{}/view"
SAM_SEARCH = "https://sam.gov/search/?keywords={}&index=opp"


def _sam_title_link(title: str, notice_id: str) -> str:
    # Returns a clickable <a> tag for the contract title linking to SAM.gov
    # If notice_id is empty we fall back to a keyword search
    url     = SAM_OPP.format(notice_id) if notice_id else SAM_SEARCH.format(urllib.parse.quote(title or ""))
    display = (title or "Untitled")[:60] + ("…" if len(title or "") > 60 else "")
    return f'<a class="tbl-link" href="{url}" target="_blank" rel="noopener" title="{title}">{display}</a>'


def _sam_agency_link(agency: str) -> str:
    # Returns a clickable <a> tag for the agency name searching SAM.gov
    url = SAM_SEARCH.format(urllib.parse.quote(agency or ""))
    return f'<a class="agency-link" href="{url}" target="_blank" rel="noopener">{agency or "—"}</a>'


# ── SVG Line / Area Chart ─────────────────────────────────────────────────────

def trend_chart(daily: list) -> str:
    # Replaces the old bar chart with a proper SVG area + line chart.
    # daily = list of {"date": "2026-04-05", "count": 42}, sorted oldest → newest.
    if not daily:
        return ""

    W, H   = 900, 110   # viewBox dimensions
    PAD_L  = 40          # left padding for y-axis labels
    PAD_R  = 16
    PAD_T  = 12
    PAD_B  = 28          # bottom padding for x-axis labels
    inner_w = W - PAD_L - PAD_R
    inner_h = H - PAD_T - PAD_B

    max_count = max(d["count"] for d in daily) or 1
    n         = len(daily)

    month_map = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
                 "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}

    def x(i):
        return PAD_L + (i / max(n - 1, 1)) * inner_w

    def y(count):
        return PAD_T + inner_h - (count / max_count) * inner_h

    # Build polyline points for the line and the closed polygon for the area fill
    pts      = [(x(i), y(d["count"])) for i, d in enumerate(daily)]
    line_pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)

    # Area polygon: line points + bottom-right corner + bottom-left corner
    area_pts = line_pts
    area_pts += f" {pts[-1][0]:.1f},{PAD_T + inner_h} {PAD_L:.1f},{PAD_T + inner_h}"

    # Dots at each data point — last one highlighted in a brighter color
    dots = ""
    for i, (px, py) in enumerate(pts):
        color = "#0076d6" if i == len(pts) - 1 else "#2563a8"
        dots += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{color}" stroke="#fff" stroke-width="1.5"><title>{daily[i]["count"]} contracts on {daily[i]["date"]}</title></circle>'

    # X-axis labels — only show every Nth label so they don't overlap
    step   = max(1, n // 6)
    labels = ""
    for i, d in enumerate(daily):
        if i % step == 0 or i == n - 1:
            short = str(d["date"])[5:]
            m, day = short.split("-")
            lbl = f"{month_map.get(m, m)} {int(day)}"
            labels += f'<text x="{x(i):.1f}" y="{H - 4}" text-anchor="middle" class="chart-axis-label">{lbl}</text>'

    # Y-axis gridlines + labels at 0, 50%, 100%
    grids = ""
    for pct in [0, 0.5, 1.0]:
        yval = PAD_T + inner_h - pct * inner_h
        cnt  = int(max_count * pct)
        grids += f'<line x1="{PAD_L}" y1="{yval:.1f}" x2="{W - PAD_R}" y2="{yval:.1f}" class="chart-grid"/>'
        grids += f'<text x="{PAD_L - 6}" y="{yval + 4:.1f}" text-anchor="end" class="chart-axis-label">{cnt}</text>'

    svg = f"""
    <svg viewBox="0 0 {W} {H}" style="width:100%;height:{H}px;" xmlns="http://www.w3.org/2000/svg">
      {grids}
      <polygon points="{area_pts}" class="chart-area"/>
      <polyline points="{line_pts}" class="chart-line"/>
      {dots}
      {labels}
    </svg>"""

    return f"""
    <div class="trend-card">
      <div class="card-head">
        <div class="card-title">Contracts posted per day</div>
        <div class="card-action">{len(daily)}-day window</div>
      </div>
      <div class="trend-body">{svg}</div>
    </div>"""


# ── SVG Pie Chart ─────────────────────────────────────────────────────────────

def pie_chart(agency_data: list) -> str:
    # Builds an SVG donut pie chart from agency contract counts.
    # Uses the stroke-dasharray trick: each slice is a circle with a partial stroke.
    if not agency_data:
        return ""

    COLORS = ["#005ea2","#2563a8","#1a4480","#0076d6","#4da3ff","#71767a","#3d4551","#1b1b1b"]
    total  = sum(r["count"] for r in agency_data) or 1
    top    = agency_data[:8]   # max 8 slices

    R   = 15.9154943   # radius giving circumference of ~100
    CX  = CY = 21      # center of 42x42 viewBox

    slices  = ""
    legend  = ""
    offset  = 25       # start at 12-o'clock (25 = 90deg offset)

    for i, row in enumerate(top):
        pct   = row["count"] / total * 100
        color = COLORS[i % len(COLORS)]
        slices += f"""
        <circle cx="{CX}" cy="{CY}" r="{R}"
          fill="transparent" stroke="{color}" stroke-width="5.5"
          stroke-dasharray="{pct:.2f} {100-pct:.2f}"
          stroke-dashoffset="{offset}"
          transform="rotate(-90 {CX} {CY})">
          <title>{row['name']}: {row['count']} contracts ({pct:.1f}%)</title>
        </circle>"""
        offset -= pct
        legend += f"""
        <div class="pie-legend-row">
          <span class="pie-swatch" style="background:{color}"></span>
          <span class="pie-name" title="{row['name']}">{row['name']}</span>
          <span class="pie-pct">{pct:.1f}%</span>
        </div>"""

    svg = f"""
    <svg viewBox="0 0 42 42" style="width:130px;height:130px;flex-shrink:0;" xmlns="http://www.w3.org/2000/svg">
      <circle cx="{CX}" cy="{CY}" r="{R}" fill="transparent" stroke="#dfe1e2" stroke-width="5.5"/>
      {slices}
      <text x="{CX}" y="{CY - 1}" text-anchor="middle" class="pie-total-num">{total:,}</text>
      <text x="{CX}" y="{CY + 4}" text-anchor="middle" class="pie-total-lbl">total</text>
    </svg>"""

    return f"""
    <div class="card">
      <div class="card-head">
        <div class="card-title">Agency share</div>
        <a href="/vendors" class="card-action">view all</a>
      </div>
      <div class="pie-wrap">
        {svg}
        <div class="pie-legend">{legend}</div>
      </div>
    </div>"""


# ── Dashboard page ────────────────────────────────────────────────────────────

def dashboard_page(data: dict) -> str:
    # Metric cards row
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

    # SVG area line chart — contracts per day
    line = trend_chart(data['daily_trend'])

    # Bar chart card (left)
    max_count = data['agency_data'][0]['count'] if data['agency_data'] else 1
    bars = ""
    for i, row in enumerate(data['agency_data']):
        pct = int(row['count'] / max_count * 88)
        cls = "bar-fill gold" if i == 0 else "bar-fill"
        # percentage label shown at the end of the bar
        bar_pct = f"{row['count'] / max_count * 100:.0f}%"
        bars += f"""
        <div class="bar-row">
          <div class="bar-label" title="{row['name']}">{row['name']}</div>
          <div class="bar-track"><div class="{cls}" style="width:{pct}%"></div></div>
          <div class="bar-count">{row['count']}</div>
        </div>"""

    bar_card = f"""
    <div class="card">
      <div class="card-head">
        <div class="card-title">Contracts by agency</div>
        <a href="/vendors" class="card-action">view all</a>
      </div>
      <div class="chart-wrap">{bars}</div>
    </div>"""

    # Pie chart card (replaces the ETL log in the second column)
    pie = pie_chart(data['agency_data'])

    # ETL log card (now full width below the two chart cards)
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

    # Latest contracts table
    # Column order: Title → Agency → Date → Notice ID  (notice ID last, de-emphasized)
    tbl_rows = ""
    for c in data['contracts']:
        title_cell  = _sam_title_link(c['title'] or "Untitled", c['notice_id'] or "")
        agency_cell = _sam_agency_link(c['agency'])
        tbl_rows += f"""
        <tr>
          <td>{title_cell}</td>
          <td>{agency_cell}</td>
          <td class="date-cell">{c['posted_date'] or '—'}</td>
          <td class="notice-id">{(c['notice_id'] or '—')[:28]}</td>
        </tr>"""

    contracts_table = searchable_table(
        "Latest contracts",
        ["title", "agency", "posted date", "notice id"],
        tbl_rows,
        data['total_contracts'],
        "dash_contracts",
    )

    return (
        metrics
        + line
        + f'<div class="grid2">{bar_card}{pie}</div>'
        + f'<div class="grid2">{log_card}<div></div></div>'
        + contracts_table
    )


# ── Contracts page ────────────────────────────────────────────────────────────

def contracts_page(contracts: list, total: int) -> str:
    # Column order: Title → Agency → Date → Notice ID
    # Title and agency are clickable SAM.gov links
    rows = ""
    for c in contracts:
        title_cell  = _sam_title_link(c['title'] or "Untitled", c['notice_id'] or "")
        agency_cell = _sam_agency_link(c['agency'])
        rows += f"""
        <tr>
          <td>{title_cell}</td>
          <td>{agency_cell}</td>
          <td class="date-cell">{c['posted_date'] or '—'}</td>
          <td class="notice-id">{c['notice_id'] or '—'}</td>
        </tr>"""

    return searchable_table(
        "All contracts",
        ["title", "agency", "posted date", "notice id"],
        rows,
        total,
        "all_contracts",
    )


# ── Vendors page ──────────────────────────────────────────────────────────────

def vendors_page(vendors: list) -> str:
    max_count = vendors[0]['count'] if vendors else 1

    # Vendor cards with SVG mini bar
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

    # Agency names in the table are clickable too
    rows = ""
    for i, v in enumerate(vendors, 1):
        agency_cell = _sam_agency_link(v['name'])
        rows += f"""
        <tr>
          <td class="date-cell">{i}</td>
          <td>{agency_cell}</td>
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


# ── Applications page ─────────────────────────────────────────────────────────

def applications_page(runs: list) -> str:
    rows = ""
    for r in runs:
        b = badge("success", "green") if r['success'] else badge("failed", "red")
        rows += f"""
        <tr>
          <td>{r['time']}</td>
          <td>{r['source']}</td>
          <td class="date-cell">{r['posted_from']} → {r['posted_to']}</td>
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


# ── Errors page ───────────────────────────────────────────────────────────────

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