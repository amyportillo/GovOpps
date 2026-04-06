# run.py
# The single entry point for this project.
# Every command you need is here — no digging through other files.
#
# Usage:
#   python run.py etl          <- fetch contracts from SAM.gov and load into the DB
#   python run.py api          <- start the FastAPI server (http://localhost:8000/docs)
#   python run.py dashboard    <- open the Streamlit dashboard (http://localhost:8501)

import sys
import subprocess


def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py [etl | api | dashboard]")
        print()
        print("  etl        — fetch latest contracts from SAM.gov and save to the database")
        print("  api        — start the REST API at http://localhost:8000/docs")
        print("  dashboard  — open the visual dashboard at http://localhost:8501")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "etl":
        from etl import run_etl
        run_etl()

    elif command == "api":
        print("Starting API at http://localhost:8000")
        print("Open http://localhost:8000/docs to explore endpoints.")
        subprocess.run(["uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

    elif command == "dashboard":
        print("Starting dashboard at http://localhost:8501")
        subprocess.run(["uvicorn", "dashboard:app", "--reload", "--host", "0.0.0.0", "--port", "8501"])

    else:
        print(f"Unknown command: '{command}'")
        print("Valid commands: etl, api, dashboard")
        sys.exit(1)


if __name__ == "__main__":
    main()
