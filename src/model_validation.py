# I import the necessary tools 
import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.lines as mlines  
import warnings

# I set the visual style for the plots
sns.set_theme(style="whitegrid")

# Path configuration to make the script work on any computer 
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# I load the data 
file_path = os.path.join(project_root, "data", "Final_Cleaned_Database.csv")

try:
    df = pd.read_csv(file_path)
    print(f"Data loaded successfully. Total rows: {len(df)}")
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    exit()

# I select numeric columns for analysis
numeric_cols = [col for col in df.columns if col not in ['Country', 'Year']]

# I prepare the data for an "honest" prediction 
# To predict year T, I must only use data from the past (T-1, T-2, etc.)

# I create new "_lag1" columns that contain the value from the previous year
# For example, the row for 2010 will have a "GDP_lag1" column with the GDP value from 2009
lagged_cols = [f'{c}_lag1' for c in numeric_cols]
df[lagged_cols] = df.groupby('Country')[numeric_cols].shift(1)

# The first year for each country (2005) has no previous year, so it contains empty values (NaN)
# I drop these rows because I can't use them to train the model
df_predictive = df.dropna()

# I define my feature selection strategy 
# Based on the correlation matrix, I choose 1 or 2 relevant variables to help predict each indicator
feature_selection_map = {
   'Real_GDP_Per_Capita': ['NEET_Rate_lag1', 'Income_Distribution_Ratio_lag1'],
    'NEET_Rate': ['Unemployment_Rate_lag1', 'Income_Distribution_Ratio_lag1'],
    'Unemployment_Rate': ['NEET_Rate_lag1', 'Income_Distribution_Ratio_lag1'],
    'Income_Distribution_Ratio': ['NEET_Rate_lag1', 'Income_Share_Bottom_40_lag1'],
    'Income_Share_Bottom_40': ['NEET_Rate_lag1', 'Income_Distribution_Ratio_lag1'], 
    # I deliberately exclude GHG_Emissions and Renewable_Energy_Share because I saw it wasn't well correlated with others => I will use a simpler model for it
}

# I configure the validation (Backtesting) 
# I define the cutoff year => everything before is for training, everything after is for testing
CUTOFF_YEAR = 2019 

print("\nStarting Hybrid Linear Regression Validation (Backtesting)")
print(f"Training Period: 2005 - {CUTOFF_YEAR}")
print(f"Testing Period: {CUTOFF_YEAR + 1} - 2022")

# I create a directory to save the charts
output_dir = os.path.join(project_root, "results", "model_validation_plot")
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory '{output_dir}' created")

results = []

# I start the validation loop, country by country 
countries = df_predictive['Country'].unique()
print(f"Processing validation for {len(countries)} countries...")

