import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.lines as mlines  

# I set the visual style for the plots
sns.set_theme(style="whitegrid")

# 1. LOAD DATA

file_path = "/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/Final_Cleaned_Database.csv"

try:
    df = pd.read_csv(file_path)
    print(f"Data loaded successfully. Total rows: {len(df)}")
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    exit()

# I select numeric columns for analysis
numeric_cols = [col for col in df.columns if col not in ['Country', 'Year']]


# 2. CONFIGURE BACKTESTING STRATEGY

CUTOFF_YEAR = 2019 

print("\nStarting Model Validation (Backtesting)")
print(f"Training Period: 2005 - {CUTOFF_YEAR}")
print(f"Testing Period: {CUTOFF_YEAR + 1} - 2022")

# I create a directory to save the charts
output_dir = "validation_charts"
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory '{output_dir}' created")

results = []


# 3. COUNTRY-LEVEL VALIDATION LOOP

countries = df['Country'].unique()
print(f"Processing validation for {len(countries)} countries...")

for country in countries:
    df_country = df[df['Country'] == country]
    
    # I split the data into training and testing sets
    train = df_country[df_country['Year'] <= CUTOFF_YEAR]
    test = df_country[df_country['Year'] > CUTOFF_YEAR]
    
    # I skip countries with insufficient data
    if len(train) < 5 or len(test) == 0:
        continue

    # I initialize the figure for this country
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    # I add padding at the top for the title and the legend
    fig.suptitle(f"Model Validation: {country} (Prediction vs Real Data)", fontsize=16, weight='bold', y=0.98)
    axes_flat = axes.flatten() 

    for i, col in enumerate(numeric_cols):
        # 1. I train the model on historical data
        X_train = train['Year'].values.reshape(-1, 1)
        y_train = train[col].values
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # 2. I predict on the test set
        X_test = test['Year'].values.reshape(-1, 1)
        y_real = test[col].values
        y_pred = model.predict(X_test)
        
        # 3. I calculate the error
        mae = mean_absolute_error(y_real, y_pred)
        results.append({'Country': country, 'Indicator': col, 'MAE': mae})
        
        # 4. I plot the results
        ax = axes_flat[i]
        
        # I generate a trend line for the whole period
        years_full = np.arange(2005, 2023).reshape(-1, 1)
        pred_full = model.predict(years_full)
        
        # I plot the real data points
        sns.scatterplot(data=df_country, x='Year', y=col, ax=ax, color='black', s=40)
        
        # I plot the model's prediction line
        ax.plot(years_full, pred_full, color='red', linestyle='--', linewidth=2)
        
        # I mark the cutoff year
        ax.axvline(x=CUTOFF_YEAR, color='gray', linestyle=':')
        
        ax.set_title(f"{col}\nMAE: {mae:.2f}", fontsize=10)
        ax.set_xlabel('')
        
        # I set x-axis ticks every 3 years
        ax.set_xticks(np.arange(2005, 2025, 3))
        
        ax.grid(True, linestyle='--', alpha=0.5)
        
    # I remove the empty subplot
    fig.delaxes(axes_flat[-1])

    # I defined the legend elements 
    legend_elements = [
        mlines.Line2D([], [], color='black', marker='o', linestyle='None', markersize=6, label='Real Data'),
        mlines.Line2D([], [], color='red', linestyle='--', linewidth=2, label='Linear Model'),
        mlines.Line2D([], [], color='gray', linestyle=':', linewidth=1.5, label='Training Cutoff (2019)')
    ]

    # I configure a unified legend at the top of the figure 
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.94), 
               ncol=3, frameon=False, fontsize=12)
    
    # I adjust layout to make room for the legend
    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    
    # I save the chart
    filename = f"{output_dir}/{country}_test.png"
    plt.savefig(filename, dpi=150)
    plt.close()

print("Validation charts generation completed")


# 4. GLOBAL ERROR ANALYSIS

df_res = pd.DataFrame(results)

print("\nGlobal Validation Results (Mean Absolute Error)")

# I calculate the average error per indicator
summary_errors = df_res.groupby('Indicator')['MAE'].mean().sort_values().reset_index()
summary_errors.columns = ['Indicator', 'Average Error (MAE)']

# Unit Definitions 
units_map = {
    'Real_GDP_Per_Capita': '€',
    'GHG_Emissions': 'Tonnes CO2',
    'Income_Distribution_Ratio': 'Ratio',
    'Income_Share_Bottom_40': '% pts',
    'NEET_Rate': '% pts',
    'Unemployment_Rate': '% pts',
    'Renewable_Energy_Share': '% pts'
}

# Smart Formatting Function
def format_error_with_unit(row):
    indicator = row['Indicator']
    val = row['Average Error (MAE)']
    unit = units_map.get(indicator, '')
    
    # Special formatting for large numbers (No decimals needed for millions or thousands)
    if indicator == 'GHG_Emissions':
        return f"{val:,.0f} {unit}" # "9,327,539 Tonnes CO2"
    elif indicator == 'Real_GDP_Per_Capita':
        return f"{val:,.0f} {unit}" # "1,828 €"
    else:
        return f"{val:.2f} {unit}"  # "2.42 % pts"

summary_errors['Average Error (MAE)'] = summary_errors.apply(format_error_with_unit, axis=1)


# Save as image 
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