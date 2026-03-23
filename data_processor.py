import os
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATA_DIR = 'sample_data'

def load_data_in_range(start_date_str, end_date_str):
    """
    Loads and concatenates CSV data for a given date range.
    Assumes CSV filenames are in the format 'platform-charger-stats-YYYY-MM-DD.csv'.
    """
    all_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and f.startswith('platform-charger-stats-')]
    all_files.sort()

    if not all_files:
        logging.warning("No data files found in 'sample_data' directory.")
        return pd.DataFrame()

    filtered_files = []
    for filename in all_files:
        file_date_str = filename.replace('platform-charger-stats-', '').replace('.csv', '')
        if start_date_str <= file_date_str <= end_date_str:
            filtered_files.append(os.path.join(DATA_DIR, filename))

    if not filtered_files:
        logging.warning(f"No data files found for the date range {start_date_str} to {end_date_str}.")
        return pd.DataFrame()

    df_list = []
    for f_path in filtered_files:
        df_list.append(pd.read_csv(f_path))
    
    if not df_list:
        return pd.DataFrame()

    combined_df = pd.concat(df_list, ignore_index=True)
    
    # Clean column names (strip whitespace)
    combined_df.columns = combined_df.columns.str.strip()

    # Convert 'Start Time' to datetime for time-based analysis
    time_col = 'Start Time'
    if time_col in combined_df.columns:
        combined_df['timestamp'] = pd.to_datetime(combined_df[time_col], errors='coerce')
        combined_df.dropna(subset=['timestamp'], inplace=True)
    
    return combined_df

def calculate_executive_summary_metrics(df):
    """Calculates key metrics for the executive summary."""
    total_chargers = df['Serial Number'].nunique()
    
    kwh_col = next((col for col in df.columns if 'kwh charged' in col.lower()), 'Total kWh Charged (kWh)')
    total_energy_delivered = df[kwh_col].sum() if kwh_col in df.columns else 0

    # Assuming each row is a charging session for simplicity. Refine if actual session IDs are available.
    total_sessions = len(df) # This assumes each row is a session. Adjust if there's a specific 'Session ID' column.

    return {
        'total_chargers': total_chargers,
        'total_energy_delivered': total_energy_delivered,
        'total_sessions': total_sessions,
        'kwh_col': kwh_col # Return kwh_col for consistency
    }

def calculate_charger_performance_metrics(df, kwh_col):
    """Calculates performance metrics per charger."""
    charger_performance = df.groupby('Serial Number').agg(
        Total_Sessions=('Serial Number', 'size'),
        Total_Energy_kWh=(kwh_col, 'sum') if kwh_col in df.columns else (None, lambda x: 0),
        Average_Uptime_pct=('Charger Uptime (%)', 'mean') if 'Charger Uptime (%)' in df.columns else (None, lambda x: 0)
    ).round(2)
    charger_performance = charger_performance.rename(columns={'Total_Energy_kWh': 'Total Energy (kWh)'})
    return charger_performance

def calculate_usage_patterns(df):
    """Calculates usage patterns like sessions per hour."""
    if 'timestamp' not in df.columns or df['timestamp'].empty:
        return pd.DataFrame()
    
    df['hour'] = df['timestamp'].dt.hour
    sessions_per_hour = df.groupby('hour').size().reindex(range(24), fill_value=0)
    return sessions_per_hour

def calculate_charging_behavior_metrics(df, fast_charging_threshold):
    """
    Calculates metrics related to charging behavior:
    - Average session duration
    - Session duration distribution
    - Fast vs slow charging usage (needs definition, here using Total kWh Charged)
    """
    behavior_metrics = {}

    # Average Session Duration
    session_duration_col = 'Average Session Duration (min)'
    if session_duration_col in df.columns:
        behavior_metrics['average_session_duration'] = df[session_duration_col].mean().round(2)
        behavior_metrics['session_durations'] = df[session_duration_col].dropna().tolist()
    else:
        behavior_metrics['average_session_duration'] = 0
        behavior_metrics['session_durations'] = []
        logging.warning(f"'{session_duration_col}' not found for charging behavior analysis.")

    # Fast vs Slow Charging Usage
    kwh_col = next((col for col in df.columns if 'kwh charged' in col.lower()), 'Total kWh Charged (kWh)')
    if kwh_col in df.columns:
        df['Charging_Type'] = df[kwh_col].apply(lambda x: 'Fast' if x > fast_charging_threshold else 'Slow')
        charging_type_counts = df['Charging_Type'].value_counts(normalize=True) * 100
        behavior_metrics['fast_vs_slow_charging'] = charging_type_counts.to_dict()
    else:
        behavior_metrics['fast_vs_slow_charging'] = {'Fast': 0, 'Slow': 0}
        logging.warning(f"'{kwh_col}' not found for fast vs slow charging analysis.")

    return behavior_metrics

