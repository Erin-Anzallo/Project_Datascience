# Import the necessary tools 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set the visual style for the plots
sns.set_theme(style="whitegrid")

# Robust path configuration 
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# 1. LOAD DATA
file_path = os.path.join(project_root, "data", "Final_cleaned_database.csv")

try:
    df = pd.read_csv(file_path)
    print(f"Data loaded successfully. Rows: {len(df)}")
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")

output_dir = os.path.join(project_root, "results", "descriptive_analysis_plot")
os.makedirs(output_dir, exist_ok=True)

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

# Calculate evolution of the mean (%)
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
plt.savefig(f"{output_dir}/evolution_table_detailed.png", bbox_inches='tight', dpi=300)
print("Image saved: evolution_table_detailed.png")


# 4. TREND CHARTS BY SDG
print("\nGenerating charts by SDG :")

# aggregate data by year to get the European average
# standard deviation to visualize the disparity between countries
annual_means = df.groupby('Year')[numeric_cols].mean()
annual_std = df.groupby('Year')[numeric_cols].std()

def plot_indicators(indicators, title, filename):
    
    n_cols = len(indicators)
    fig, axes = plt.subplots(1, n_cols, figsize=(6 * n_cols, 5))
    fig.suptitle(title, fontsize=16, weight='bold')
    
    # Handle the case where there is only one chart (axes is not a list)
    if n_cols == 1:
        axes = [axes]

    colors = ['green', 'orange', 'blue', 'red']
    
    # Define the X-axis range: from the first to the last year, with a step of 3.
    min_year = int(annual_means.index.min())
    max_year = int(annual_means.index.max())
    years_ticks = range(min_year, max_year + 1, 3) # Step of 3 (2005, 2008, 2011...)
    
    for i, col in enumerate(indicators):
        ax = axes[i]
        color = colors[i % len(colors)]
        
        # 1. Plot the mean line 
        sns.lineplot(data=annual_means, x=annual_means.index, y=col, ax=ax, 
                     color=color, linewidth=3, marker='o')
        
        # 2. Plot the standard deviation 
        # The shaded area shows how spread out the countries are around the mean
        ax.fill_between(annual_means.index, 
                        annual_means[col] - annual_std[col], 
                        annual_means[col] + annual_std[col], 
                        color=color, alpha=0.15, label='Std Dev (Disparity)')
        
        # Clean up titles (remove underscores from column names)
        ax.set_title(col.replace('_', ' '), fontsize=12, weight='bold')
        ax.set_xlabel('Year')
        
        # Apply the 3-year step to the X-axis for better readability
        ax.set_xticks(years_ticks)
        
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(f"{output_dir}/{filename}", dpi=300)
    print(f"Image saved: {filename}")

# SDG 8: Focus on Economic Growth and Employment
indicators_sdg8 = ['Real_GDP_Per_Capita', 'NEET_Rate', 'Unemployment_Rate']
plot_indicators(indicators_sdg8, "SDG 8: Decent Work and Economic Growth", "evolution_sdg8.png")

# SDG 10: Focus on Inequalities
indicators_sdg10 = ['Income_Distribution_Ratio', 'Income_Share_Bottom_40']
plot_indicators(indicators_sdg10, "SDG 10: Reduced Inequalities", "evolution_sdg10.png")

# SDG 13: Focus on Climate Transition
indicators_sdg13 = ['Renewable_Energy_Share', 'GHG_Emissions']
plot_indicators(indicators_sdg13, "SDG 13: Climate Action", "evolution_sdg13.png")



# 5. CORRELATION MATRIX

print("\nGenerating Correlation Matrix :")

# Create a heatmap to identify relationships between different goals  

plt.figure(figsize=(10, 8))

# Compute the Pearson correlation matrix to compare every indicator against the others
# It measures the linear relationship: +1 means they increase together (strong positive relationship)
# -1 means they move in opposite directions (strong negative relationship), and the diagonal is always 1.0 (self-correlation)
corr_matrix = df[numeric_cols].corr()

# Create the heatmap
sns.heatmap(corr_matrix, 
            annot=True,       # Write the exact coefficient in each cell
            cmap='coolwarm',  # Red = positive correlation, Blue = negative, White = neutral
            fmt=".2f",        # Round to 2 decimal places for readability
            linewidths=0.5)   # Add white lines between cells to make it cleaner

plt.title("Correlation Matrix of SDG Indicators", fontsize=14)
plt.tight_layout() # Adjust layout to make sure labels are not cut off

# save the image
plt.savefig(f"{output_dir}/correlation_matrix.png", dpi=300)
print("Image saved: correlation_matrix.png")

plt.show()
print("Analysis completed")
