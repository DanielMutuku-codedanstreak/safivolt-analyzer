import os
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.platypus.doctemplate import PageTemplate, Frame
from reportlab.lib.styles import getSampleStyleSheet, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.pagesizes import A4 # Import A4
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import functions from newly created modules
from data_processor import (
    load_data_in_range, 
    calculate_executive_summary_metrics, 
    calculate_charger_performance_metrics,
    calculate_usage_patterns,
    calculate_charging_behavior_metrics,
    calculate_power_technical_metrics,
    detect_anomalies,
    calculate_charger_health_scores,
    generate_insights,
    generate_recommendations,
)
from chart_generator import (
    create_kwh_chart, 
    create_uptime_chart, 
    create_sessions_chart,
    create_usage_over_time_chart,
    create_session_duration_histogram,
    create_fast_vs_slow_charging_pie_chart,
    create_line_chart, 
    create_scatter_plot, 
)
from pdf_generator import (
    _header_footer, 
    create_title_page, 
    create_chapter_title, 
    create_chapter_body, 
    create_table_flowable,
    generate_pdf_report
)

# --- Configuration ---
OUTPUT_DIR = 'output-report'
CHART_DIR = os.path.join(OUTPUT_DIR, 'charts')
FAST_CHARGING_THRESHOLD = 20 # kWh

# Anomaly Detection Thresholds (placeholders, adjust as needed)
TEMP_THRESHOLD_HIGH = 60 # Celsius
UPTIME_THRESHOLD_LOW = 90 # Percentage
CHARGE_RATE_THRESHOLD_LOW = 5 # kW

# Page Dimensions
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = MARGIN_RIGHT = 15 * mm
MARGIN_TOP = MARGIN_BOTTOM = 15 * mm
FRAME_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
FRAME_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

# Styles for ReportLab
styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['h1']
styleH2 = styles['h2']
styleH3 = styles['h3']