def calculate_power_technical_metrics(df):
    """
    Calculates metrics related to power and technical performance.
    Placeholders for now, as specific columns for these are not clear in sample data.
    """
    tech_metrics = {}

    # Placeholder for Temperature readings
    temp_col = 'Average Charger Temperature (C)' # Assuming such a column might exist
    if temp_col in df.columns and not df[temp_col].isnull().all():
        tech_metrics['average_temperature'] = df[temp_col].mean().round(2)
        tech_metrics['temperature_readings'] = df[['timestamp', temp_col]].dropna().to_dict(orient='list')
    else:
        tech_metrics['average_temperature'] = 0
        tech_metrics['temperature_readings'] = []
        logging.warning(f"'{temp_col}' not found or is empty for technical analysis.")

    # Placeholder for Voltage & Current variations (assuming columns like 'Voltage_L1', 'Current_L1')
    voltage_col = 'Average Voltage (V)' # Placeholder
    current_col = 'Average Current (A)' # Placeholder
    if voltage_col in df.columns and current_col in df.columns and not df[voltage_col].isnull().all() and not df[current_col].isnull().all():
        tech_metrics['average_voltage'] = df[voltage_col].mean().round(2)
        tech_metrics['average_current'] = df[current_col].mean().round(2)
        tech_metrics['voltage_current_trends'] = df[['timestamp', voltage_col, current_col]].dropna().to_dict(orient='list')
    else:
        tech_metrics['average_voltage'] = 0
        tech_metrics['average_current'] = 0
        tech_metrics['voltage_current_trends'] = []
        logging.warning(f"'{voltage_col}' or '{current_col}' not found or are empty for technical analysis.")

    # Placeholder for Charging Rate trends (could be derived from kWh and duration)
    # For now, let's assume a 'Charging Rate (kW)' column
    charging_rate_col = 'Average Charging Rate (kW)' # Placeholder
    if charging_rate_col in df.columns and not df[charging_rate_col].isnull().all():
        tech_metrics['average_charging_rate'] = df[charging_rate_col].mean().round(2)
        tech_metrics['charging_rate_trends'] = df[['timestamp', charging_rate_col]].dropna().to_dict(orient='list')
    else:
        tech_metrics['average_charging_rate'] = 0
        tech_metrics['charging_rate_trends'] = []
        logging.warning(f"'{charging_rate_col}' not found or is empty for technical analysis.")

    return tech_metrics

def detect_anomalies(df, temp_threshold_high, uptime_threshold_low, charge_rate_threshold_low):
    """
    Detects anomalies based on predefined thresholds.
    Returns a dictionary of anomalous chargers for each category.
    """
    anomalies = {
        'high_temp_chargers': [],
        'low_uptime_chargers': [],
        'low_charge_rate_chargers': []
    }

    # High Temperature Anomalies
    temp_col = 'Average Charger Temperature (C)'
    if temp_col in df.columns:
        high_temp_df = df[df[temp_col] > temp_threshold_high]
        anomalies['high_temp_chargers'] = high_temp_df['Serial Number'].astype(str).unique().tolist()
        if anomalies['high_temp_chargers']:
            logging.warning(f"High temperature detected for chargers: {anomalies['high_temp_chargers']}")
    else:
        logging.warning(f"'{temp_col}' column not found for high temperature anomaly detection.")

    # Low Uptime Anomalies
    uptime_col = 'Charger Uptime (%)'
    if uptime_col in df.columns:
        low_uptime_df = df[df[uptime_col] < uptime_threshold_low]
        anomalies['low_uptime_chargers'] = low_uptime_df['Serial Number'].astype(str).unique().tolist()
        if anomalies['low_uptime_chargers']:
            logging.warning(f"Low uptime detected for chargers: {anomalies['low_uptime_chargers']}")
    else:
        logging.warning(f"'{uptime_col}' column not found for low uptime anomaly detection.")
    
    # Low Charging Rate Anomalies (underutilization or fault)
    charge_rate_col = 'Average Charging Rate (kW)'
    if charge_rate_col in df.columns:
        low_charge_rate_df = df[df[charge_rate_col] < charge_rate_threshold_low]
        anomalies['low_charge_rate_chargers'] = low_charge_rate_df['Serial Number'].astype(str).unique().tolist()
        if anomalies['low_charge_rate_chargers']:
            logging.warning(f"Low charging rate detected for chargers: {anomalies['low_charge_rate_chargers']}")
    else:
        logging.warning(f"'{charge_rate_col}' column not found for low charging rate anomaly detection.")

    return anomalies

