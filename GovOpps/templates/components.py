# Shared layout shell used by every page.
# Pass the active page name so the sidebar highlights the right item.

from templates.styles import CSS


def layout(active: str, title: str, content: str, last_sync: str = "", pipeline_status: str = "idle") -> str:

    def nav(label, href, page_id):
        cls = "nav-item active" if active == page_id else "nav-item"
        return f'<a href="{href}" class="{cls}"><div class="nav-dot"></div>{label}</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>GovOpps — {title}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="layout">

  <div class="sidebar">
    <div class="logo">
      <div class="logo-flag"><span class="r"></span><span class="w"></span><span class="b"></span></div>
      <div class="logo-title">GovOpps</div>
      <div class="logo-sub">Government Contract Data</div>
    </div>
    <div class="nav">
      <div class="nav-label">Main</div>
      {nav('Dashboard',    '/',             'dashboard')}
      {nav('Contracts',    '/contracts',    'contracts')}
      {nav('Vendors',      '/vendors',      'vendors')}
      <div class="nav-label">System</div>
      {nav('Applications', '/applications', 'applications')}
      {nav('Error Log',    '/errors',       'errors')}
    </div>
    <div class="sidebar-footer">
      <div class="sidebar-footer-text">SAM.gov pipeline<br>Last sync: {last_sync}</div>
    </div>
  </div>

  <div class="main">
    <div class="topbar">
      <div class="page-title">{title}</div>
      <div class="topbar-right">
        <div class="etl-badge"><span>pipeline</span>{pipeline_status}</div>
      </div>
    </div>
    <div class="content">
      {content}
    </div>
  </div>

</div>
</body>
</html>"""


def badge(text: str, color: str = "gray") -> str:
    return f'<span class="badge badge-{color}">{text}</span>'


def searchable_table(card_title: str, headers: list, rows: str, total: int, table_id: str = "tbl") -> str:
    header_html = "".join(f"<th>{h}</th>" for h in headers)
    return f"""
    <script>
    function filter_{table_id}(val) {{
      val = val.toLowerCase();
      document.querySelectorAll('#{table_id} tbody tr').forEach(function(r) {{
        r.style.display = r.textContent.toLowerCase().includes(val) ? '' : 'none';
      }});
    }}
    </script>
    <div class="table-card">
      <div class="table-head-row">
        <div class="card-title">{card_title}</div>
        <input class="search-bar" placeholder="search..." oninput="filter_{table_id}(this.value)">
      </div>
      <table id="{table_id}">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div class="table-footer"><span>{total} total records</span></div>
    </div>"""
