# Charger Performance Analyzer

This Python script analyzes daily charger performance data from CSV files, generates charts, and compiles them into a PDF report.

## Setup Instructions

To get started with this project, follow these steps:

1.  **Navigate to the project directory:**
    ```bash
    cd charger_report_analyzer
    ```

2.  **Create a Python Virtual Environment (Recommended):**
    It's highly recommended to use a virtual environment to manage project dependencies and avoid conflicts with your system's Python packages.

    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    You'll need to activate the virtual environment in each new terminal session where you want to run the script.

    ```bash
    source venv/bin/activate
    ```

4.  **Install Required Libraries:**
    Once your virtual environment is active, install the necessary Python libraries using `pip`:

    ```bash
    pip install -r requirements.txt
    ```

## Data Input

Place your CSV data files inside the `sample_data/` directory within this project. The script expects CSV filenames to be in the format `platform-charger-stats-YYYY-MM-DD.csv`.

## Running the Analyzer

After setting up and activating your virtual environment, you can run the analysis script:

```bash
python analyzer.py
```

## Output

The script will generate the following outputs in the `charger_report_analyzer` directory:

*   `report.pdf`: A PDF document containing an overall summary, a list of chargers with low uptime, and performance charts.
*   `charts/`: A directory containing individual chart images (`.png` files) generated during the process.

## CSV Data Structure Assumptions

The script expects CSV files with the following initial columns, followed by various performance metrics:

*   `Tenant`
*   `Charging Station`
*   `Serial Number`
*   Performance metrics (e.g., `Charger Uptime (%)`, `Total kWh Charged`, `Premature Stops`, `Offline Minutes`), as derived from the system's `ChargerStatKey` enum.

Feel free to customize the `analyzer.py` script to generate different charts or analyses based on your specific needs.
