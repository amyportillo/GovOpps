# GovOpps

A data pipeline and dashboard for government contract opportunities pulled from the SAM.gov API.

The system fetches real contract data, cleans it, stores it in a PostgreSQL database, and displays it through a web dashboard and REST API.

---

## How to run everything

Once you've set up the project (see below), all you need is one command:

```bash
govopps
```

That's it. It will:
1. Pull the latest contracts from SAM.gov
2. Start the REST API at `http://localhost:8000/docs`
3. Open the dashboard at `http://localhost:8501`

To stop everything just press `Ctrl+C`.

---

## First time setup

**1. Clone the repo and go into the project folder**
```bash
cd GovOpps
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up your `.env` file**
```bash
cp config.example.py .env
```
Then open `.env` and fill in your SAM.gov API key and PostgreSQL credentials:
```
SAM_API_KEY=your_key_here
DB_NAME=gov_contracts_dw
DB_USER=postgres
DB_PASSWORD=your_password
```

**5. Add the `govopps` alias to your terminal**
```bash
echo "alias govopps='bash /path/to/GovOpps/start.sh'" >> ~/.zshrc
source ~/.zshrc
```

**6. Make sure PostgreSQL is running and the database exists**
```sql
CREATE DATABASE gov_contracts_dw;
```

---

## Running individual pieces

If you only want to run one part at a time:

```bash
python run.py etl          # fetch contracts from SAM.gov → save to database
python run.py api          # start the REST API only
python run.py dashboard    # start the dashboard only
```

---

## Project structure

```
GovOpps/
├── run.py            entry point — run etl, api, or dashboard
├── start.sh          script behind the govopps alias
├── etl.py            pulls data from SAM.gov, cleans it, loads into DB
├── api.py            FastAPI — REST endpoints for contracts, vendors, ETL history
├── dashboard.py      FastAPI — serves the visual dashboard on port 8501
├── database.py       SQLAlchemy ORM models + DB setup
├── schemas.py        Pydantic response shapes for the API
├── config.py         all settings, reads from .env
├── templates/
│   ├── styles.py     all CSS for the dashboard
│   ├── components.py shared layout (sidebar, topbar)
│   └── pages.py      one function per page (Dashboard, Contracts, Vendors, etc.)
└── .env              your secrets — never commit this
```

---

## What the dashboard shows

- **Dashboard** — metrics overview, contracts by agency, daily trend chart, ETL run history
- **Contracts** — full searchable table of all 1,000 contracts
- **Vendors** — all agencies with contract counts
- **Applications** — history of every ETL run
- **Error Log** — any errors caught during data fetching

---

## Notes

- The database keeps a rolling cap of **1,000 contracts** — when new ones come in, the oldest drop off automatically
- SAM.gov has a daily API rate limit, so running `govopps` multiple times in one day may hit the quota. The data in the DB stays intact even when that happens
- The API key in `.env` is personal — do not commit it to GitHub
