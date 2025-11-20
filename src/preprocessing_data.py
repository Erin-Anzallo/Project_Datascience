import pandas as pd
import os 

# 1. DEFINE PARAMETERS AND ABSOLUTE PATHS

# Source directory paths for reading data 
PATH_SDG8 = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/SDG8'
PATH_SDG10 = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/SDG10'
PATH_SDG13 = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/SDG13'

# Destination directory path for saving the final output file
OUTPUT_DIR = '/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data'
output_file_name = 'Final_cleaned_database.csv'

# Target countries for geographical filtering
TARGET_COUNTRIES = [
    'Germany', 'Austria', 'Belgium', 'Bulgaria', 'Cyprus', 'Croatia', 
    'Denmark', 'Spain', 'Estonia', 'Finland', 'France', 'Greece', 
    'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 
    'Malta', 'Netherlands', 'Poland', 'Portugal', 'Czechia', 'Romania', 
    'Slovakia', 'Slovenia', 'Sweden', 'Switzerland', 'Norway'
]

# Mapping variable names to their file names and base directory paths
file_mapping_and_paths = {
    # Variable_Name: (File_Name, Path_Variable)
    'Real_GDP_Per_Capita': ('real_GDP_per_capita.csv', PATH_SDG8),
    'NEET_Rate': ('NEET.csv', PATH_SDG8),
    'Unemployment_Rate': ('unemployment-rate.csv', PATH_SDG8),
    
    'Income_Distribution_Ratio': ('income_distribution.csv', PATH_SDG10),
    'Income_Share_Bottom_40': ('income_share_of_the_bottom_40%_of_the_population.csv', PATH_SDG10),
    
    'Renewable_Energy_Share': ('renewable-share-energy.csv', PATH_SDG13),
    'GHG_Emissions': ('total-ghg-emissions.csv', PATH_SDG13)
}

# Group files based on their column structure for batch cleaning
files_structure_1 = ['NEET_Rate', 'Unemployment_Rate', 'Renewable_Energy_Share', 'GHG_Emissions']
files_structure_2 = ['Real_GDP_Per_Capita', 'Income_Distribution_Ratio', 'Income_Share_Bottom_40']

cleaned_dfs = []

# 2. DATA CLEANING FUNCTIONS

def clean_structure_1(full_file_path, var_name):
    """Handles files with columns: Entity, Year, and a long Value column (Structure 1)."""
    df = pd.read_csv(full_file_path) 
    value_col = df.columns[-1]
    
    df_clean = df[['Entity', 'Year', value_col]].copy()
    df_clean.rename(columns={'Entity': 'Country', 'Year': 'Year', value_col: var_name}, inplace=True)
    return df_clean

def clean_structure_2(full_file_path, var_name):
    """Handles Eurostat files with columns: geo, TIME_PERIOD, and OBS_VALUE (Structure 2)."""
    df = pd.read_csv(full_file_path)
    
    df_clean = df[['geo', 'TIME_PERIOD', 'OBS_VALUE']].copy()
    df_clean.rename(columns={'geo': 'Country', 'TIME_PERIOD': 'Year', 'OBS_VALUE': var_name}, inplace=True)
    return df_clean

# 3. PROCESSING, MERGING, AND FILTERING (2005-2022)

# Process all files
for var_name, (file_name, file_path_dir) in file_mapping_and_paths.items():
    # Crucial step: Construct the full absolute path for reading the file
    full_path_read = os.path.join(file_path_dir, file_name)
    
    try:
        if var_name in files_structure_1:
            df_clean = clean_structure_1(full_path_read, var_name)
        elif var_name in files_structure_2:
            df_clean = clean_structure_2(full_path_read, var_name)
        cleaned_dfs.append(df_clean)
    except FileNotFoundError:
        print(f"ERROR: File not found at location: {full_path_read}. Check your folder structure.")
        # Stop execution if a file is missing
        exit() 

# Sequential Merge (Outer Join to keep all Country-Year combinations)
if cleaned_dfs:
    df_merged = cleaned_dfs[0]
    for i in range(1, len(cleaned_dfs)):
        df_merged = pd.merge(df_merged, cleaned_dfs[i], on=['Country', 'Year'], how='outer')

    # 1. Temporal Filtering: 2005 to 2022
    df_final = df_merged[(df_merged['Year'] >= 2005) & (df_merged['Year'] <= 2022)].copy()

    # 2. Geographical Filtering: Only TARGET_COUNTRIES
    df_final = df_final[df_final['Country'].isin(TARGET_COUNTRIES)].copy()

    # Final cleanup and sorting
    df_final.dropna(subset=['Country', 'Year'], inplace=True) 
    df_final.sort_values(by=['Country', 'Year'], inplace=True)

    # 4. FINAL SAVE
    
    # Construct the full absolute path for writing the file
    output_path_write = os.path.join(OUTPUT_DIR, output_file_name)

    # Save the final cleaned dataframe
    df_final.to_csv(output_path_write, index=False)
    
    print(f"SUCCESS: Final database created and saved to:")
    print(f"{output_path_write}")
    print(f"Dimensions: {len(df_final)} rows, {len(df_final.columns)} columns.")
else:
    print("\nERROR: No files could be loaded. The final database was not created.")