for country in countries:
    df_country_pred = df_predictive[df_predictive['Country'] == country]
    train = df_country_pred[df_country_pred['Year'] <= CUTOFF_YEAR]
    test = df_country_pred[df_country_pred['Year'] > CUTOFF_YEAR]

    if len(train) < 5 or len(test) == 0:
        continue

    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    fig.suptitle(f"Model Validation: {country}", fontsize=16, weight='bold', y=0.98)
    axes_flat = axes.flatten() 

    for i, col in enumerate(numeric_cols):
        model = LinearRegression()
        
        # Strategy for GHG and Renewable Energy
        if col in ['GHG_Emissions', 'Renewable_Energy_Share']:
            # For GHG and Renewable Energy, I use a simple model based only on time (the year) because the other variables were not helpful
            feature_cols = ['Year']
            # For this simple model, I don't need the lagged data
            train_simple = df[df['Country'] == country][df['Year'] <= CUTOFF_YEAR]
            test_simple = df[df['Country'] == country][df['Year'] > CUTOFF_YEAR]
            
            X_train = train_simple[feature_cols]
            y_train = train_simple[col]
            X_test = test_simple[feature_cols]
            y_real = test_simple[col]
            
            # I prepare the data to plot the prediction curve over the whole period
            X_full = df[df['Country'] == country][feature_cols]

        else:
            # For all other indicators, I use my other model
            # I get the relevant variables I chose from the dictionary
            selected_features = feature_selection_map.get(col, [])
            feature_cols = ['Year'] + selected_features
            
            # The predictive features (X) are the year and the selected lagged columns
            X_train = train[feature_cols]
            # The target (y) is the value of the indicator for the current year
            y_train = train[col]
            X_test = test[feature_cols]
            y_real = test[col]
            
            # I prepare the data to plot the prediction curve over the whole period
            X_full = df_country_pred[feature_cols]

        # Training and Prediction :
        # model.fit(): the model "learns" the relationship between X and y
        model.fit(X_train, y_train)
        # model.predict(): model to makes its predictions on the test data
        y_pred = model.predict(X_test)
        y_pred_full = model.predict(X_full)
        
        # I calculate the Mean Absolute Error (MAE) between the prediction and reality
        mae = mean_absolute_error(y_real, y_pred)
        results.append({'Country': country, 'Indicator': col, 'MAE': mae})
        
        # Visualization 
        ax = axes_flat[i]
        # I display the real data (black dots)
        sns.scatterplot(data=df[df['Country'] == country], x='Year', y=col, ax=ax, color='black', s=40)
        # I draw the model's prediction curve (in orange)
        ax.plot(X_full['Year'], y_pred_full, color='orange', linestyle='--', linewidth=2)
        # I add a vertical line to mark the separation between training and testing
        ax.axvline(x=CUTOFF_YEAR, color='gray', linestyle=':')
        ax.set_title(f"{col}\nMAE: {mae:.2f}", fontsize=10)
        ax.set_xlabel('')
        ax.set_xticks(np.arange(2005, 2025, 3))
        ax.grid(True, linestyle='--', alpha=0.5)
        
    fig.delaxes(axes_flat[-1])

    legend_elements = [
        mlines.Line2D([], [], color='black', marker='o', linestyle='None', markersize=6, label='Real Data'),
        mlines.Line2D([], [], color='orange', linestyle='--', linewidth=2, label='Hybrid Model Prediction'),
        mlines.Line2D([], [], color='gray', linestyle=':', linewidth=1.5, label='Training Cutoff (2019)')
    ]

    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.94), 
               ncol=3, frameon=False, fontsize=12)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    
    filename = f"{output_dir}/{country}_validation.png"
    plt.savefig(filename, dpi=150)
    plt.close()

print("Validation charts generation completed")

# Global Error Analysis :
df_res = pd.DataFrame(results)
print("\nGlobal Validation Results (Mean Absolute Error) - Hybrid Model")

# I calculate the average error for each indicator, across all countries
summary_errors = df_res.groupby('Indicator')['MAE'].mean().sort_values().reset_index()
summary_errors.columns = ['Indicator', 'Average Error (MAE)']

units_map = {
    'Real_GDP_Per_Capita': '€',
    'GHG_Emissions': 'Tonnes CO2',
    'Income_Distribution_Ratio': 'S80/S20 Ratio',
    'Income_Share_Bottom_40': '% pts',
    'NEET_Rate': '% pts',
    'Unemployment_Rate': '% pts',
    'Renewable_Energy_Share': '% pts'
}

def format_error_with_unit(row):
    indicator = row['Indicator']
    val = row['Average Error (MAE)']
    unit = units_map.get(indicator, '')
    
    if indicator in ['GHG_Emissions', 'Real_GDP_Per_Capita']:
        return f"{val:,.0f} {unit}"
    else:
        return f"{val:.2f} {unit}"

summary_errors['Average Error (MAE)'] = summary_errors.apply(format_error_with_unit, axis=1)

# I save this final table as an image
plt.figure(figsize=(10, 5))
plt.axis('off')

table = plt.table(
    cellText=summary_errors.values,
    colLabels=summary_errors.columns,
    cellLoc='center', loc='center',
    colWidths=[0.5, 0.5]
)

table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 1.8) 

plt.title("Global Model Validation Results (Mean Absolute Error)", fontsize=14, weight='bold')

filename_table = f"{output_dir}/validation_errors_table.png"
plt.savefig(filename_table, bbox_inches='tight', dpi=300)
print(f"Image saved: {filename_table}")