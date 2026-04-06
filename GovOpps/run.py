# run.py
# The single entry point for this project.
# Every command you need is here — no digging through other files.
#
# Usage:
#   python run.py etl          fetch contracts from SAM.gov and load into the DB
#   python run.py api          start the FastAPI server (http://localhost:8000/docs)
#   python run.py dashboard    open the Streamlit dashboard (http://localhost:8501)

# sys gives you access to the Python interpreter itself.
# Used here for sys.argv (read what the user typed on the command line)
# and sys.exit() (stop the program with a success/error code).
import sys

# subprocess lets you run a terminal command from inside Python code —
# as if you typed it yourself in the shell.
# Used here to launch uvicorn (the web server) as a separate process.
import subprocess


def main():
    # sys.argv is a list of command-line arguments.
    # sys.argv[0] is always the script name ("run.py").
    # sys.argv[1] is the first argument the user typed after it (e.g. "etl").
    if len(sys.argv) < 2:
        # No argument given — print usage instructions and exit cleanly
        print("Usage: python run.py [etl | api | dashboard]")
        print()
        print("  etl        — fetch latest contracts from SAM.gov and save to the database")
        print("  api        — start the REST API at http://localhost:8000/docs")
        print("  dashboard  — open the visual dashboard at http://localhost:8501")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "etl":
        # Import and run the ETL pipeline directly in this same Python process.
        # We import here (not at the top) so we only load ETL dependencies when needed.
        from etl import run_etl
        run_etl()

    elif command == "api":
        # Start the FastAPI server using uvicorn — a fast ASGI web server.
        # --reload means "restart the server automatically when you edit a file" (dev mode).
        # api:app means "look in api.py for the object named app".
        print("Starting API at http://localhost:8000")
        print("Open http://localhost:8000/docs to explore endpoints.")
        subprocess.run(["uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

    elif command == "dashboard":
        # Start the dashboard server on port 8501 — same setup as the API but a different app.
        # dashboard:app means "look in dashboard.py for the object named app".
        print("Starting dashboard at http://localhost:8501")
        subprocess.run(["uvicorn", "dashboard:app", "--reload", "--host", "0.0.0.0", "--port", "8501"])

    else:
        # The user typed something we don't recognize
        print(f"Unknown command: '{command}'")
        print("Valid commands: etl, api, dashboard")
        sys.exit(1)


if __name__ == "__main__":
    # This block only runs when you execute this file directly (python run.py ...).
    # It won't run if another file imports run.py as a module.
    main()
