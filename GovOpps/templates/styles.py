# styles.py
# All CSS for the dashboard — injected into every page via components.layout().
# Updated to add:
#   - SVG line/area chart styles (.chart-line, .chart-area, .chart-grid, .chart-axis-label)
#   - SVG pie/donut chart styles (.pie-wrap, .pie-legend, .pie-swatch, etc.)
#   - Clickable link styles (.tbl-link, .agency-link)
#   - Better table styles (.date-cell, improved hover)
#   - All original styles preserved exactly

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#112e51;
  --navy2:#1a4480;
  --navy3:#2563a8;
  --blue:#005ea2;
  --blue2:#0076d6;
  --red:#b50909;
  --green:#008817;
  --gold:#8f6c00;
  --gold-bg:#faf3d1;
  --slate:#dfe1e2;
  --slate2:#f0f0f0;
  --white:#ffffff;
  --text:#1b1b1b;
  --text2:#3d4551;
  --text3:#71767a;
  --border:#dfe1e2;
  --sans:system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
}
html,body{height:100%;font-family:var(--sans);font-size:14px;background:var(--slate2);color:var(--text);line-height:1.5}
a{text-decoration:none;color:inherit}

/* ── Layout ── */
.layout{display:grid;grid-template-columns:240px 1fr;min-height:100vh}

