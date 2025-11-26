import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression

# ==============================================================================
# 1. CONFIGURATION & PATHS
# ==============================================================================

# I get the absolute path of the current script (src/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# I go up one level to the project root
project_root = os.path.dirname(current_dir)

# I define the paths relative to the root
file_path = os.path.join(project_root, "data", "Final_Cleaned_Database.csv")
output_dir = os.path.join(project_root, "results")

# I make sure the results folder exists
os.makedirs(output_dir, exist_ok=True)
print(f"📂 Output directory ready: {output_dir}")

# ==============================================================================
# 2. DEFINING TARGETS (2030 OBJECTIVES)
# ==============================================================================
# Based on EU policies (Fit for 55, Social Action Plan...)
TARGETS = {
    # SDG 8: Decent Work & Economic Growth
    'NEET_Rate': {'goal': 9.0, 'direction': 'down'},           # EU Target < 9%
    'Unemployment_Rate': {'goal': 5.0, 'direction': 'down'},   # Frictional unemployment ~5%
    'Real_GDP_Per_Capita': {'goal': 'growth', 'direction': 'up'}, # Must be higher than today

    # SDG 10: Reduced Inequalities
    'Income_Distribution_Ratio': {'goal': 4.0, 'direction': 'down'}, # Ratio < 4
    'Income_Share_Bottom_40': {'goal': 24.0, 'direction': 'up'},     # Share > 24%

    # SDG 13: Climate Action
    'Renewable_Energy_Share': {'goal': 42.5, 'direction': 'up'},    # EU Target 2030: 42.5%
    'GHG_Emissions': {'goal': 'reduction_vs_2005', 'direction': 'down'} # -40% vs 2005 levels
}

# ==============================================================================
# 3. LOAD DATA
# ==============================================================================
try:
    df = pd.read_csv(file_path)
    print(f"✅ Data loaded successfully. Rows: {len(df)}")
except FileNotFoundError:
    print(f"❌ Error: File not found at {file_path}")
    exit()

numeric_cols = [col for col in df.columns if col not in ['Country', 'Year']]
countries = df['Country'].unique()

# ==============================================================================
# 4. PREDICTION ENGINE (LINEAR REGRESSION)
# ==============================================================================
projections_list = []
print("\n🚀 Running projections for 2030 (excluding 2020 outlier)...")

for country in countries:
    df_country = df[df['Country'] == country]
    country_result = {'Country': country}
    
    for col in numeric_cols:
        # --- CRITICAL STEP: EXCLUDING 2020 ---
        # I exclude the year 2020 from the training set because it is a massive outlier (COVID-19).
        # Including it would bias the trend downward for economic indicators.
        df_train = df_country[df_country['Year'] != 2020]
        
        # Prepare data
        X = df_train['Year'].values.reshape(-1, 1)
        y = df_train[col].values
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict 2030
        pred_2030 = model.predict([[2030]])[0]
        
        # Get latest known value (usually 2022) for comparison
        last_real_val = df_country[col].values[-1]
        
        country_result[col + '_2030'] = round(pred_2030, 2)
        country_result[col + '_Latest'] = round(last_real_val, 2)

    projections_list.append(country_result)

df_proj = pd.DataFrame(projections_list)

# ==============================================================================
# 5. CLASSIFICATION (GREEN / ORANGE / RED)
# ==============================================================================
print("⚖️  Assigning status (Green/Orange/Red)...")

def get_status(row, indicator):
    target = TARGETS[indicator]
    val_2030 = row[indicator + '_2030']
    val_latest = row[indicator + '_Latest']
    
    # Case 1: Relative Targets (GDP & Emissions)
    if indicator == 'Real_GDP_Per_Capita':
        # Green if GDP in 2030 is higher than today (Growth)
        return 'Green' if val_2030 > val_latest else 'Red'
        
    if indicator == 'GHG_Emissions':
        # Retrieve the 2005 value for this country
        try:
            val_2005 = df[(df['Country'] == row['Country']) & (df['Year'] == 2005)]['GHG_Emissions'].values[0]
            target_val = val_2005 * 0.60 # Target: -40% compared to 2005
            
            if val_2030 <= target_val: return 'Green' # Target met
            elif val_2030 < val_latest: return 'Orange' # Improving but too slow
            else: return 'Red' # Worsening
        except:
            return 'Orange' if val_2030 < val_latest else 'Red'

    # Case 2: Fixed Targets (Unemployment, NEET, Renewables...)
    goal = target['goal']
    direction = target['direction']
    
    if direction == 'down':
        if val_2030 <= goal: return 'Green'
        elif val_2030 < val_latest: return 'Orange'
        else: return 'Red'
        
    elif direction == 'up':
        if val_2030 >= goal: return 'Green'
        elif val_2030 > val_latest: return 'Orange'
        else: return 'Red'

# Apply classification
for col in numeric_cols:
    df_proj['Status_' + col] = df_proj.apply(lambda row: get_status(row, col), axis=1)

# ==============================================================================
# 6. GLOBAL SCORE & FINAL GRADE
# ==============================================================================
score_map = {'Green': 3, 'Orange': 2, 'Red': 1}
status_cols = [c for c in df_proj.columns if 'Status_' in c]

def calculate_score(row):
    # Calculate average score across the 7 indicators
    scores = [score_map[row[c]] for c in status_cols]
    return round(sum(scores) / len(scores), 2)

df_proj['Global_Score'] = df_proj.apply(calculate_score, axis=1)

def get_grade(score):
    if score >= 2.5: return 'On Track (Green)'       
    elif score >= 1.8: return 'Progressing (Orange)' 
    else: return 'Off Track (Red)'                   

df_proj['Final_Grade'] = df_proj['Global_Score'].apply(get_grade)

# ==============================================================================
# 7. SAVE RESULTS
# ==============================================================================
output_file = os.path.join(output_dir, "final_projections_2030.csv")
df_proj.to_csv(output_file, index=False)
print(f"\n💾 Final results saved to: '{output_file}'")

# Display Leaderboard
summary = df_proj[['Country', 'Global_Score', 'Final_Grade']].sort_values(by='Global_Score', ascending=False)
print("\n--- 🏆 FINAL LEADERBOARD 2030 ---")
print(summary.head(10))
print("...")
print(summary.tail(5))