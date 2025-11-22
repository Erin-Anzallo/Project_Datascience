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

print("\n--- Descriptive Statistics ---")
print(df[numeric_cols].describe().T)


# 3. EVOLUTION TABLE (START vs END)

print("\n--- Computing Evolution Table ---")

start_year = df['Year'].min()
end_year = df['Year'].max()

# Calculate means for the start and end years
start_means = df[df['Year'] == start_year][numeric_cols].mean()
end_means = df[df['Year'] == end_year][numeric_cols].mean()

# Count number of available countries for each period
n_countries_start = df[df['Year'] == start_year]['Country'].nunique()
n_countries_end = df[df['Year'] == end_year]['Country'].nunique()

# Create a summary DataFrame
summary = pd.DataFrame({
    f'Mean {start_year} ({n_countries_start} countries)': start_means,
    f'Mean {end_year} ({n_countries_end} countries)': end_means
})

col_start = f'Mean {start_year} ({n_countries_start} countries)'
col_end = f'Mean {end_year} ({n_countries_end} countries)'

# Calculate percentage change
summary['Change (%)'] = ((summary[col_end] - summary[col_start]) / summary[col_start]) * 100

print(summary.round(2))

# Save table as an image
summary_graph = summary.round(2)

plt.figure(figsize=(12, 6))
plt.axis('off')

table = plt.table(
    cellText=summary_graph.values,
    rowLabels=summary_graph.index,
    colLabels=summary_graph.columns,
    cellLoc='center', loc='center',
    colWidths=[0.3, 0.3, 0.2]
)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 2)

plt.title(f"Average Evolution ({start_year} - {end_year})", fontsize=14, weight='bold', pad=20)
plt.savefig("evolution_table.png", bbox_inches='tight', dpi=300)
print("Image saved: evolution_table.png")