/* ── Sidebar ── */
.sidebar{background:var(--navy);display:flex;flex-direction:column;position:sticky;top:0;height:100vh}
.logo{padding:24px 20px 18px;border-bottom:1px solid rgba(255,255,255,0.1)}
.logo-flag{display:flex;gap:3px;margin-bottom:10px}
.logo-flag span{display:block;height:4px;border-radius:1px}
.logo-flag .r{background:#b22234;flex:3}
.logo-flag .w{background:#fff;flex:2}
.logo-flag .b{background:#3c3b6e;flex:2}
.logo-title{font-size:16px;font-weight:700;color:#fff;letter-spacing:0.2px}
.logo-sub{font-size:11px;color:rgba(255,255,255,0.5);margin-top:2px;letter-spacing:0.3px}
.nav{padding:16px 0;flex:1}
.nav-label{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.35);padding:0 20px;margin-bottom:6px;margin-top:18px;font-weight:600}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 20px;font-size:13px;color:rgba(255,255,255,0.65);border-left:3px solid transparent;cursor:pointer;transition:all 0.12s}
.nav-item:hover{color:#fff;background:rgba(255,255,255,0.07)}
.nav-item.active{color:#fff;background:rgba(0,94,162,0.35);border-left:3px solid #4da3ff}
.nav-dot{width:5px;height:5px;border-radius:50%;background:currentColor;opacity:0.5;flex-shrink:0}
.nav-item.active .nav-dot{background:#4da3ff;opacity:1}
.sidebar-footer{padding:16px 20px;border-top:1px solid rgba(255,255,255,0.1)}
.sidebar-footer-text{font-size:11px;color:rgba(255,255,255,0.35);line-height:1.7}

/* ── Topbar ── */
.main{overflow-y:auto;display:flex;flex-direction:column}
.topbar{background:var(--white);border-bottom:2px solid var(--blue);padding:0 32px;height:58px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.page-title{font-size:18px;font-weight:700;color:var(--navy);letter-spacing:0.1px}
.topbar-right{display:flex;align-items:center;gap:12px}
.etl-badge{font-size:11px;color:var(--green);background:#ecf3ec;padding:4px 12px;border-radius:2px;border:1px solid #a9d4a9;font-weight:600;letter-spacing:0.2px}
.etl-badge span{color:var(--text3);font-weight:400;margin-right:4px}
.content{padding:28px 32px;flex:1}

/* ── Metrics ── */
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px}
.metric{background:var(--white);border-radius:2px;border:1px solid var(--border);border-top:3px solid var(--blue);padding:16px 18px}
.metric-label{font-size:11px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;color:var(--text2);margin-bottom:8px}
.metric-value{font-size:30px;font-weight:700;color:var(--navy)}
.metric-sub{font-size:11px;color:var(--text3);margin-top:5px}
.metric-up{color:var(--green);font-weight:600}
.metric-down{color:var(--red);font-weight:600}

/* ── Cards ── */
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}
.card{background:var(--white);border-radius:2px;border:1px solid var(--border);overflow:hidden}
.card-head{padding:14px 18px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:#f8f9fa}
.card-title{font-size:12px;font-weight:700;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px}
.card-action{font-size:11px;color:var(--blue);font-weight:600}
.card-action:hover{text-decoration:underline}
.chart-wrap{padding:16px 18px}

/* ── Bar chart ── */
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.bar-label{font-size:11px;color:var(--text2);width:140px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{flex:1;height:10px;background:var(--slate);border-radius:1px;overflow:hidden}
.bar-fill{height:100%;background:var(--navy2)}
.bar-fill.gold{background:var(--blue)}
.bar-count{font-size:11px;color:var(--text3);width:36px;text-align:right;flex-shrink:0;font-weight:600}

/* ── SVG line/area chart ── */
.trend-card{background:var(--white);border-radius:2px;border:1px solid var(--border);overflow:hidden;margin-bottom:24px}
.trend-body{padding:16px 20px 8px}
.chart-line{fill:none;stroke:#005ea2;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.chart-area{fill:#005ea2;fill-opacity:0.08}
.chart-grid{stroke:#dfe1e2;stroke-width:0.5;stroke-dasharray:3,3}
.chart-axis-label{font-size:9px;fill:#71767a;font-family:system-ui,sans-serif}
/* donut total text inside pie */
.pie-total-num{font-size:6px;font-weight:700;fill:#112e51;font-family:system-ui,sans-serif}
.pie-total-lbl{font-size:3px;fill:#71767a;font-family:system-ui,sans-serif}

/* ── Pie chart layout ── */
.pie-wrap{display:flex;align-items:center;gap:20px;padding:16px 18px}
.pie-legend{display:flex;flex-direction:column;gap:7px;flex:1;min-width:0}
.pie-legend-row{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text2)}
.pie-swatch{width:9px;height:9px;border-radius:1px;flex-shrink:0}
.pie-name{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pie-pct{color:var(--text3);font-size:10px;font-weight:600;flex-shrink:0}

/* ── ETL log ── */
.mini-log{padding:4px 0}
.log-row{display:flex;align-items:center;gap:12px;padding:10px 18px;border-bottom:1px solid var(--border);font-size:12px}
.log-row:last-child{border-bottom:none}
.log-time{color:var(--text3);width:145px;flex-shrink:0}
.log-source{color:var(--text2);flex:1;font-weight:500}

/* ── Tables ── */
.table-card{background:var(--white);border-radius:2px;border:1px solid var(--border);overflow:hidden;margin-bottom:24px}
.table-head-row{padding:12px 18px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:12px;background:#f8f9fa}
.search-bar{font-family:var(--sans);font-size:12px;background:var(--white);border:1px solid #71767a;border-radius:2px;padding:7px 12px;color:var(--text);width:260px;outline:none}
.search-bar:focus{border-color:var(--blue);box-shadow:0 0 0 2px rgba(0,94,162,0.2)}
table{width:100%;border-collapse:collapse;font-size:13px}
thead tr{background:var(--slate2)}
th{padding:10px 16px;text-align:left;font-size:11px;letter-spacing:0.8px;text-transform:uppercase;color:var(--text2);font-weight:700;border-bottom:2px solid var(--border)}
td{padding:12px 16px;border-bottom:1px solid var(--border);color:var(--text2);vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#f0f7ff}
/* notice_id is now last and de-emphasized */
.notice-id{color:var(--text3);font-size:11px;font-family:monospace}
/* date column consistent width */
.date-cell{white-space:nowrap;color:var(--text3);font-size:12px}
.table-footer{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-top:1px solid var(--border);font-size:11px;color:var(--text3);background:#f8f9fa}

/* ── Clickable links in tables (requirements #4) ── */
/* Title link — dark navy, underline on hover, gold accent */
.tbl-link{color:var(--navy);font-weight:500;text-decoration:none;border-bottom:1px solid transparent;transition:color 0.15s,border-color 0.15s}
.tbl-link:hover{color:var(--blue);border-bottom-color:var(--blue)}
/* Agency link — quieter, muted blue */
.agency-link{color:var(--navy3);font-size:12px;text-decoration:none}
.agency-link:hover{text-decoration:underline;color:var(--blue)}

/* ── Badges ── */
.badge{display:inline-block;font-size:10px;padding:2px 8px;border-radius:2px;font-weight:700;letter-spacing:0.4px;text-transform:uppercase}
.badge-green{background:#ecf3ec;color:#1a6b1a;border:1px solid #a9d4a9}
.badge-red{background:#fde8e8;color:#8b0000;border:1px solid #f4b8b8}
.badge-blue{background:#e8f1fa;color:#003f73;border:1px solid #99c3e8}
.badge-gray{background:var(--slate);color:var(--text3);border:1px solid #c6cace}
.badge-amber{background:var(--gold-bg);color:var(--gold);border:1px solid #e6c84b}

/* ── Vendors grid ── */
.vendor-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}
.vendor-card{background:var(--white);border-radius:2px;border:1px solid var(--border);border-top:3px solid var(--navy2);padding:16px 18px}
.vendor-name{font-size:13px;font-weight:700;color:var(--navy);margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vendor-count{font-size:24px;font-weight:700;color:var(--navy)}
.vendor-label{font-size:11px;color:var(--text3);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.4px}
.mini-bar-track{width:100%;height:4px;background:var(--slate);overflow:hidden;margin-top:10px}
.mini-bar-fill{height:100%;background:var(--navy2)}
"""