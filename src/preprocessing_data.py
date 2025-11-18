import pandas as pd
import os
import io
from functools import reduce

# =============================================================================
# 1. CONFIGURATION AND PATHS
# =============================================================================
print("--- STARTING DATA PREPARATION SCRIPT (PRODUCTION VERSION) ---")

# --- USER-SPECIFIC DIRECTORY PATHS ---
# These paths are based on your folder structure (SDG8, SDG10, SDG13 subfolders)
PATH_SDG8  = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/SDG8'
PATH_SDG10 = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/SDG10'
PATH_SDG13 = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/SDG13'

# Target countries list (Used for filtering all datasets)
TARGET_COUNTRIES = [
    'Germany', 'Austria', 'Belgium', 'Bulgaria', 'Cyprus', 'Croatia', 
    'Denmark', 'Spain', 'Estonia', 'Finland', 'France', 'Greece', 
    'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 
    'Malta', 'Netherlands', 'Poland', 'Portugal', 'Czechia', 'Romania', 
    'Slovakia', 'Slovenia', 'Sweden', 'Switzerland', 'Norway'
]

list_of_dataframes = []
# -----------------------------------------------------------------------------

# =============================================================================
# 2. LOAD COMPLEX SWITZERLAND GHG EMISSIONS (Robust Text Parsing)
# =============================================================================
try:
    print("\n1. Loading Switzerland GHG Data...")
    filename_swiss_ghg = 'Switzerland_greenhouse_gas_emissions.csv'
    path_swiss_ghg = os.path.join(PATH_SDG13, filename_swiss_ghg)
    
    if os.path.exists(path_swiss_ghg):
        # 1. Read file as text to dynamically find the correct header row index
        with open(path_swiss_ghg, 'r', encoding='latin-1', errors='ignore') as f:
            lines = f.readlines()
        
        header_index = -1
        for i, line in enumerate(lines):
            # Header line must contain both 'years' and 'Switzerland'
            if "years" in line.lower() and "switzerland" in line.lower():
                header_index = i
                break
        
        if header_index != -1:
            # 2. Load data from the identified header line
            raw_data = "".join(lines[header_index:])
            df_ch = pd.read_csv(io.StringIO(raw_data), sep=',', encoding='latin-1')
            
            # 3. Identify, rename, and clean columns
            col_year = None; col_val = None
            for col in df_ch.columns:
                c_str = str(col).lower().strip()
                if 'years' in c_str: col_year = col
                if 'switzerland' in c_str and 'percent' in c_str: col_val = col
            
            if col_year and col_val:
                df_ch = df_ch.rename(columns={col_year: 'Year', col_val: 'GHG_Emissions_Switzerland'})
                df_ch = df_ch[['Year', 'GHG_Emissions_Switzerland']]
                df_ch['Country'] = 'Switzerland'
                df_ch = df_ch.dropna()
                df_ch['Year'] = pd.to_numeric(df_ch['Year'], errors='coerce').astype(int)
                
                list_of_dataframes.append(df_ch)
                print(f"   -> OK: Switzerland GHG loaded.")

except Exception as e:
    print(f"   -> ERROR: Crash loading Switzerland GHG data: {e}")

# =============================================================================
# 3. LOAD EUROSTAT AND UNECE DATA (Standardized Loading and Filtering)
# =============================================================================
print("\n2. Loading Eurostat & UNECE Data...")

file_config = {
    'sdg_08_10_real GDP_per_capita.csv':      ('GDP_per_Capita', PATH_SDG8),
    'sdg_08_20_NEET.csv':                     ('NEET_Rate', PATH_SDG8),
    'sdg_08_30_employment_rate_by_sex.csv':   ('Employment_Rate', PATH_SDG8),
    'sdg_10_41_income_distribution.csv':      ('Income_Inequality', PATH_SDG10),
    'sdg_10_50_Income_share_of_the_bottom_40%_of_the_population.csv': ('Income_Share_Bottom_40', PATH_SDG10),
    'Greenhouse_gas_emissions_by_source_sector.csv': ('GHG_Emissions_EU', PATH_SDG13),
    'UNECE_Renewable_Energy_Data.csv':        ('Renewable_Energy_Share', PATH_SDG13) # Final, clean source
}

