import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.lines as mlines
import warnings

# 1: I import the necessary tools 
warnings.filterwarnings("ignore")

# Path configuration 
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# I set a nice visual style for all my plots
sns.set_theme(style="whitegrid")

# 2: I load the data 
file_path = os.path.join(project_root, "data", "Final_Cleaned_Database.csv")
try:
    df = pd.read_csv(file_path)
    print("Data loaded successfully.")
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    exit()

# 3: I define the 2030 EU Targets and my color-coded logic 
targets_2030 = {
    'Real_GDP_Per_Capita': {'value': None, 'goal': 'higher_is_better'},
    'NEET_Rate': {'value': 9.0, 'goal': 'lower_is_better'},
    'Unemployment_Rate': {'value': 5.0, 'goal': 'lower_is_better'}, # Assuming ~5% as a proxy for high employment
    'Income_Distribution_Ratio': {'value': None, 'goal': 'lower_is_better'},
    'Income_Share_Bottom_40': {'value': None, 'goal': 'higher_is_better'},
    'Renewable_Energy_Share': {'value': 42.5, 'goal': 'higher_is_better'},
    'GHG_Emissions': {'value': None, 'goal': 'lower_is_better'} # Relative target, we'll check the trend
}

# 4: I define the feature selection map for my hybrid model 
feature_selection_map = {
    'Real_GDP_Per_Capita': ['NEET_Rate_lag1', 'Income_Distribution_Ratio_lag1'],
    'NEET_Rate': ['Unemployment_Rate_lag1', 'Income_Distribution_Ratio_lag1'],
    'Unemployment_Rate': ['NEET_Rate_lag1', 'Income_Distribution_Ratio_lag1'],
    'Income_Distribution_Ratio': ['NEET_Rate_lag1', 'Income_Share_Bottom_40_lag1'],
    'Income_Share_Bottom_40': ['NEET_Rate_lag1', 'Income_Distribution_Ratio_lag1'],
    'Renewable_Energy_Share': ['Real_GDP_Per_Capita_lag1']
}

# 5: I start the forecasting process 
print("\nStarting forecast to 2030 for all countries...")
all_forecasts = []
countries = df['Country'].unique()

# I create a specific directory for the trend graphs
graph_output_dir = os.path.join(project_root, "results", "forecast_2030", "trend_graphs")
os.makedirs(graph_output_dir, exist_ok=True)


