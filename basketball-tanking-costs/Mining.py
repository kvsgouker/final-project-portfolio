# Standard Library
import itertools

# Libraries
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LassoCV, RidgeCV
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif_calc

# Project Modules
from General import show_df_info, pretty_print_df, save_plot
from Paths import FILE_PATH_TO_COMPILED_DATA
from Tables import (
    load_fan_attendance_revenue,
    load_fan_attendance,
    add_lagged_features,
    load_extended_game_history
)
from TankEffects import filter_seasons
from TankLog import TankLog

# Shared Logger
log = TankLog.get_shared_logger()
TRANSFORMATIONS = {
    'identity': lambda x: x,
    'log': lambda x: np.log1p(np.clip(x, a_min=0, a_max=None)),
    'sqrt': lambda x: np.sqrt(np.clip(x, a_min=0, a_max=None)),
    'square': lambda x: x ** 2,
    'inverse': lambda x: 1 / (x + 1e-6)
}


def transformed_univariate_mining(df, target, exclude=None, min_valid_fraction=0.5):
    """
    Evaluate univariate linear regressions between transformed versions of numeric columns
    and a specified target column. Returns a sorted DataFrame of best-fitting candidates.

    Args:
        df (pd.DataFrame): Input DataFrame containing numeric columns.
        target (str): Name of the target column.
        exclude (list[str], optional): List of columns to skip during analysis. Defaults to None.
        min_valid_fraction (float): Minimum fraction of valid observations required for a candidate to be accepted.

    Returns:
        pd.DataFrame: A DataFrame of candidate variables sorted by R-squared.
    """
    if exclude is None:
        exclude = []

    candidates = []

    for col in df.columns:
        if col == target or col in exclude or not pd.api.types.is_numeric_dtype(df[col]):
            continue

        for t_name, t_func in TRANSFORMATIONS.items():
            try:
                transformed_col = f"{col}_{t_name}"
                df[transformed_col] = t_func(df[col])

                if df[transformed_col].var() < 1e-7:
                    log.log(
                        TankLog.EXECUTION_FLOW_LOGGING,
                        f"Skipped {transformed_col} due to low variance.",
                        __file__, "transformed_univariate_mining", 20
                    )
                    continue

                model = sm.OLS.from_formula(
                    f"{target} ~ {transformed_col}",
                    data=df.dropna(subset=[transformed_col, target])
                )
                results = model.fit()

                if results.nobs < len(df) * min_valid_fraction:
                    log.log(
                        TankLog.EXECUTION_FLOW_LOGGING,
                        f"Skipped {transformed_col} due to insufficient valid observations.",
                        __file__, "transformed_univariate_mining", 27
                    )
                    continue

                candidate = {
                    "col": col,
                    "transform": t_name,
                    "r2": results.rsquared,
                    "coef": results.params.iloc[1],
                    "pval": results.pvalues.iloc[1],
                    "stderr": results.bse.iloc[1],
                    "tvalue": results.tvalues.iloc[1],
                    "nobs": results.nobs
                }
                candidates.append(candidate)

                log.log(
                    TankLog.INFO_LOGGING,
                    f"Analyzed {col} ({t_name}): R²={results.rsquared:.4f}, "
                    f"p={results.pvalues.iloc[1]:.4g}, n={results.nobs}",
                    __file__, "transformed_univariate_mining", 35
                )

            except Exception as e:
                log.log(
                    TankLog.WARNING_LOGGING,
                    f"Error processing {col} ({t_name}): {e}",
                    __file__, "transformed_univariate_mining", 40
                )

    if not candidates:
        log.log(
            TankLog.WARNING_LOGGING,
            "No valid candidates were found.",
            __file__, "transformed_univariate_mining", 45
        )
        return pd.DataFrame()

    candidates_df = pd.DataFrame(candidates).sort_values(by='r2', ascending=False).reset_index(drop=True)

    log.log(
        TankLog.INFO_LOGGING,
        f"Total valid candidates collected: {len(candidates_df)}",
        __file__, "transformed_univariate_mining", 50
    )

    return candidates_df


