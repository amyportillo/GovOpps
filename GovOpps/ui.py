# ui.py
# All the HTML and CSS for the dashboard.
# Each function returns an HTML string — dashboard.py calls them with real data.

# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#0c1f3f;--navy2:#152b52;--navy3:#1e3a6e;
  --gold:#c9a84c;--gold2:#e8c96a;
  --slate:#e8edf5;--slate2:#f4f6fa;
  --text:#0c1f3f;--text2:#4a5568;--text3:#8a94a6;
  --green:#1d9e75;--red:#e24b4a;--blue:#378add;
  --border:rgba(12,31,63,0.1);
  --mono: ui-monospace,'SF Mono','Cascadia Code','Fira Mono',monospace;
  --serif: 'New York','Iowan Old Style',Georgia,serif;
}
body{font-family:var(--mono);background:var(--slate2);color:var(--text)}
.layout{display:grid;grid-template-columns:220px 1fr;min-height:100vh}
.sidebar{background:var(--navy);display:flex;flex-direction:column}
.logo{padding:28px 24px 20px;border-bottom:1px solid rgba(255,255,255,0.08)}
.logo-title{font-family:var(--serif);font-size:18px;font-weight:600;color:#fff;letter-spacing:-0.3px}
.logo-sub{font-size:10px;color:rgba(255,255,255,0.4);letter-spacing:1.5px;text-transform:uppercase;margin-top:3px}
.nav{padding:20px 0;flex:1}
.nav-label{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,0.3);padding:0 24px;margin-bottom:8px;margin-top:16px}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 24px;font-size:12px;color:rgba(255,255,255,0.55);border-left:2px solid transparent}
.nav-item.active{color:#fff;background:rgba(201,168,76,0.12);border-left:2px solid var(--gold)}
.nav-dot{width:6px;height:6px;border-radius:50%;background:currentColor;opacity:0.6}
.nav-item.active .nav-dot{background:var(--gold);opacity:1}
.sidebar-footer{padding:20px 24px;border-top:1px solid rgba(255,255,255,0.08)}
.sidebar-footer-text{font-size:10px;color:rgba(255,255,255,0.3);line-height:1.8}
.main{background:var(--slate2)}
.topbar{background:#fff;border-bottom:1px solid var(--border);padding:0 32px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}
.page-title{font-family:var(--serif);font-size:20px;font-weight:600;color:var(--navy);letter-spacing:-0.3px}
.topbar-right{display:flex;align-items:center;gap:16px}
.etl-badge{font-size:10px;color:var(--green);background:#eaf3de;padding:5px 12px;border-radius:20px;border:1px solid rgba(29,158,117,0.2)}
.etl-badge span{color:var(--text3);margin-right:4px}
.content{padding:28px 32px}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:28px}
.metric{background:#fff;border-radius:10px;border:1px solid var(--border);padding:18px 20px}
.metric-label{font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--text3);margin-bottom:10px}
.metric-value{font-family:var(--serif);font-size:28px;font-weight:600;color:var(--navy);letter-spacing:-1px}
.metric-sub{font-size:10px;color:var(--text3);margin-top:6px}
.metric-up{color:var(--green)}.metric-down{color:var(--red)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}
.card{background:#fff;border-radius:10px;border:1px solid var(--border);overflow:hidden}
.card-head{padding:18px 20px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.card-title{font-size:12px;font-weight:500;color:var(--navy);letter-spacing:0.3px}
.card-action{font-size:10px;color:var(--blue)}
.chart-wrap{padding:16px 20px}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.bar-label{font-size:10px;color:var(--text2);width:130px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{flex:1;height:8px;background:var(--slate);border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;background:var(--navy3)}
.bar-fill.gold{background:var(--gold)}
.bar-count{font-size:10px;color:var(--text3);width:28px;text-align:right}
.mini-log{padding:4px 0}
.log-row{display:flex;align-items:center;gap:12px;padding:10px 20px;border-bottom:1px solid rgba(12,31,63,0.05);font-size:11px}
.log-row:last-child{border-bottom:none}
.log-time{color:var(--text3);width:150px;flex-shrink:0}
.log-source{color:var(--text2);flex:1}
.table-card{background:#fff;border-radius:10px;border:1px solid var(--border);overflow:hidden;margin-bottom:24px}
.table-head-row{padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.search-bar{font-family:var(--mono);font-size:11px;background:var(--slate2);border:1px solid var(--border);border-radius:6px;padding:7px 14px;color:var(--text);width:240px;outline:none}
table{width:100%;border-collapse:collapse;font-size:11px}
thead tr{background:var(--slate2)}
th{padding:10px 16px;text-align:left;font-size:9px;letter-spacing:1.2px;text-transform:uppercase;color:var(--text3);font-weight:500;border-bottom:1px solid var(--border)}
td{padding:13px 16px;border-bottom:1px solid rgba(12,31,63,0.05);color:var(--text2)}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--slate2)}
.notice-id{color:var(--navy3);font-weight:500}
.badge{display:inline-block;font-size:9px;padding:3px 9px;border-radius:20px;font-weight:500}
.badge-green{background:#eaf3de;color:#0f6e56}
.badge-red{background:#fde8e8;color:#9b1c1c}
.badge-blue{background:#e6f1fb;color:#185fa5}
.badge-gray{background:var(--slate);color:var(--text3)}
.table-footer{display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-top:1px solid var(--border)}
.page-info{font-size:10px;color:var(--text3)}

/* hide streamlit chrome */
#MainMenu,footer,header[data-testid="stHeader"],.stDeployButton{display:none !important}
.stMainBlockContainer,.block-container{padding:0 !important;max-width:100% !important}
div[data-testid="stVerticalBlock"]{gap:0 !important}
"""


# ── Components ────────────────────────────────────────────────────────────────

def sidebar(last_sync: str) -> str:
    return f"""
    <div class="sidebar">
      <div class="logo">
        <div class="logo-title">GovOpps</div>
        <div class="logo-sub">Contract Intelligence</div>
      </div>
      <div class="nav">
        <div class="nav-label">Main</div>
        <div class="nav-item active"><div class="nav-dot"></div>Dashboard</div>
        <div class="nav-item"><div class="nav-dot"></div>Contracts</div>
        <div class="nav-item"><div class="nav-dot"></div>Vendors</div>
        <div class="nav-label">System</div>
        <div class="nav-item"><div class="nav-dot"></div>Applications</div>
        <div class="nav-item"><div class="nav-dot"></div>Error Log</div>
      </div>
      <div class="sidebar-footer">
        <div class="sidebar-footer-text">SAM.gov pipeline<br>Last sync: {last_sync}</div>
      </div>
    </div>"""


def metrics(total_contracts: int, total_agencies: int, etl_runs: int, error_count: int, success_rate: str) -> str:
    return f"""
    <div class="metrics">
      <div class="metric">
        <div class="metric-label">Total Contracts</div>
        <div class="metric-value">{total_contracts:,}</div>
        <div class="metric-sub">from SAM.gov</div>
      </div>
      <div class="metric">
        <div class="metric-label">Agencies</div>
        <div class="metric-value">{total_agencies:,}</div>
        <div class="metric-sub">unique agencies</div>
      </div>
      <div class="metric">
        <div class="metric-label">ETL Runs</div>
        <div class="metric-value">{etl_runs}</div>
        <div class="metric-sub"><span class="metric-up">{success_rate}</span> success rate</div>
      </div>
      <div class="metric">
        <div class="metric-label">Errors Logged</div>
        <div class="metric-value">{error_count}</div>
        <div class="metric-sub">{'<span class="metric-down">needs review</span>' if error_count > 0 else 'all clear'}</div>
      </div>
    </div>"""


def agency_chart(agency_data: list) -> str:
    max_count = agency_data[0]["count"] if agency_data else 1
    rows = ""
    for i, row in enumerate(agency_data[:6]):
        pct = int(row["count"] / max_count * 88)
        css_class = "gold" if i == 0 else ""
        rows += f"""
        <div class="bar-row">
          <div class="bar-label" title="{row['name']}">{row['name']}</div>
          <div class="bar-track"><div class="bar-fill {css_class}" style="width:{pct}%"></div></div>
          <div class="bar-count">{row['count']}</div>
        </div>"""
    return f"""
    <div class="card">
      <div class="card-head">
        <div class="card-title">Contracts by agency</div>
        <div class="card-action">top 6</div>
      </div>
      <div class="chart-wrap">{rows}</div>
    </div>"""


def etl_log(runs: list) -> str:
    rows = ""
    for run in runs[:6]:
        badge = '<span class="badge badge-green">success</span>' if run["success"] else '<span class="badge badge-red">failed</span>'
        rows += f"""
        <div class="log-row">
          <div class="log-time">{run['time']}</div>
          <div class="log-source">{run['source']}</div>
          {badge}
        </div>"""
    return f"""
    <div class="card">
      <div class="card-head">
        <div class="card-title">Recent ETL runs</div>
        <div class="card-action">view all</div>
      </div>
      <div class="mini-log">{rows}</div>
    </div>"""


def contracts_table(contracts: list, total: int) -> str:
    rows = ""
    for c in contracts:
        notice  = c.get("notice_id") or "—"
        title   = c.get("title") or "Untitled"
        agency  = c.get("agency") or "—"
        date    = c.get("posted_date") or "—"
        rows += f"""
        <tr>
          <td class="notice-id">{notice[:24]}</td>
          <td>{title[:60]}</td>
          <td>{agency[:35]}</td>
          <td>{date}</td>
        </tr>"""

    # inline JS so search filters rows without a page reload
    js = """
    <script>
    function filterRows(val) {
      val = val.toLowerCase();
      document.querySelectorAll('#ctable tbody tr').forEach(function(row) {
        row.style.display = row.textContent.toLowerCase().includes(val) ? '' : 'none';
      });
    }
    </script>"""

    return f"""
    {js}
    <div class="table-card">
      <div class="table-head-row">
        <div class="card-title">Latest contracts</div>
        <input class="search-bar" placeholder="search by title or agency..." oninput="filterRows(this.value)">
      </div>
      <table id="ctable">
        <thead><tr><th>notice id</th><th>title</th><th>agency</th><th>posted date</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div class="table-footer">
        <div class="page-info">showing {len(contracts)} of {total:,} contracts</div>
      </div>
    </div>"""


# ── Page assembly ─────────────────────────────────────────────────────────────

def render_page(data: dict) -> str:
    return f"""
    <style>{CSS}</style>
    <div class="layout">
      {sidebar(data['last_sync'])}
      <div class="main">
        <div class="topbar">
          <div class="page-title">Dashboard</div>
          <div class="topbar-right">
            <div class="etl-badge"><span>pipeline</span>{data['pipeline_status']}</div>
          </div>
        </div>
        <div class="content">
          {metrics(data['total_contracts'], data['total_agencies'], data['etl_runs'], data['error_count'], data['success_rate'])}
          <div class="grid2">
            {agency_chart(data['agency_data'])}
            {etl_log(data['etl_log'])}
          </div>
          {contracts_table(data['contracts'], data['total_contracts'])}
        </div>
      </div>
    </div>"""
