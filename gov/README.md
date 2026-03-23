# Gov Contracts - Python

This is a Python version of the SAM.gov data fetcher and API.
Built with: FastAPI + SQLAlchemy + PostgreSQL + httpx

## Setup

1. Create and activate a virtual environment

   Mac / Linux:
     python -m venv venv
     source venv/bin/activate

   Windows:
     python -m venv venv
     venv\Scripts\activate

2. Install dependencies
     pip install -r requirements.txt

3. Create your .env file
  Ill be providing what to put in the .env file 

## Running the ETL

This fetches contract data from SAM.gov and stores it:
    python etl.py

You should see something like:
    Database tables verified / created.
    Fetching SAM.gov data posted between 03/14/2026 and 03/21/2026...
    Status: 200
    Parsed and inserted 25 cleaned record(s).
    --- DATABASE SUMMARY ---
    Total raw JSON records : 1
    Total contract records : 25

---

## Running the API

Start the server:
    uvicorn api:app --reload --port 8000

Then go to: http://localhost:8000/docs
That's where you can test all the endpoints

---

## API Endpoints

GET /contracts
  Gets contract opportunities with agency names
  ?limit=N       max number of results, default 100, max 1000
  ?agency_id=N   only get contracts from one agency

GET /vendors
  Gets list of agencies with how many contracts each has
  ?search=word   search agency names (case doesn't matter)

GET /applications
  Gets history of when we ran the ETL
  ?limit=N       max results, default 50, max 500