def exhaustive_best_subset(df, target, predictors, k=3, exclude=None):
    """
    Performs exhaustive search to find the best k-variable subset of predictors that
    maximizes R² in a linear regression model predicting the target variable.

    Args:
        df (pd.DataFrame): The dataset containing the target and predictor variables.
        target (str): The name of the target variable (dependent variable).
        predictors (list[str]): A list of candidate predictor (independent) variable names.
        k (int): The number of predictors to include in each subset (default is 3).
        exclude (list[str], optional): A list of predictors to exclude from consideration.

    Returns:
        tuple: (best_r2, best_subset) where:
            - best_r2 (float): The highest R² score achieved among all subsets tested.
            - best_subset (tuple): The combination of predictors that yielded this R².
              If no valid model is found, returns (None, None).
    """
    if exclude is None:
        exclude = []

    if not predictors:
        print("No predictors selected for exhaustive best subset.")
        return None, None

    # Remove excluded variables from the predictor list
    predictors = [p for p in predictors if p not in exclude]

    best_r2 = -1
    best_subset = None

    # Generate all possible k-sized combinations of predictors
    for subset in itertools.combinations(predictors, k):
        try:
            # Build formula: target ~ var1 + var2 + ...
            formula = f"{target} ~ {' + '.join(subset)}"
            model = sm.OLS.from_formula(
                formula,
                data=df.dropna(subset=list(subset) + [target])
            )
            results = model.fit()

            # Track the best performing subset by R²
            if results.rsquared > best_r2:
                best_r2 = results.rsquared
                best_subset = subset
        except Exception:
            continue  # Skip any subset that causes an error

    return best_r2, best_subset


def lasso_ridge_selection(df, target, predictors, exclude=None):
    """
    Performs variable selection using Lasso and Ridge regression with cross-validation.
    This function identifies which predictors are most relevant in predicting the target variable.

    Args:
        df (pd.DataFrame): The dataset containing both predictor and target variables.
        target (str): The name of the target variable (dependent variable).
        predictors (list[str]): A list of candidate predictor variable names.
        exclude (list[str], optional): A list of predictor names to exclude from the analysis.

    Returns:
        dict: A dictionary with the following keys:
            - "lasso" (list[str]): Predictor names selected by Lasso (non-zero coefficients).
            - "ridge" (list[str]): All predictors, since Ridge does not perform feature elimination.
            - "lasso_score" (float): R² score of the Lasso model on the full dataset.
            - "ridge_score" (float): R² score of the Ridge model on the full dataset.
    """
    if exclude is None:
        exclude = []

    if not predictors:
        print("No predictors selected for Lasso/Ridge selection.")
        return {}

    # Filter out excluded predictors
    predictors = [p for p in predictors if p not in exclude]

    # Prepare the input (X) and output (y) data, handling NaNs
    X = df[predictors].fillna(0).values
    y = df[target].fillna(0).values

    # Standardize the predictor variables
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit Lasso and Ridge with cross-validation
    lasso = LassoCV(cv=5).fit(X_scaled, y)
    ridge = RidgeCV(cv=5).fit(X_scaled, y)

    # Lasso sets irrelevant coefficients to zero — select only non-zero ones
    lasso_vars = [p for coef, p in zip(lasso.coef_, predictors) if abs(coef) > 1e-6]

    return {
        "lasso": lasso_vars,
        "ridge": predictors,  # Ridge regression does not zero out coefficients
        "lasso_score": lasso.score(X_scaled, y),
        "ridge_score": ridge.score(X_scaled, y)
    }


def compute_vif(X):
    """
    Computes the Variance Inflation Factor (VIF) for each column in the DataFrame.

    VIF quantifies the extent of multicollinearity among predictor variables.
    A VIF > 10 is often considered problematic.

    Args:
        X (pd.DataFrame): DataFrame of predictors (numeric columns only).

    Returns:
        pd.Series: A series mapping each predictor to its VIF score.
                   Returns an empty Series if fewer than two predictors exist.
    """
    if X.empty or X.shape[1] < 2:
        log.log(
            TankLog.WARNING_LOGGING,
            "VIF skipped: not enough variables.",
            __file__,
            "compute_vif",
            42
        )
        return pd.Series(dtype=float)

    # Standardize the predictors
    X_scaled = StandardScaler().fit_transform(X)

    # Compute VIF for each predictor
    vif_values = [vif_calc(X_scaled, i) for i in range(X_scaled.shape[1])]

    return pd.Series(vif_values, index=X.columns)


