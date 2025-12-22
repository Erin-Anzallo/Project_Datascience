# 2030 SDG Monitor: Sustainability Trends & Forecasts

## Project Overview

The **2030 SDG Monitor** is a data science project designed to analyze, forecast and visualize the progress of European countries towards the United Nations Sustainable Development Goals (SDGs) for the year 2030.

Focusing on **SDG 8 (Decent Work)**, **SDG 10 (Reduced Inequalities)**, and **SDG 13 (Climate Action)**, this project utilizes a predictive pipeline based on historical data (2005–2019) to project future trends and assess whether countries are on track to meet EU targets.

## Key Features

*   **Predictive Modeling:** Forecasts indicators up to 2030 using Linear Regression models.
*   **Hybrid Methodology:** Combines time-series trends with autoregressive dynamics (lagged socio-economic variables).
*   **Model Validation:** Includes a backtesting module to evaluate model accuracy (MAE) using a 2019 cutoff (pre-pandemic).
*   **Interactive Dashboard:** A web-based interface (Plotly Dash) featuring:
    *   Choropleth maps for European overview.
    *   Trend lines comparing historical data, forecasts and 2030 targets.
    *   A color system (Green/Orange/Red) to visualize distance to targets.

## Project Structure

```text
Project_Datascience/
├── data/
│   └── Final_Cleaned_Database.csv    # Historical dataset (2005-2022)
├── results/
│   ├── descriptive_analysis/         # Exploratory data analysis charts
│   ├── forecast_2030/                # Generated forecast data & static plots
│   └── model_validation_plot/        # Backtesting performance charts
├── src/
│   ├── dashboard.py                  # Interactive Dash application
│   ├── descriptive_analysis.py       # Descriptive analysis script
│   ├── forecast_to_2030.py           # Main forecasting script
│   ├── model_validation.py           # Backtesting & error analysis script
│   └── preprocessing_data.py         # Data preprocessing script
└── README.md
```

## Installation & Requirements

This project requires **Python 3.9+**. Install the necessary dependencies:

```bash
pip install -R requirements.txt
```

## Usage

### 1. Data Preprocessing
Clean and prepare the raw dataset for analysis.

```bash
python src/preprocessing_data.py
```
*Output: Generates the cleaned dataset `data/Final_Cleaned_Database.csv`.*

### 2. Descriptive Analysis
Perform exploratory data analysis to visualize historical trends.

```bash
python src/descriptive_analysis.py
```
*Output: Generates distribution and correlation plots in `results/descriptive_analysis/`.*

### 3. Model Validation (Optional)
Run the backtesting script to evaluate the reliability of the models. It trains on data up to 2019 and tests on 2020-2022.

```bash
python src/model_validation.py
```
*Output: Generates validation charts and an error summary table in `results/model_validation_plot/`.*

### 4. Generate Forecasts
Run the main forecasting script to generate predictions for 2023-2030.

```bash
python src/forecast_to_2030.py
```
*Output: Creates `graph_forecast_data.csv` and static trend images in `results/forecast_2030/`.*

### 5. Launch the Dashboard
Start the interactive web application to explore the results.

```bash
python src/dashboard.py
```
*Output: The app will run locally. Open your browser at `http://127.0.0.1:8050/`.*

## Methodology

To address the complexity of socio-economic and environmental indicators, we developed a **Linear Regression pipeline combining temporal trends and autoregressive dynamics**:

1.  **Socio-Economic Indicators (e.g., GDP, Unemployment, Inequality):**
    *   Modeled using **Lagged Features** (e.g., $X_{t-1}$) to capture system inertia and causal dependencies.
    *   *Example:* Unemployment Rate is predicted using the previous year's NEET Rate and Income Distribution.

2.  **Environmental Indicators (GHG Emissions, Renewable Share):**
    *   Modeled using **Time-Series Trends** (Year as the sole feature).
    *   This approach captures the structural, often policy-driven trajectory of green transition metrics.

**Note on Training:** The models are trained on data from **2005 to 2019** to avoid biasing the long-term trend with the specific anomalies of the COVID-19 pandemic years.

## Indicators & Targets

| Indicator | SDG | 2030 Target / Goal |
| :--- | :--- | :--- |
| **Real GDP Per Capita** | SDG 8 | Growth Trend |
| **Unemployment Rate** | SDG 8 | ≤ 5.0% |
| **NEET Rate** | SDG 8 | ≤ 9.0% |
| **Income Distribution (S80/S20)** | SDG 10 | Reduction Trend |
| **Income Share Bottom 40%** | SDG 10 | Increase Trend |
| **Renewable Energy Share** | SDG 13 | ≥ 42.5% |
| **GHG Emissions** | SDG 13 | Reduction Trend |

## Authors

*   **Erin Anzallo** - *M1 Data Science Project*