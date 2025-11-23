import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set the visual style for the plots
sns.set_theme(style="whitegrid")


# 1. LOAD DATA

file_path = "/Users/eanzallo/Desktop/M1/data science/Project_Datascience/data/Final_Cleaned_Database.csv"

try:
    df = pd.read_csv(file_path)
    print(f"Data loaded successfully. Rows: {len(df)}")
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    exit()

# Select numeric columns for analysis
numeric_cols = [col for col in df.columns if col not in ['Country', 'Year']]


# 2. DESCRIPTIVE STATISTICS

print("\nDescriptive Statistics :")
print(df[numeric_cols].describe().T)


# 3. EVOLUTION & CONVERGENCE TABLE (MEAN + STD DEV)

print("\nComputing Evolution Table :")

start_year = df['Year'].min()
end_year = df['Year'].max()

# Count number of countries available for start and end years
n_countries_start = df[df['Year'] == start_year]['Country'].nunique()
n_countries_end = df[df['Year'] == end_year]['Country'].nunique()

# Calculate Mean and Standard Deviation for start and end years
stats_start = df[df['Year'] == start_year][numeric_cols].agg(['mean', 'std']).T
stats_end = df[df['Year'] == end_year][numeric_cols].agg(['mean', 'std']).T

# Rename columns for clarity
stats_start.columns = [f'Mean {start_year} ({n_countries_start} countries)', f'Std {start_year}']
stats_end.columns = [f'Mean {end_year} ({n_countries_end} countries)', f'Std {end_year}']

# Combine into a single DataFrame
summary = pd.concat([stats_start, stats_end], axis=1)

# Calculate Evolution of the Mean (%)
summary['Mean Change (%)'] = ((summary[f'Mean {end_year} ({n_countries_end} countries)'] - summary[f'Mean {start_year} ({n_countries_start} countries)']) / summary[f'Mean {start_year} ({n_countries_start} countries)']) * 100

# Reorder columns for better readability
cols_order = [f'Mean {start_year} ({n_countries_start} countries)', f'Std {start_year}', f'Mean {end_year} ({n_countries_end} countries)', f'Std {end_year}', 'Mean Change (%)']
summary = summary[cols_order]

print(summary.round(2))

# Save table as an image
summary_graph = summary.round(2)

plt.figure(figsize=(15, 6))
plt.axis('off')

# Define column widths
widths = [0.15] * 5 

table = plt.table(
    cellText=summary_graph.values,
    rowLabels=summary_graph.index,
    colLabels=summary_graph.columns,
    cellLoc='center', loc='center',
    colWidths=widths
)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 2)

plt.title(f"Evolution of Means and Disparities ({start_year} - {end_year})", fontsize=14, weight='bold', pad=20)
plt.savefig("evolution_table_detailed.png", bbox_inches='tight', dpi=300)
print("Image saved: evolution_table_detailed.png")

      