def do_mining(df, target, exclusions=None):
    """
    Perform feature mining using transformations, subset selection, regularization,
    and VIF analysis to identify valuable predictors of the target.

    Steps:
    1. Run univariate regression with transformations to find strong predictors.
    2. Apply the best transformations to generate new variables.
    3. Perform exhaustive best-subset selection (k=3) on transformed variables.
    4. Apply LASSO and Ridge regression to assess variable importance.
    5. Calculate VIF for LASSO-selected predictors (optional residual analysis skipped).

    Args:
        df (pd.DataFrame): Input dataset.
        target (str): Name of the dependent variable (response).
        exclusions (list[str], optional): Columns to exclude from consideration.

    Returns:
        pd.DataFrame: Top univariate transformation models ranked by R².
    """
    log = TankLog.get_shared_logger()
    df = df.copy()

    # Step 1: Univariate mining with transformations
    top_transformations_df = transformed_univariate_mining(df, target, exclude=exclusions)

    if top_transformations_df.empty:
        log.log(TankLog.WARNING_LOGGING, "No valid univariate models were found.",
                __file__, "do_mining", 5)
        return pd.DataFrame()

    log.log(TankLog.INFO_LOGGING, "Top variable-transformation pairs:",
            __file__, "do_mining", 10)

    for _, row in top_transformations_df.head(10).iterrows():
        log.log(
            TankLog.INFO_LOGGING,
            f"{row['col']} ({row['transform']}): "
            f"R²={row['r2']:.4f}, "
            f"Coef={row['coef']:.4f}, "
            f"p={row['pval']:.4g}, "
            f"t={row['tvalue']:.2f}, "
            f"N={int(row['nobs'])}",
            __file__, "do_mining", 13
        )

    # Step 2: Apply best transformations
    log.log(TankLog.INFO_LOGGING, "[Step 2] Create transformed dataframe",
            __file__, "do_mining", 17)

    transformed_df, transformed_vars, transformation_map = apply_best_transformations(
        df,
        top_transformations_df.head(10)
    )

    for col in transformed_vars:
        original_var, transform = transformation_map[col]
        log.log(
            TankLog.INFO_LOGGING,
            f"{col} was created from '{original_var}' using '{transform}'",
            __file__, "do_mining", 23
        )

    if len(transformed_vars) < 3:
        log.log(TankLog.WARNING_LOGGING,
                "Not enough variables for exhaustive subset selection.",
                __file__, "do_mining", 26)
        return top_transformations_df

    # Step 3: Exhaustive best subset
    log.log(TankLog.INFO_LOGGING, "[Step 3] Exhaustive Best Subset",
            __file__, "do_mining", 29)

    r2, subset = exhaustive_best_subset(transformed_df, target, transformed_vars, k=3)

    log.log(
        TankLog.INFO_LOGGING,
        f"Best subset: {subset} R²={r2:.4f}",
        __file__, "do_mining", 31
    )

    # Step 4: LASSO and Ridge
    log.log(TankLog.INFO_LOGGING, "[Step 4] LASSO and Ridge",
            __file__, "do_mining", 34)

    reg_results = lasso_ridge_selection(transformed_df, target, transformed_vars)

    if not reg_results['lasso']:
        log.log(TankLog.WARNING_LOGGING,
                "LASSO selected no variables. Skipping VIF and residual plot.",
                __file__, "do_mining", 37)
        return top_transformations_df

    # Step 5: VIF
    log.log(TankLog.INFO_LOGGING, "[Step 5] VIF",
            __file__, "do_mining", 40)

    X = transformed_df[reg_results['lasso']].dropna()

    if X.empty:
        log.log(TankLog.WARNING_LOGGING,
                "VIF skipped: No complete cases after dropna().",
                __file__, "do_mining", 41)
    else:
        vif_series = compute_vif(X)
        log.log(TankLog.INFO_LOGGING, str(vif_series),
                __file__, "do_mining", 42)

    # Optional Step 6: Residual analysis (commented out)
    log.log(TankLog.INFO_LOGGING, "[Step 6] Residual Plot",
            __file__, "do_mining", 44)
    residual_plot(transformed_df, target, reg_results['lasso'])

    return top_transformations_df