for filename, (variable_name, folder_path) in file_config.items():
    full_path = os.path.join(folder_path, filename)
    
    if os.path.exists(full_path):
        try:
            # Determine read parameters
            if filename == 'UNECE_Renewable_Energy_Data.csv':
                # FIX: Comma separator + header=1 to skip the first descriptive line
                df_temp = pd.read_csv(full_path, sep=',', encoding='latin-1', header=1) 
            else:
                # Standard read for Eurostat files
                df_temp = pd.read_csv(full_path, sep=',', encoding='latin-1')
            
            # Universal Header Cleanup (lowercase, snake_case)
            df_temp.columns = df_temp.columns.str.strip().str.lower().str.replace(' ', '_', regex=False).str.replace('[^a-z0-9_]', '', regex=True)

            if filename == 'UNECE_Renewable_Energy_Data.csv':
                # FIX: Map UNECE columns (which are now simple strings)
                df_temp = df_temp.rename(columns={
                    'country_e': 'Country',
                    'period': 'Year',
                    'value': variable_name
                })
                df_clean = df_temp[['Country', 'Year', variable_name]].copy()
            
            elif {'geo', 'time_period', 'obs_value'}.issubset(df_temp.columns):
                # Eurostat Standard Mapping
                df_temp = df_temp.rename(columns={'geo': 'Country', 'time_period': 'Year', 'obs_value': variable_name})
                
                # --- FIX DUPLICATES: Sex and Age Filtering ---
                if 'sex' in df_temp.columns:
                    vals = df_temp['sex'].unique()
                    if 't' in vals: df_temp = df_temp[df_temp['sex'] == 't']
                    elif 'total' in vals: df_temp = df_temp[df_temp['sex'] == 'total']
                
                if 'age' in df_temp.columns:
                    vals_age = df_temp['age'].unique()
                    
                    # NEET Rate: Prioritize 15-29 (Standard definition)
                    if variable_name == 'NEET_Rate' and 'y1529' in vals_age:
                        df_temp = df_temp[df_temp['age'] == 'y1529']
                        
                    # Employment Rate: Prioritize 20-64 (Standard EU target group)
                    elif variable_name == 'Employment_Rate':
                        if 'y2064' in vals_age: df_temp = df_temp[df_temp['age'] == 'y2064']
                        elif 'y1564' in vals_age: df_temp = df_temp[df_temp['age'] == 'y1564']

                df_clean = df_temp[['Country', 'Year', variable_name]].copy()
            
            else:
                print(f"   -> FORMAT ERROR: {filename} (Columns are missing or misnamed.)")
                continue
            
            # Final Aggregation (Safety net against any remaining duplicates)
            df_clean = df_clean[df_clean['Country'].isin(TARGET_COUNTRIES)]
            if df_clean.duplicated(subset=['Country', 'Year']).any():
                df_clean = df_clean.groupby(['Country', 'Year'])[variable_name].mean().reset_index()

            if not df_clean.empty:
                list_of_dataframes.append(df_clean)
                print(f"   -> OK: {variable_name}")

        except Exception as e:
            print(f"   -> READ ERROR: {filename} ({e})")
    else:
        print(f"   -> MISSING: {filename}")

# =============================================================================
# 4. FINAL MERGE, HARMONIZATION, AND EXPORT
# =============================================================================
print("\n3. Finalizing Data...")

if list_of_dataframes:
    # 1. MERGE all dataframes
    df_final = reduce(lambda left, right: pd.merge(left, right, on=['Country', 'Year'], how='outer'), list_of_dataframes)
    df_final = df_final.sort_values(by=['Country', 'Year'])
    
    # 2. HARMONIZE GHG (Merge Switzerland + EU columns)
    if 'GHG_Emissions_Switzerland' in df_final.columns and 'GHG_Emissions_EU' in df_final.columns:
        df_final['GHG_Emissions_Total'] = df_final['GHG_Emissions_EU'].fillna(df_final['GHG_Emissions_Switzerland'])
        df_final = df_final.drop(columns=['GHG_Emissions_EU', 'GHG_Emissions_Switzerland'])
    elif 'GHG_Emissions_EU' in df_final.columns:
         df_final = df_final.rename(columns={'GHG_Emissions_EU': 'GHG_Emissions_Total'})

    # 3. ROUNDING (Employment and NEET to 1 decimal place)
    if 'NEET_Rate' in df_final.columns:
        df_final['NEET_Rate'] = df_final['NEET_Rate'].round(1)
    if 'Employment_Rate' in df_final.columns:
        df_final['Employment_Rate'] = df_final['Employment_Rate'].round(1)

    # 4. EXPORT
    output_folder = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data'
    output_path = os.path.join(output_folder, 'Final_Cleaned_Database.csv')
    
    # Saving with semicolon (;) separator for European Excel compatibility
    df_final.to_csv(output_path, index=False, sep=';')
    
    print("\n=== SUCCESS! ===")
    print(f"Database created at: {output_path}")
    print(f"Total observations (Country-Year pairs): {len(df_final)}")
else:
    print("\n=== FAILURE ===")
    print("No data loaded. Check file paths and encodings.")

input("\nPress Enter to exit...")