for country in countries:
    df_country = df[df['Country'] == country].copy()
    
    # I define the order of my indicators for consistent tables and graphs
    numeric_cols = [
        'Real_GDP_Per_Capita',
        'NEET_Rate',
        'Unemployment_Rate',
        'Income_Distribution_Ratio',
        'Income_Share_Bottom_40',
        'Renewable_Energy_Share',
        'GHG_Emissions'
    ]
    lagged_cols = [f'{c}_lag1' for c in numeric_cols]
    df_country[lagged_cols] = df_country[numeric_cols].shift(1)
    
    train_data = df_country.dropna()

    models = {}
    for col in numeric_cols:
        if col == 'GHG_Emissions':
            feature_cols = ['Year']
            X_train = df_country[feature_cols]
            y_train = df_country[col]
        else:
            selected_features = feature_selection_map.get(col, [])
            feature_cols = ['Year'] + selected_features
            X_train = train_data[feature_cols]
            y_train = train_data[col]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        models[col] = {'model': model, 'features': feature_cols}

    last_known_data = df_country[df_country['Year'] == 2022].to_dict('records')[0]
    forecast_df = pd.DataFrame([last_known_data])

    for year in range(2023, 2031):
        previous_year_data = forecast_df[forecast_df['Year'] == year - 1].iloc[0]
        new_prediction = {'Country': country, 'Year': year}
        
        for col in numeric_cols:
            new_prediction[f'{col}_lag1'] = previous_year_data[col]
            
        for col in numeric_cols:
            model_info = models[col]
            input_features = pd.DataFrame([new_prediction])[model_info['features']]
            predicted_value = model_info['model'].predict(input_features)[0]

             # I add a constraint to prevent negative predictions for rates and shares
            if col in ['NEET_Rate', 'Unemployment_Rate', 'Renewable_Energy_Share', 'Income_Distribution_Ratio', 'Income_Share_Bottom_40'] and predicted_value < 0:
                predicted_value = 0 # A rate or share cannot be negative
            new_prediction[col] = predicted_value
            
        forecast_df = pd.concat([forecast_df, pd.DataFrame([new_prediction])], ignore_index=True)

    # I generate a graph for this country's forecast 
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    fig.suptitle(f"2030 Forecast for {country}", fontsize=16, weight='bold', y=0.98)
    axes_flat = axes.flatten()

    for i, col in enumerate(numeric_cols):
        ax = axes_flat[i]
        
        # 1. I plot the historical data
        sns.scatterplot(data=df_country, x='Year', y=col, ax=ax, color='black', label='Historical Data')
        
        # 2. I plot the forecasted trend line
        # I create a full trend line from 2005 to 2030
        # First, I get the model's fit on the historical data
        model_info = models[col]
        if col == 'GHG_Emissions':
            historical_fit_input = df_country[model_info['features']]
        else:
            historical_fit_input = train_data[model_info['features']]
        historical_fit = model_info['model'].predict(historical_fit_input)
        
        # Then, I combine the historical fit with the future forecast
        full_trend = np.concatenate([historical_fit, forecast_df[col].iloc[1:].values])
        full_years = np.concatenate([historical_fit_input['Year'].values, forecast_df['Year'].iloc[1:].values])
        ax.plot(full_years, full_trend, color='blue', linestyle='--', label='Model Trend & Forecast')
        
        # 3. I add the 2030 target line, if it exists
        target_value = targets_2030[col]['value']
        if target_value is not None:
            ax.axhline(y=target_value, color='red', linestyle=':', linewidth=2, label=f'2030 Target ({target_value})')
        
        ax.set_title(col.replace('_', ' '), fontsize=12)
        ax.set_xlabel('Year')
        ax.set_ylabel('')
        ax.legend()

    # I remove the empty subplot
    fig.delaxes(axes_flat[-1])
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # I save the chart
    filename = f"{graph_output_dir}/{country}_forecast_trends.png"
    plt.savefig(filename, dpi=150)
    plt.close(fig)

    prediction_2030 = forecast_df[forecast_df['Year'] == 2030].iloc[0]
    
    for col in numeric_cols:
        last_value = last_known_data[col]
        forecast_value = prediction_2030[col]
        target_info = targets_2030[col]
        
        status = 'Error' # Default status
        
        # Color-Coded Logic 
        if target_info['value'] is not None: # Case with a specific target value
            is_met = False
            if target_info['goal'] == 'lower_is_better' and forecast_value <= target_info['value']:
                is_met = True
            elif target_info['goal'] == 'higher_is_better' and forecast_value >= target_info['value']:
                is_met = True
            
            if is_met:
                status = 'Green'
            else:
                # If target is not met, I check the trend
                is_improving = False
                if target_info['goal'] == 'lower_is_better' and forecast_value < last_value:
                    is_improving = True
                elif target_info['goal'] == 'higher_is_better' and forecast_value > last_value:
                    is_improving = True
                
                status = 'Orange' if is_improving else 'Red'
        
        else: # Case for trend-based goals (GDP, S80/S20, etc.)
            if col == 'Real_GDP_Per_Capita':
                # For GDP, I use a specific growth-based logic
                growth_pct = ((forecast_value - last_value) / last_value) * 100
                if growth_pct > 10:
                    status = 'Green' # Dynamic growth
                elif growth_pct >= 5:
                    status = 'Orange' # Medium growth
                else:
                    status = 'Red' # Stagnation
            else:
                # For other trend-based goals, I use a simple trend direction
                is_good_trend = False
                if target_info['goal'] == 'lower_is_better' and forecast_value < last_value:
                    is_good_trend = True
                elif target_info['goal'] == 'higher_is_better' and forecast_value > last_value:
                    is_good_trend = True
                status = 'Green' if is_good_trend else 'Red'
                
        all_forecasts.append({
            'Country': country,
            'Indicator': col,
            'Last Value (2022)': last_value,
            'Forecast (2030)': forecast_value,
            'Target (2030)': f"<= {target_info['value']}" if target_info['goal'] == 'lower_is_better' and target_info['value'] is not None else (f">= {target_info['value']}" if target_info['goal'] == 'higher_is_better' and target_info['value'] is not None else "Good Trend"),
            'Status': status
        })

# 6: I display the final results in a clean table 
results_df = pd.DataFrame(all_forecasts)

pivot_df = results_df.pivot(index='Country', columns='Indicator', values='Forecast (2030)')[numeric_cols]
status_df = results_df.pivot(index='Country', columns='Indicator', values='Status')[numeric_cols]

print("\nForecasted Values for 2030")
print(pivot_df.round(2))

print("\nStatus vs. 2030 EU Targets (Green/Orange/Red)")
print(status_df)

# Save results to CSV files
output_dir = os.path.join(project_root, "results", "forecast_2030")
os.makedirs(output_dir, exist_ok=True)
pivot_df.round(2).to_csv(os.path.join(output_dir, "forecast_2030_values.csv"))
status_df.to_csv(os.path.join(output_dir, "forecast_2030_status.csv"))
print(f"\nResults saved in '{output_dir}'")
