# Import the necessary tools 
import pandas as pd
import os

# 1. PARAMETERS AND PATHS DEFINITION

# Absolute paths provided by the user 
PATH_SDG8 = './data/SDG8'
PATH_SDG10 = './data/SDG10'
PATH_SDG13 = './data/SDG13'
OUTPUT_DIR = './data'
output_file_name = 'Final_cleaned_database.csv' 

# Target countries list 
TARGET_COUNTRIES = [
    'Germany', 'Austria', 'Belgium', 'Bulgaria', 'Cyprus', 'Croatia', 
    'Denmark', 'Spain', 'Estonia', 'Finland', 'France', 'Greece', 
    'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 
    'Netherlands', 'Poland', 'Portugal', 'Czechia', 'Romania', 
    'Slovakia', 'Slovenia', 'Sweden', 'Switzerland', 'Norway'
]

# File mapping (Variable name: (File name, Path directory))
file_mapping_and_paths = {
    'Real_GDP_Per_Capita': ('real_GDP_per_capita.csv', PATH_SDG8),
    'NEET_Rate': ('NEET.csv', PATH_SDG8),
    'Unemployment_Rate': ('unemployment-rate.csv', PATH_SDG8),
    'Income_Distribution_Ratio': ('income_distribution.csv', PATH_SDG10),
    'Income_Share_Bottom_40': ('income_share_of_the_bottom_40%_of_the_population.csv', PATH_SDG10),
    'Renewable_Energy_Share': ('renewable-share-energy.csv', PATH_SDG13),
    'GHG_Emissions': ('total-ghg-emissions.csv', PATH_SDG13)
}

# I define two lists to handle different file structures (e.g. Our World in Data vs Eurostat)
# files_structure_1 uses clean_structure_1 (Entity, Year, Value) and files_structure_2 uses clean_structure_2 (geo, TIME_PERIOD, OBS_VALUE)
files_structure_1 = ['NEET_Rate', 'Unemployment_Rate', 'Renewable_Energy_Share', 'GHG_Emissions']
files_structure_2 = ['Real_GDP_Per_Capita', 'Income_Distribution_Ratio', 'Income_Share_Bottom_40']
cleaned_dfs = []

# Dynamic Filtering Parameters
START_YEARS = {
    'Bulgaria': 2006, 'Cyprus': 2006, 'Croatia': 2010, 
    'Romania': 2007, 'Switzerland': 2007,
}
DEFAULT_START_YEAR = 2005
END_YEAR = 2022

# 2. DATA CLEANING FUNCTIONS

def clean_structure_1(full_file_path, var_name):
    #Cleans files with the 'Entity, Year, Long_Value_Name' structure.
    df = pd.read_csv(full_file_path) 
    # Check for required columns
    if 'Entity' not in df.columns or 'Year' not in df.columns:
        raise KeyError(f"Missing required columns ('Entity', 'Year') in loaded file: {full_file_path}")
    # I assume the value is always in the last column for this structure (typical of Our World in Data)
    value_col = df.columns[-1]
    df_clean = df[['Entity', 'Year', value_col]].copy()
    df_clean.rename(columns={'Entity': 'Country', 'Year': 'Year', value_col: var_name}, inplace=True)
    return df_clean

def clean_structure_2(full_file_path, var_name):
    #Cleans Eurostat files with the 'geo, TIME_PERIOD, OBS_VALUE' structure.
    df = pd.read_csv(full_file_path)
    # Check for required columns
    if 'geo' not in df.columns or 'TIME_PERIOD' not in df.columns or 'OBS_VALUE' not in df.columns:
        # Raise an informative error if columns are missing
        raise KeyError(f"Missing required columns in loaded file: {full_file_path}")
        
    df_clean = df[['geo', 'TIME_PERIOD', 'OBS_VALUE']].copy()
    df_clean.rename(columns={'geo': 'Country', 'TIME_PERIOD': 'Year', 'OBS_VALUE': var_name}, inplace=True)
    return df_clean

# 3. PROCESSING AND MERGING LOOP

# Process and merge data
for var_name, (file_name, file_path_dir) in file_mapping_and_paths.items():
    # Construct the full path for reading
    full_path_read = os.path.join(file_path_dir, file_name)
    
    try:
        if var_name in files_structure_1:
            df_clean = clean_structure_1(full_path_read, var_name)
        elif var_name in files_structure_2:
            # CORRECT CALL: Using the variable 'full_path_read'
            df_clean = clean_structure_2(full_path_read, var_name)
        cleaned_dfs.append(df_clean)
        
    except FileNotFoundError:
        print(f"ERROR: File not found at path: {full_path_read}. Check directory structure.")
        exit() 
    except KeyError as e:
        print(f"ERROR: Missing column while processing file {file_name}. Details: {e}")
        exit()

# Sequential Merge
if cleaned_dfs:
    df_merged = cleaned_dfs[0]
    for i in range(1, len(cleaned_dfs)):
        df_merged = pd.merge(df_merged, cleaned_dfs[i], on=['Country', 'Year'], how='outer')

# 4. DYNAMIC FILTERING AND FINAL SAVE

# Apply dynamic start year filter
    # I create a series of start years: specific year if in START_YEARS, else DEFAULT_START_YEAR (2005)
    start_year_series = df_merged['Country'].map(START_YEARS).fillna(DEFAULT_START_YEAR)

    # I apply 3 filters: keep only target countries, keep years >= dynamic start year, and keep years <= 2022
    df_final = df_merged[
    (df_merged['Country'].isin(TARGET_COUNTRIES)) &
    (df_merged['Year'] >= start_year_series) & 
    (df_merged['Year'] <= END_YEAR)
    ].copy()

# Cleanup and final sort
    df_final.dropna(subset=['Country', 'Year'], inplace=True) 
    df_final.sort_values(by=['Country', 'Year'], inplace=True)

# Save the raw cleaned database (with NaNs, ready for imputation)
    output_path_write = os.path.join(OUTPUT_DIR, output_file_name)
    df_final.to_csv(output_path_write, index=False)

    print("SUCCESS: Final database created and saved to:")
    print(f"{output_path_write}")
    print(f"Dimensions: {len(df_final)} rows, {len(df_final.columns)} columns.")
else:
    print("\nERROR: No files could be loaded. The final database was not created.")