def calculate_charger_rankings(df, kwh_col, n_top=5, n_bottom=5):
    """
    Calculates top N and bottom N chargers based on energy delivered and uptime.
    """
    rankings = {
        'top_kwh_chargers': [],
        'bottom_uptime_chargers': []
    }

    # Top N by kWh
    if kwh_col in df.columns:
        kwh_rank = df.groupby('Serial Number')[kwh_col].sum().nlargest(n_top)
        rankings['top_kwh_chargers'] = kwh_rank.reset_index().values.tolist()
    else:
        logging.warning(f"'{kwh_col}' column not found for top kWh ranking.")

    # Bottom N by Uptime
    uptime_col = 'Charger Uptime (%)'
    if uptime_col in df.columns:
        uptime_rank = df.groupby('Serial Number')[uptime_col].mean().nsmallest(n_bottom)
        rankings['bottom_uptime_chargers'] = uptime_rank.reset_index().values.tolist()
    else:
        logging.warning(f"'{uptime_col}' column not found for bottom uptime ranking.")
    
    return rankings

def calculate_charger_health_scores(df, kwh_col, anomalies, base_score=100, weights=None):
    """
    Calculates a health score for each charger based on multiple factors.
    """
    if weights is None:
        weights = {
            'uptime': 0.4,
            'energy': 0.3,
            'anomalies': {
                'high_temp': -20,
                'low_uptime': -20,
                'low_charge_rate': -10
            }
        }
    
    health_scores = {}
    
    charger_stats = df.groupby('Serial Number').agg(
        Total_Energy_kWh=(kwh_col, 'sum'),
        Average_Uptime_pct=('Charger Uptime (%)', 'mean')
    )

    if not charger_stats.empty:
        # Normalize energy and uptime for scoring
        max_energy = charger_stats['Total_Energy_kWh'].max()
        if max_energy > 0:
            charger_stats['Normalized_Energy'] = charger_stats['Total_Energy_kWh'] / max_energy
        else:
            charger_stats['Normalized_Energy'] = 0
            
        charger_stats['Normalized_Uptime'] = charger_stats['Average_Uptime_pct'] / 100

        for serial_number, row in charger_stats.iterrows():
            score = float(base_score)
            
            # Weighted score for uptime and energy
            score += row['Normalized_Uptime'] * weights['uptime'] * 100
            score += row['Normalized_Energy'] * weights['energy'] * 100
            
            # Deduct points for anomalies
            if serial_number in anomalies.get('high_temp_chargers', []):
                score += weights['anomalies']['high_temp']
            if serial_number in anomalies.get('low_uptime_chargers', []):
                score += weights['anomalies']['low_uptime']
            if serial_number in anomalies.get('low_charge_rate_chargers', []):
                score += weights['anomalies']['low_charge_rate']
            
            health_scores[serial_number] = round(max(0, min(score, 100)), 2) # Clamp score between 0 and 100

    health_scores_df = pd.DataFrame(health_scores.items(), columns=['Serial Number', 'Health Score'])
    return health_scores_df.sort_values(by='Health Score', ascending=False)

def generate_insights(report_data):
    """
    Generates human-readable insights from the report data.
    """
    insights = []
    
    # Peak Usage Insight
    usage_patterns = report_data.get('usage_patterns_data')
    if usage_patterns is not None and not usage_patterns.empty:
        peak_hour = usage_patterns.idxmax()
        insights.append(f"Peak usage occurs around {peak_hour}:00, with the highest number of charging sessions.")

    # Anomaly Insights
    anomalies = report_data.get('anomalies', {})
    if anomalies.get('high_temp_chargers'):
        insights.append(f"High temperatures detected in chargers: {', '.join(anomalies['high_temp_chargers'])}. This could indicate cooling issues.")
    if anomalies.get('low_uptime_chargers'):
        insights.append(f"Low uptime for chargers: {', '.join(anomalies['low_uptime_chargers'])}. These chargers are frequently offline.")
    if anomalies.get('low_charge_rate_chargers'):
        insights.append(f"Low charging rates observed in chargers: {', '.join(anomalies['low_charge_rate_chargers'])}. This may point to underutilization or faults.")

    # Health Score Insights
    health_scores = report_data.get('health_scores')
    if health_scores is not None and not health_scores.empty:
        low_health_chargers = health_scores[health_scores['Health Score'] < 70]
        if not low_health_chargers.empty:
            insights.append(f"Chargers with low health scores needing attention: {', '.join(low_health_chargers['Serial Number'])}.")

    return insights

def generate_recommendations(insights):
    """
    Generates actionable recommendations based on the insights.
    """
    recommendations = []
    for insight in insights:
        if "Peak usage" in insight:
            recommendations.append("Consider implementing dynamic pricing to incentivize off-peak charging and manage grid load.")
        if "High temperatures" in insight:
            recommendations.append("Schedule immediate maintenance checks for chargers with high temperature warnings to prevent failures.")
        if "Low uptime" in insight:
            recommendations.append("Investigate network connectivity and hardware for chargers with low uptime to improve reliability.")
        if "Low charging rates" in insight:
            recommendations.append("Analyze low-rate chargers for potential faults or under-powering issues.")
        if "low health scores" in insight:
            recommendations.append("Prioritize review and maintenance for chargers with low health scores.")
            
    return list(set(recommendations)) # Return unique recommendations