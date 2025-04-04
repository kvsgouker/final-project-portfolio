# Political Migration and Its Electoral Impact: A Data-Driven Study

This project investigates how internal migration across U.S. counties shapes political outcomes, with a focus on voter turnout and partisan shifts. By combining election returns and IRS migration data, it explores how demographic movement influences electoral behavior—particularly in Florida and historically predictive (“bellwether”) counties.

## Summary

The goal of this study is to determine how patterns of residential mobility contribute to political change at the county level. The project integrates datasets from the Harvard Dataverse and the IRS to explore the relationship between migration trends and voting behavior in national elections from 2000 to 2020.

## Data Sources

- **Harvard Dataverse** — County-level U.S. presidential election returns (2000–2020)
- **IRS** — County-to-county migration data (2011–2019)
- FIPS codes used to align datasets geographically

## Methods

- Cleaned and merged datasets using FIPS identifiers
- Identified counties with strong historical alignment to national outcomes
- Mapped and visualized migration trends and turnout changes
- Explored partisan dynamics at the county level
- Acknowledged granularity and causality limitations (aggregated data, not individuals)

## Key Insights

- Residential mobility appears to correlate with changing turnout rates and partisan leanings
- Bellwether counties show detectable migration-linked shifts in voter behavior
- Visualization and exploratory models suggest migration as a key driver in evolving electoral maps

## Tools & Dependencies

This project was developed using the following tools:

- R and RStudio
- `dplyr` / `tidyverse`
- `ggplot2`
- `knitr` / `pander` / `here`

All analyses were conducted in RMarkdown with outputs formatted for both PDF and HTML rendering.

## Limitations

- Migration data excludes non-tax filers and only captures net flows
- Election returns are at the county level, not individual voter data
- Correlation does not imply causation; this study provides a demographic lens, not definitive proof

## Author

Kyle Salgado-Gouker  
February 2023  
