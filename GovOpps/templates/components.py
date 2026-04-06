# Shared layout shell and reusable UI components used by every page.
# Pass the active page name so the sidebar highlights the right nav item.

from templates.styles import CSS  # the giant CSS string that styles everything


def layout(active: str, title: str, content: str, last_sync: str = "", pipeline_status: str = "idle") -> str:
    # Builds the full HTML page — sidebar, topbar, and content area.
    # Every dashboard route calls this to wrap its inner HTML in the shared chrome.
    #
    # active          = page ID to highlight in the nav (e.g. "contracts")
    # title           = shown in the browser tab and the topbar
    # content         = the inner HTML produced by one of the pages.py functions
    # last_sync       = timestamp of the last ETL run, shown in the sidebar footer
    # pipeline_status = shown as a badge in the topbar ("running" or "no runs yet")

    def nav(label, href, page_id):
        # Generates a single sidebar nav link.
        # Adds the "active" CSS class if this is the current page — makes it highlighted.
        cls = "nav-item active" if active == page_id else "nav-item"
        return f'<a href="{href}" class="{cls}"><div class="nav-dot"></div>{label}</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>GovOpps — {title}</title>
  <!-- All CSS is inlined here — no separate stylesheet file needed -->
  <style>{CSS}</style>
</head>
<body>
<div class="layout">

  <!-- Left sidebar with logo and navigation links -->
  <div class="sidebar">
    <div class="logo">
      <!-- Three-stripe flag graphic — red, white, blue -->
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
    <!-- Shows when the ETL last ran — updated on every page load -->
    <div class="sidebar-footer">
      <div class="sidebar-footer-text">SAM.gov pipeline<br>Last sync: {last_sync}</div>
    </div>
  </div>

  <!-- Right side: topbar + scrollable content area -->
  <div class="main">
    <div class="topbar">
      <div class="page-title">{title}</div>
      <div class="topbar-right">
        <!-- Small badge showing whether the pipeline has run -->
        <div class="etl-badge"><span>pipeline</span>{pipeline_status}</div>
      </div>
    </div>
    <!-- This is where each page's unique content gets injected -->
    <div class="content">
      {content}
    </div>
  </div>

</div>
</body>
</html>"""


def badge(text: str, color: str = "gray") -> str:
    # Returns a small colored label — used for success/failed/error status indicators.
    # color options: "green", "red", "amber", "blue", "gray"
    # Example output: <span class="badge badge-green">success</span>
    return f'<span class="badge badge-{color}">{text}</span>'


def searchable_table(card_title: str, headers: list, rows: str, total: int, table_id: str = "tbl") -> str:
    # Builds a card containing a table with a live search box above it.
    # Typing in the search box instantly hides rows that don't match — no page reload needed.
    #
    # card_title = text shown above the table, e.g. "All contracts"
    # headers    = list of column header strings, e.g. ["title", "agency", "date"]
    # rows       = pre-built HTML string of <tr>...</tr> rows
    # total      = number shown in the footer, e.g. "247 total records"
    # table_id   = unique ID for the <table> element — must be unique per page if multiple tables

    header_html = "".join(f"<th>{h}</th>" for h in headers)

    return f"""
    <!-- Inline JavaScript for the search filter — no external JS library needed -->
    <script>
    function filter_{table_id}(val) {{
      val = val.toLowerCase();
      // Loop over every row in this table's tbody and show/hide based on whether
      // the row's full text content contains the search string
      document.querySelectorAll('#{table_id} tbody tr').forEach(function(r) {{
        r.style.display = r.textContent.toLowerCase().includes(val) ? '' : 'none';
      }});
    }}
    </script>
    <div class="table-card">
      <div class="table-head-row">
        <div class="card-title">{card_title}</div>
        <!-- oninput fires on every keystroke, calling the filter function above -->
        <input class="search-bar" placeholder="search..." oninput="filter_{table_id}(this.value)">
      </div>
      <table id="{table_id}">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div class="table-footer"><span>{total} total records</span></div>
    </div>"""