def generate_report(start_date_str, end_date_str):
    logging.info(f"Generating report for {start_date_str} to {end_date_str}...")

    if not os.path.exists(CHART_DIR):
        os.makedirs(CHART_DIR)

    # Load and process data
    combined_df = load_data_in_range(start_date_str, end_date_str)
    if combined_df.empty:
        logging.warning(f"No data to process for the date range {start_date_str} to {end_date_str}. Exiting.")
        return

    # Detect anomalies
    anomalies = detect_anomalies(combined_df, TEMP_THRESHOLD_HIGH, UPTIME_THRESHOLD_LOW, CHARGE_RATE_THRESHOLD_LOW)

    # Calculate executive summary metrics first to get kwh_col
    executive_summary_metrics = calculate_executive_summary_metrics(combined_df)
    kwh_col = executive_summary_metrics['kwh_col']

    # Build report_data dictionary
    report_data = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'report_date_range': f"{start_date_str} to {end_date_str}",
        'combined_df': combined_df,
        'executive_summary_metrics': executive_summary_metrics,
        'charger_performance_metrics': calculate_charger_performance_metrics(combined_df, kwh_col),
        'usage_patterns_data': calculate_usage_patterns(combined_df),
        'charging_behavior_metrics': calculate_charging_behavior_metrics(combined_df, FAST_CHARGING_THRESHOLD),
        'power_technical_metrics': calculate_power_technical_metrics(combined_df),
        'anomalies': anomalies,
        'TEMP_THRESHOLD_HIGH': TEMP_THRESHOLD_HIGH,
        'UPTIME_THRESHOLD_LOW': UPTIME_THRESHOLD_LOW,
        'CHARGE_RATE_THRESHOLD_LOW': CHARGE_RATE_THRESHOLD_LOW,
    }

    # Auto-Insight Generation
    report_data['health_scores'] = calculate_charger_health_scores(combined_df, kwh_col, anomalies)
    report_data['insights'] = generate_insights(report_data)
    report_data['recommendations'] = generate_recommendations(report_data['insights'])

    logging.info(f"Generated Insights: {report_data['insights']}")
    logging.info(f"Generated Recommendations: {report_data['recommendations']}")


    # Generate charts
    chart_paths = {}
    
    # Executive Summary placeholder chart
    temp_kwh_chart_path = os.path.join(CHART_DIR, 'executive_summary_kwh_chart.png')
    create_kwh_chart(report_data['combined_df'].groupby('Serial Number').agg(
        **{kwh_col: (kwh_col, 'sum')}
    ).reset_index().rename(columns={'Serial Number': 'Serial Number'}), temp_kwh_chart_path, f"Total kWh Charged per Charger ({report_data['report_date_range']})")
    if os.path.exists(temp_kwh_chart_path):
        chart_paths['executive_summary_kwh'] = temp_kwh_chart_path

    # Charger Performance charts
    charger_energy_chart_path = os.path.join(CHART_DIR, 'charger_energy_chart.png')
    create_kwh_chart(report_data['combined_df'].groupby('Serial Number').agg(
        **{kwh_col: (kwh_col, 'sum')}
    ).reset_index().rename(columns={'Serial Number': 'Serial Number'}), charger_energy_chart_path, f"Total kWh Charged per Charger ({report_data['report_date_range']})")
    if os.path.exists(charger_energy_chart_path):
        chart_paths['charger_energy_chart'] = charger_energy_chart_path

    charger_sessions_chart_path = os.path.join(CHART_DIR, 'charger_sessions_chart.png')
    create_sessions_chart(report_data['charger_performance_metrics'].reset_index(), charger_sessions_chart_path, f"Total Sessions per Charger ({report_data['report_date_range']})")
    if os.path.exists(charger_sessions_chart_path):
        chart_paths['charger_sessions_chart'] = charger_sessions_chart_path
    
    # Usage Patterns charts
    if not report_data['usage_patterns_data'].empty:
        usage_over_time_chart_path = os.path.join(CHART_DIR, 'usage_over_time_chart.png')
        create_usage_over_time_chart(report_data['combined_df'], # create_usage_over_time_chart expects combined_df
                                     usage_over_time_chart_path, 
                                     f"Usage Over Time ({report_data['report_date_range']})")
        if os.path.exists(usage_over_time_chart_path):
            chart_paths['usage_over_time_chart'] = usage_over_time_chart_path
    
    # Charging Behavior charts
    if report_data['charging_behavior_metrics']['session_durations']:
        session_duration_hist_path = os.path.join(CHART_DIR, 'session_duration_histogram.png')
        create_session_duration_histogram(report_data['charging_behavior_metrics']['session_durations'], session_duration_hist_path, f"Session Duration Distribution ({report_data['report_date_range']})")
        if os.path.exists(session_duration_hist_path):
            chart_paths['session_duration_histogram'] = session_duration_hist_path

    if report_data['charging_behavior_metrics']['fast_vs_slow_charging']:
        fast_slow_pie_chart_path = os.path.join(CHART_DIR, 'fast_slow_pie_chart.png')
        create_fast_vs_slow_charging_pie_chart(report_data['charging_behavior_metrics']['fast_vs_slow_charging'], fast_slow_pie_chart_path, f"Fast vs Slow Charging Usage ({report_data['report_date_range']})")
        if os.path.exists(fast_slow_pie_chart_path):
            chart_paths['fast_slow_pie_chart'] = fast_slow_pie_chart_path

    # Power & Technical Metrics Charts
    tech_metrics = report_data['power_technical_metrics']
    if tech_metrics['temperature_readings']:
        temp_over_time_chart_path = os.path.join(CHART_DIR, 'temperature_over_time_chart.png')
        create_line_chart(tech_metrics['temperature_readings'], 'timestamp', 'Average Charger Temperature (C)', 
                          temp_over_time_chart_path, f"Temperature Over Time ({report_data['report_date_range']})", "Time", "Temperature (C)")
        if os.path.exists(temp_over_time_chart_path):
            chart_paths['temperature_over_time_chart'] = temp_over_time_chart_path

    if tech_metrics['voltage_current_trends']:
        voltage_current_chart_path = os.path.join(CHART_DIR, 'voltage_current_chart.png')
        create_line_chart(tech_metrics['voltage_current_trends'], 'timestamp', 'Average Voltage (V)', 
                          voltage_current_chart_path, f"Voltage Over Time ({report_data['report_date_range']})", "Time", "Voltage (V)")
        if os.path.exists(voltage_current_chart_path):
            chart_paths['voltage_current_chart'] = voltage_current_chart_path
        
        # You might want another line chart for current, or plot both on the same chart
        current_chart_path = os.path.join(CHART_DIR, 'current_chart.png')
        create_line_chart(tech_metrics['voltage_current_trends'], 'timestamp', 'Average Current (A)', 
                          current_chart_path, f"Current Over Time ({report_data['report_date_range']})", "Time", "Current (A)")
        if os.path.exists(current_chart_path):
            chart_paths['current_chart'] = current_chart_path


    if tech_metrics['charging_rate_trends']:
        charging_rate_scatter_path = os.path.join(CHART_DIR, 'charging_rate_scatter.png')
        create_scatter_plot(tech_metrics['charging_rate_trends'], 'timestamp', 'Average Charging Rate (kW)', 
                            charging_rate_scatter_path, f"Charging Rate vs Time ({report_data['report_date_range']})", "Time", "Charging Rate (kW)")
        if os.path.exists(charging_rate_scatter_path):
            chart_paths['charging_rate_scatter'] = charging_rate_scatter_path


    # Generate PDF Report
    output_filename = os.path.join(OUTPUT_DIR, f'charger_report_{start_date_str}_to_{end_date_str}.pdf')
    generate_pdf_report(output_filename, report_data, chart_paths)

    logging.info(f"Report saved as {output_filename}")
    logging.info("All reports generated successfully.")


if __name__ == '__main__':
    # Default date range for testing
    generate_report('2026-03-12', '2026-03-18')