def residual_plot(df, target, predictors, title_hint=""):
    """
    Generate and save a residual plot from a linear regression model.

    This diagnostic plot shows residuals versus fitted values for a linear model.
    Includes:
        - Seaborn residual plot with confidence band
        - Horizontal reference line at 0
        - R² displayed in the corner
        - Plot saved to disk via save_plot()

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        target (str): The dependent variable (string).
        predictors (list[str]): List of predictor (independent) variable names.
        title_hint (str): Optional suffix to help identify this plot file.

    Returns:
        None
    """
    # Drop missing values in predictors or target
    clean_df = df.dropna(subset=predictors + [target])

    # Fit linear regression model
    formula = f"{target} ~ {' + '.join(predictors)}"
    model = sm.OLS.from_formula(formula, data=clean_df).fit()

    # Compute residuals and fitted values
    residuals = model.resid
    fitted = model.fittedvalues
    r_squared = model.rsquared

    # Plot
    plt.figure(figsize=(10, 6))
    sns.residplot(x=fitted, y=residuals, lowess=True, line_kws={'color': 'red'}, scatter_kws={'alpha': 0.6})

    # Horizontal line at 0
    plt.axhline(0, color='black', linestyle='--', linewidth=1)

    # Labels and Title
    title = f"Residual Plot: {target} ~ {' + '.join(predictors)}"
    title = f"{title} ({title_hint})" if title_hint else title
    plt.title(title)
    plt.xlabel(f"Fitted Values of {target}")
    plt.ylabel("Residuals")
    plt.grid(True, linestyle='--', alpha=0.5)

    # Annotate R²
    plt.text(0.95, 0.05, f"$R^2$ = {r_squared:.3f}",
             transform=plt.gca().transAxes,
             fontsize=12, verticalalignment='bottom', horizontalalignment='right',
             bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.3'))

    plt.tight_layout()
    save_plot(plt, f"residual_plot_{target}_{title_hint}".strip("_"))
    plt.show()


def safe_transform(t_name, x):
    """
    Safely apply a named transformation to a numeric array.

    Applies transformations from the TRANSFORMATIONS dictionary while guarding against:
      - Negative values for 'log' and 'sqrt'
      - Division by zero for 'inverse'

    Args:
        t_name (str): The name of the transformation ('log', 'sqrt', 'square', 'identity', 'inverse')
        x (np.array or pd.Series): Input numeric data

    Returns:
        np.array or pd.Series: Transformed data
    """
    if t_name in ['log', 'sqrt']:
        x = np.clip(x, a_min=0, a_max=None)  # Prevent sqrt/log of negative numbers
    if t_name == 'inverse':
        x = np.clip(x, a_min=1e-6, a_max=None)  # Avoid division by zero

    return TRANSFORMATIONS[t_name](x)


def apply_best_transformations(df, transform_df):
    """
    Apply selected variable transformations to a DataFrame and record the mapping.

    This function takes a DataFrame of variable names and transformation types (e.g., 'log', 'sqrt'),
    then applies each transformation to the corresponding column in the input DataFrame.
    The resulting transformed columns are added to a copy of the input DataFrame.

    Args:
        df (pd.DataFrame): The original DataFrame containing the raw features.
        transform_df (pd.DataFrame): A DataFrame with at least two columns:
            - 'col': the name of the variable to transform
            - 'transform': the name of the transformation to apply

    Returns:
        tuple:
            - pd.DataFrame: A new DataFrame with transformed columns added
            - list of str: Names of the newly added columns
            - dict: Mapping of new column names to tuples of (original variable, transformation type)

    """
    df = df.copy()
    new_columns = []
    transformation_map = {}

    for _, row in transform_df.iterrows():
        var = row['col']
        transform = row['transform']
        new_col = f"{transform}_{var}"
        df[new_col] = safe_transform(transform, df[var])
        new_columns.append(new_col)
        transformation_map[new_col] = (var, transform)

    return df, new_columns, transformation_map


def do_mining_operations():
    """
    Perform exploratory data mining on NBA attendance and related features.

    This function serves as the high-level entry point for analyzing how various
    factors (team performance, lagged win percentages, and game-level statistics)
    relate to fan attendance. It executes multiple mining workflows by calling
    `do_mining()` on progressively more complex datasets:

    1. **Fan Attendance Revenue Data (2011–2019):**
       - Filters out COVID-affected seasons.
       - Excludes highly correlated attendance-related columns.
       - Mines predictors for `attendance_avg`.

    2. **Lagged Team Performance Data (2005–2024):**
       - Adds lagging performance indicators (home wins, win %).
       - Repeats mining for `attendance_avg`.

    3. **Game-Level Data (2005–2024):**
       - Computes rolling win percentages for home teams across various windows.
       - Mines predictors for single-game `attendance`.
       - Exports enriched dataset to CSV.

    Returns:
        None. Prints data mining summaries and saves the final dataset.

    Notes:
        - Uses `TankLog` for structured logging.
        - Relies on helper functions for lagging, data loading, and pretty printing.
        - Results printed include summary stats and ranked variable transformations.
    """
    # get the data for attendance without covid years (post 2019)
    df = load_fan_attendance_revenue()
    fan_attendance_revenue_filtered_for_covid_df = filter_seasons(df, min_year=2011,
                                                                  max_year=2019)
    target = "attendance_avg"
    # remove columns that are also attendance based.
    exclusions = ["avg_home_attendance", "total_attendance", 'away_attendance_total',
                  'avg_away_attendance', 'attendance_average', 'home_attendance_total']
    results_df = do_mining(fan_attendance_revenue_filtered_for_covid_df, target, exclusions)

    print(show_df_info(results_df, "Mining for Average Attendance"))
    print(pretty_print_df(results_df))

    # now mine our game data using attendance and lagging (1 year, 2 year, 4 year, and 6 year)
    attendance_df = load_fan_attendance()
    attendance_df_lagged = add_lagged_features(
        attendance_df,
        group_col="franchise_id",
        time_col="season_year",
        columns_to_lag=["home_wins", "total_wins", "Pct"],
        lags=[1, 2, 4, 6]
    )
    attendance_df_lagged = attendance_df_lagged[(attendance_df_lagged['season_year'] >= 2005) &
                                                (attendance_df_lagged['season_year'] <= 2024)].copy()
    # show results
    print(show_df_info(attendance_df_lagged, "Attendance With Lagging"))
    results_df = do_mining(attendance_df_lagged, target, exclusions)
    print(show_df_info(results_df, "Mining for Average Attendance"))
    print(pretty_print_df(results_df))

    # get games with franchise id column.
    games_df = load_extended_game_history()
    # The next fields are already present in extended_game_history()
    #
    # # create home and away flag to track records.
    # games_df['home_win_flag'] = (games_df['winner'] == games_df['hometeamId']).astype(int)
    # games_df['away_win_flag'] = (games_df['winner'] == games_df['awayteamId']).astype(int)
    # # rolling lag fields for wide ranges of games
    # for window in [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
    #     games_df[f'home_team_last{window}_win_pct'] = (
    #         games_df.groupby('home_team_franchise_id')
    #         .apply(lambda g: g['home_win_flag'].rolling(window=window, min_periods=1).mean())
    #         .reset_index(level=0, drop=True)
    #     )

    print(show_df_info(games_df, "Attendance depending on games recently played pct"))
    # all of these fields are not involved iin modeling.
    exclusions = [
        "gameId", "gameDate", "hometeamCity", "hometeamName", "hometeamId",
        "awayteamCity", "awayteamName", "awayteamId", "homeScore", "awayScore",
        "winner", "gameType", "arenaId", "gameLabel", "gameSubLabel",
        "seriesGameNumber", "season_year", "home_team_franchise_id",
        "away_team_franchise_id", "home_win_flag", "away_win_flag"
    ]
    # all games between 2005 and 2024.
    games_df = games_df[(games_df['season_year'] >= 2005) &
                        (games_df['season_year'] <= 2024)].copy()

    target = "attendance"
    results_df = do_mining(games_df, target, exclusions)
    print(show_df_info(results_df, "Mining for Average Attendance"))
    print(pretty_print_df(results_df))
    # save a copy
    # games_df.to_csv(FILE_PATH_TO_COMPILED_DATA + "extended_game_history.csv", index=False)
    # show dataframe metadata.
    print(show_df_info(games_df, "All NBA Games Played"))


# --- Example Usage ---
if __name__ == "__main__":
    do_mining_operations()








