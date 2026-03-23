import os
import matplotlib.pyplot as plt
import pandas as pd

CHART_DIR = os.path.join('.', 'charts') # Assuming CHART_DIR is relative to the execution path

def _save_no_data_chart(output_path, report_title):
    """Saves a chart indicating that no data is available."""
    plt.figure(figsize=(12, 6))
    plt.title(f'{report_title} - No Data Available')
    plt.text(0.5, 0.5, 'No Data Available', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes, fontsize=14, color='gray')
    plt.savefig(output_path)
    plt.close()

def create_kwh_chart(df, output_path, report_title):
    """Creates a bar chart of kWh per charger."""
    if df.empty:
        _save_no_data_chart(output_path, report_title)
        return
    
    kwh_col = next((col for col in df.columns if 'kwh charged' in col.lower()), None)
    if not kwh_col:
        print(f"Warning: No 'kWh Charged' column found for chart in {os.path.basename(output_path)}.")
        return

    plt.figure(figsize=(12, 6))
    df_sorted = df.sort_values(by=kwh_col, ascending=False)
    plt.bar(df_sorted['Serial Number'], df_sorted[kwh_col], color='skyblue')
    plt.title(report_title)
    plt.ylabel('kWh Charged')
    plt.xlabel('Charger Serial Number')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_uptime_chart(df, output_path, report_title):
    """Creates a bar chart of uptime."""
    if df.empty:
        _save_no_data_chart(output_path, report_title)
        return

    uptime_col = 'Charger Uptime (%)'
    if uptime_col not in df.columns:
        print(f"Warning: Column '{uptime_col}' not found for chart in {os.path.basename(output_path)}.")
        return

    plt.figure(figsize=(12, 6))
    df_sorted = df.sort_values(by=uptime_col)
    plt.barh(df_sorted['Serial Number'], df_sorted[uptime_col], color='lightgreen')
    plt.title(report_title)
    plt.xlabel('Uptime (%)')
    plt.ylabel('Charger Serial Number')
    plt.axvline(x=95, color='r', linestyle='--', label='95% Target')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_sessions_chart(df, output_path, report_title):
    """Creates a bar chart of sessions per charger."""
    if df.empty:
        _save_no_data_chart(output_path, report_title)
        return
    
    plt.figure(figsize=(12, 6))
    df_sorted = df.sort_values(by='Total_Sessions', ascending=False)
    plt.bar(df_sorted['Serial Number'], df_sorted['Total_Sessions'], color='lightcoral')
    plt.title(report_title)
    plt.ylabel('Number of Sessions')
    plt.xlabel('Charger Serial Number')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_usage_over_time_chart(df, output_path, report_title):
    """Creates a line chart of usage over time (sessions per hour)."""
    if df.empty:
        _save_no_data_chart(output_path, report_title)
        return

    # Ensure a 'timestamp' column exists and is datetime
    if 'timestamp' not in df.columns:
        print(f"Warning: 'timestamp' column not found for usage over time chart for {report_title}.")
        # Attempt to derive 'timestamp' if possible from 'Start Time'
        if 'Start Time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Start Time'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)
        else:
            return # Cannot create chart without time data
    
    if df['timestamp'].empty: # Check after potential derivation
        _save_no_data_chart(output_path, report_title)
        return

    df['hour'] = df['timestamp'].dt.hour
    sessions_per_hour = df.groupby('hour').size().reindex(range(24), fill_value=0)

    plt.figure(figsize=(12, 6))
    sessions_per_hour.plot(kind='line', marker='o', color='purple')
    plt.title(report_title)
    plt.xlabel('Hour of Day')
    plt.ylabel('Number of Sessions')
    plt.xticks(range(0, 24, 2))
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_session_duration_histogram(session_durations, output_path, report_title):
    """Creates a histogram of session durations."""
    if not session_durations:
        _save_no_data_chart(output_path, report_title)
        return

    plt.figure(figsize=(12, 6))
    plt.hist(session_durations, bins=20, color='lightgreen', edgecolor='black')
    plt.title(report_title)
    plt.xlabel('Session Duration (min)')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_fast_vs_slow_charging_pie_chart(fast_vs_slow_data, output_path, report_title):
    """Creates a pie chart for fast vs slow charging usage."""
    if not fast_vs_slow_data or (fast_vs_slow_data.get('Fast', 0) == 0 and fast_vs_slow_data.get('Slow', 0) == 0):
        _save_no_data_chart(output_path, report_title)
        return

    labels = fast_vs_slow_data.keys()
    sizes = fast_vs_slow_data.values()
    colors = ['#ff9999','#66b3ff'] # Custom colors

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title(report_title)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_line_chart(df_data, x_col, y_col, output_path, report_title, x_label, y_label):
    """Creates a line chart for generic time-series data."""
    if not df_data or not isinstance(df_data, dict) or not x_col in df_data or not y_col in df_data or not df_data[x_col] or not df_data[y_col]:
        _save_no_data_chart(output_path, report_title)
        return
    
    # Assuming df_data is a dict with list values, convert to DataFrame for plotting
    df = pd.DataFrame(df_data)

    plt.figure(figsize=(12, 6))
    plt.plot(df[x_col], df[y_col], marker='o', linestyle='-')
    plt.title(report_title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_scatter_plot(df_data, x_col, y_col, output_path, report_title, x_label, y_label):
    """Creates a scatter plot for generic data."""
    if not df_data or not isinstance(df_data, dict) or not x_col in df_data or not y_col in df_data or not df_data[x_col] or not df_data[y_col]:
        _save_no_data_chart(output_path, report_title)
        return

    df = pd.DataFrame(df_data)

    plt.figure(figsize=(12, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.7)
    plt.title(report_title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()