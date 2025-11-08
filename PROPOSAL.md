# Europe 2030: Are we on track for sustainable growth, equality, and climate action?

## Category: Data Analysis & Visualization

## Problem statement or motivation

The Sustainable Development Goals (SDGs) set by the United Nations aim
to achieve by 2030 a balance between economic progress, social equity,
and environmental protection. However, despite the efforts made, it
remains difficult to assess whether European countries are truly on the
right track.

This project seeks to answer a simple question:
Will European countries achieve SDGs 8, 10, and 13 by 2030?

The three selected SDGs represent the three main pillars of sustainable
development:

-   SDG 8 -- Decent Work and Economic Growth (economic pillar)
-   SDG 10 -- Reduced Inequalities (social pillar)
-   SDG 13 -- Climate Action (environmental pillar)

I choose these goals because they are interconnected: a strong economy
can help reduce inequalities but may also affect the environment.
Analyzing them together makes it possible to better understand the
trade-offs between growth, social justice, and sustainability.

## Planned approach and technologies

The data will be directly extracted from the Eurostat database, which
provides harmonized indicators for all European countries.
The project will include the member states of the European Union, as
well as Switzerland, Norway, and the United Kingdom, to provide a
broader European perspective.

Methodology:

1.  Collect and clean data for the period 2005--2024.
2.  Project trends up to 2030 using statistical models (linear
    regression) or simple machine learning models like scikit-learn.
3.  Create visualizations:
    -   Evolution charts for each country.
    -   Interactive map of Europe:
        -   Countries shown in green if they are on track,
        -   orange if progress is slow,
        -   red if they are moving away from the target.
    -   Clicking on a country will display its corresponding trend
        curves.

## Expected challenges and how you'll address them

-   Short time series (≈ 20 years): compare several models and validate
    results using recent years.
-   Missing or inconsistent data: apply imputation and normalization
    methods.
-   Differences between countries: harmonize units and align available
    time periods.

## Success criteria (how will you know it's working?)

-   Establishes a clear and reproducible data processing pipeline.
-   Generates coherent and interpretable projections up to 2030.
-   Produces readable and informative interactive visualizations.
-   Classifies countries according to their level of progress toward
    SDGs 8, 10, and 13 (green, orange, red).

## Stretch goals (if time permits)

-   Create a global SDG performance index (8-10-13) to summarize
    progress by country.
-   Develop an interactive dashboard (using Streamlit or Dash) to
    dynamically explore results and projections.