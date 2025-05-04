"""
Project Name: Star Power
File: modeling.py

All regressors and correlation for star power.

Author: Kyle Salgado-Gouker
"""

import multiprocessing
import os
import threading
import time

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# MUST USE scipy.stats rand!
from scipy.stats import randint

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from xgboost import XGBRegressor
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor

# torch_regression.py
import torch
import torch.nn as nn
import torch.optim as optim

from access.paths import DATA_DIRECTORY
from analysis.genres import found_genres
from analysis.plotting import plot_feature_importance
from config.settings import content_modeling_cols, DO_GRID_SEARCH, USE_RANDOMIZED_GRID, general_modeling_columns
from utils.utilities import pretty_print_df


def run_models(grouped):

    # sp model
    X_sp, y_sp = grouped[['sp_sum_previous', 'log_budget_adj']], grouped['sp']
    X_train_sp, X_test_sp, y_train_sp, y_test_sp = train_test_split(X_sp, y_sp, test_size=0.2, random_state=42)
    r2_sp = r2_score(y_test_sp, LinearRegression().fit(X_train_sp, y_train_sp).predict(X_test_sp))

    # Revenue model
    X_rev, y_rev = grouped[['sp_sum_previous', 'log_budget_adj']], grouped['revenue_adj']
    X_train_rev, X_test_rev, y_train_rev, y_test_rev = (
        train_test_split(X_rev, y_rev, test_size=0.2, random_state=42))
    r2_rev = r2_score(y_test_rev, LinearRegression().fit(X_train_rev, y_train_rev).predict(X_test_rev))

    return r2_sp, r2_rev

# Define the model
class ImprovedRegressor(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    def forward(self, x):
        return self.net(x)

# Training function
def train_torch_model(X, y, epochs=500, lr=1e-3):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32)

    model = ImprovedRegressor(X_train.shape[1])
    loss_fn = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        pred = model(X_train)
        loss = loss_fn(pred, y_train)
        loss.backward()
        optimizer.step()

        if epoch % 50 == 0:
            model.eval()
            with torch.no_grad():
                val_pred = model(X_test)
                val_loss = loss_fn(val_pred, y_test)
            print(f"[Epoch {epoch}] Train Loss: {loss.item():.4f} | Val Loss: {val_loss.item():.4f}")

    return model, scaler


def select_features(main_labels, content = False, genres = False):
    selected_features = main_labels.copy()
    content_labels = content_modeling_cols
    if content:
        selected_features.extend(content_labels)
    if genres:
        selected_features.extend(found_genres)
    return selected_features


def evaluate_model(name, y_true_log, y_pred_log, debug_examples=5):
    # guarantee they are flat.
    y_pred = np.expm1(np.asarray(y_pred_log).ravel())
    y_true = np.expm1(np.asarray(y_true_log).ravel())
    # reshape for metrics calls.
    y_pred = np.array(y_pred).reshape(-1)
    y_true = np.array(y_true).reshape(-1)

    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)

    print(f"\n=== {name} Results ===")
    print(f"R²:   {r2:.4f}")
    print(f"RMSE: ${rmse:,.2f}")
    print(f"MAE:  ${mae:,.2f}")

    print(f"\nSample Predictions:")
    for i in range(min(debug_examples, len(y_true))):
        print(f"  Actual: ${y_true[i]:,.2f} | Predicted: ${y_pred[i]:,.2f}")

    return r2, rmse, mae


def starpower_correlation(df, title, first_column, second_column):
    # Model sp_sum_previous to sp current film!
    # Now re-merge on tmdb_id after summing per film
    # Use film_grouped_df directly
    print(f"\nResults for {title}:\n")

    correlation = df[[first_column, second_column]].corr().iloc[0, 1]
    print(f"The correlation is {correlation}.")

    # 1. Descriptive statistics
    summary_stats = df[[first_column, second_column]].describe()

    # 2. Correlation and covariance
    correlation_matrix = df[[first_column, second_column]].corr()
    covariance_matrix = df[[first_column, second_column]].cov()

    # 3. Skewness and kurtosis
    skewness = df[[first_column, second_column]].skew()
    kurtosis = df[[first_column, second_column]].kurt()

    # 4. Edge diagnostics
    extremes = {
        first_column: {
            'min': df[first_column].min(),
            'max': df[first_column].max(),
            '5th percentile': np.percentile(df[first_column], 5),
            '95th percentile': np.percentile(df[first_column], 95),
        },
        second_column: {
            'min': df[second_column].min(),
            'max': df[second_column].max(),
            '5th percentile': np.percentile(df[second_column], 5),
            '95th percentile': np.percentile(df[second_column], 95),
        }
    }

    # 5. Visualize Results

    plt.figure(figsize=(8, 6))
    plt.scatter(df[first_column], df[second_column], alpha=0.5)
    plt.xlabel(first_column)
    plt.ylabel(second_column)
    plt.title(f"Scatter Plot of {first_column} vs. {second_column}")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 6. Print or return results
    print("=== Summary Statistics ===")
    print(summary_stats)
    print("\n=== Correlation Matrix ===")
    print(correlation_matrix)
    print("\n=== Covariance Matrix ===")
    print(covariance_matrix)
    print("\n=== Skewness ===")
    print(skewness)
    print("\n=== Kurtosis ===")
    print(kurtosis)
    print("\n=== Edge Distribution Summary ===")
    print(pd.DataFrame(extremes))

    return correlation


def model_regressions(modeling_df, modeling_columns, target='log_revenue_adj'):

    X = modeling_df[modeling_columns].values
    y = modeling_df[target].values.reshape(-1, 1)

    # # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest (limit depth)
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,  # important to prevent overfitting
        random_state=42
    )
    rf_model.fit(X_train_scaled, y_train.ravel())

    # Predict and evaluate
    y_pred_log_test = rf_model.predict(X_test_scaled)
    y_pred_test = np.expm1(y_pred_log_test)
    y_test_true = np.expm1(np.asarray(y_test, dtype=float).ravel())

    r2 = r2_score(y_test_true, y_pred_test)
    rmse = np.sqrt(mean_squared_error(y_test_true, y_pred_test))
    mae = mean_absolute_error(y_test_true, y_pred_test)

    print("=== Results for RFR ===\n")
    print(f"R²:   {r2:.4f}")
    print(f"RMSE: ${rmse:,.2f}")
    print(f"MAE:  ${mae:,.2f}")

    print(f"\nSample Predictions:")
    for actual, pred in zip(y_test_true[:5], y_pred_test[:5]):
        print(f"  Actual: ${actual.item():,.2f} | Predicted: ${pred.item():,.2f}")

    feature_importances_df = plot_feature_importance(rf_model, 'Simple RFR - 100 Estimators, Max Depth = 5', modeling_columns)

    # === PyTorch Evaluation ===
    # model, scaler = train_torch_model(X, y)
    # X_scaled = scaler.transform(X)
    # X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
    # with torch.no_grad():
    #     y_log_pred = model(X_tensor).numpy()
    #
    # evaluate_model("PyTorch Neural Net", y_raw, y_log_pred)

    # === XGBoost Evaluation ===
    xgb_model = XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=4,  #  regularization
        subsample=0.8,  # random sampling
        colsample_bytree=0.8,  # add feature sampling
        random_state=42
    )
    xgb_model.fit(X_train, y_train.ravel())
    y_log_pred_xgb = xgb_model.predict(X_test).reshape(-1, 1)

    evaluate_model("XGBoost", y_test, y_log_pred_xgb)
    xgb_feature_importances_df = plot_feature_importance(xgb_model, "XGB Regressor, 500 Estimators, Max Depth = 4", modeling_columns)

    print("\nXGB Feature Importance - 500 Estimators, Max Depth = 4\n")
    print(pretty_print_df(xgb_feature_importances_df))

    xgb_model = XGBRegressor(
        n_estimators=600,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.7,
        colsample_bytree=1.0,
        gamma=2.5,
        reg_alpha=0.5,
        reg_lambda=1.5,
        random_state=42
    )

    xgb_model.fit(X_train, y_train.ravel())
    y_log_pred_xgb = xgb_model.predict(X_test).reshape(-1, 1)

    evaluate_model("XGBoost", y_test, y_log_pred_xgb)
    xgb_feature_importances_df = plot_feature_importance(xgb_model, "XGB Regressor, 600 Estimators, Max Depth = 5", modeling_columns)

    print("\nXGB Feature Importance - 600 Estimators, Max Depth = 5\n")
    print(pretty_print_df(xgb_feature_importances_df))

    xgb_model = XGBRegressor(
        n_estimators=1000,
        learning_rate=0.02,
        max_depth=7,
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=2.0,
        reg_alpha=0.5,
        reg_lambda=1.5,
        random_state=42
    )
    xgb_model.fit(X_train, y_train.ravel())
    y_log_pred_xgb = xgb_model.predict(X_test).reshape(-1, 1)

    evaluate_model("XGBoost", y_test, y_log_pred_xgb)
    xgb_feature_importances_df = plot_feature_importance(xgb_model, "XGB Regressor, 1000 Estimators, Max Depth = 7", modeling_columns)

    print("\nXGB Feature Importance - 1000 Estimators, Max Depth = 7\n")
    print(pretty_print_df(xgb_feature_importances_df))

    # === Ridge Regression Evaluation ===
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    ridge_model = RidgeCV(alphas=[0.1, 1.0, 10.0])
    ridge_model.fit(X_train_scaled, y_train)

    y_log_pred_ridge = ridge_model.predict(X_test_scaled).reshape(-1, 1)

    evaluate_model("Ridge Regression", y_test, y_log_pred_ridge)

    # === Random Forest Evaluation ===
    best_rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features='sqrt',
        bootstrap=True,
        random_state=42
    )
    best_rf.fit(X_train_scaled, y_train.ravel())
    y_log_pred_best_rf = best_rf.predict(X_test_scaled).reshape(-1, 1)

    evaluate_model("Random Forest", y_test, y_log_pred_best_rf)


    if DO_GRID_SEARCH:
        if USE_RANDOMIZED_GRID:
            y_actual, y_pred = randomized_rf_regression(modeling_df)
        else:
            y_actual, y_pred = do_grid_search_regression(modeling_df)
    else:
        # Invert log1p transformation
        y_pred = np.expm1(y_log_pred_best_rf).flatten()
        y_test = np.asarray(y_test, dtype=float).ravel()
        y_actual = np.expm1(y_test).flatten()

    return feature_importances_df, y_actual, y_pred


def do_grid_search_regression(modeling_df):

    print("\nSampling Data for Grid Search.")

    # Prepare data
    # STEP 1: Sample and split BEFORE fitting anything
    sample_df = modeling_df.sample(frac=0.1, random_state=42)

    # sample_df = modeling_df.copy()
    X_full = modeling_df[general_modeling_columns].values
    y_full = modeling_df['log_revenue_adj'].values.reshape(-1, 1)

    X = sample_df[general_modeling_columns].values
    y = sample_df['log_revenue_adj'].values.reshape(-1, 1)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Optimize by forcing np_array.
    X_train = np.array(X_train).astype(np.float64)
    y_train = np.array(y_train).astype(np.float64).ravel()

    # check nans (there should be no NaNs here)
    print(np.any(np.isnan(X_train)))
    print(np.any(np.isnan(y_train)))

    print("\n\n===Grid Search Results ===")

    # # Set grid parameters
    # param_grid = {
    #     'n_estimators': [100, 250],
    #     'max_depth': [5, 10, 20, 40],
    #     'min_samples_split': [2, 5],
    #     'min_samples_leaf': [1, 2],
    #     'max_features': ['sqrt', 'log2'],
    #     'bootstrap': [True]
    # }

    param_grid = {
        'n_estimators': [100],
        'max_depth': [10, 20],
        'min_samples_split': [2],
        'min_samples_leaf': [1],
        'max_features': ['sqrt']
    }

    # param_grid = {
    #     'n_estimators': [100, 250],
    #     'max_depth': [10, 40],
    #     'min_samples_split': [2, 5],
    #     'min_samples_leaf': [1, 2],
    #     'max_features': ['sqrt']
    # }

    # Initialize model and grid search
    rf = RandomForestRegressor(random_state=42)
    n_jobs = os.cpu_count()-1

    # Debug this slow machine.
    print(f"Threads: {threading.active_count()}")
    print(f"CPUs: {multiprocessing.cpu_count()}")

    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=2,
        scoring='r2',
        verbose=3,
        n_jobs=n_jobs
    )

    # Train model
    grid_search.fit(X_train, y_train.ravel())

    # Evaluate best model
    best_rf = grid_search.best_estimator_
    results_df = pd.DataFrame(grid_search.cv_results_)
    results_df.sort_values('mean_test_score', ascending=False).head(10)
    print("\nRFR Best Result from Grid")
    print(pretty_print_df(results_df, rows=10))

    y_pred_log = best_rf.predict(X)

    # Invert log1p transformation
    y_pred = np.expm1(y_pred_log).flatten()
    y_actual = np.expm1(y).flatten()

    # Compute metrics
    r2 = r2_score(y_actual, y_pred)
    rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
    mae = mean_absolute_error(y_actual, y_pred)

    print("\nBest Parameters:", grid_search.best_params_)
    print(f"R²:   {r2:.4f}")
    print(f"RMSE: ${rmse:,.2f}")
    print(f"MAE:  ${mae:,.2f}")

    print("\nSample Predictions:")
    for actual, pred in zip(y_actual[:5], y_pred[:5]):
        print(f"  Actual: ${actual:,.2f} | Predicted: ${pred:,.2f}")

    # See full leaderboard.
    results_df = pd.DataFrame(grid_search.cv_results_)
    results_df = results_df.sort_values(by="mean_test_score", ascending=False)
    pd.set_option("display.max_columns", None)  # Show all columns

    print(results_df[[
        "mean_test_score", "std_test_score",
        "param_n_estimators", "param_max_depth",
        "param_max_features", "param_min_samples_leaf",
        "param_min_samples_split"
    ]].head(10))

    # Re-train best estimator on full dataset
    X = X_full
    y = y_full

    y_log_pred = best_rf.predict(X).reshape(-1, 1)

    evaluate_model("GridSearch Best RF on Full Data", y, y_log_pred)
    y_pred = np.expm1(y_log_pred).flatten()
    y_actual = np.expm1(y).flatten()

    return y_actual, y_pred


def randomized_rf_regression(modeling_df):
    print("\nSampling Data for Randomized Search...")

    sample_df = modeling_df.sample(frac=0.1, random_state=42)
    X_full = modeling_df[general_modeling_columns].values
    y_full = modeling_df['log_revenue_adj'].values.reshape(-1, 1)

    X = sample_df[general_modeling_columns].values
    y = sample_df['log_revenue_adj'].values.reshape(-1, 1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    X_train = np.asarray(X_train, dtype=np.float64)
    y_train = np.asarray(y_train, dtype=np.float64).ravel()

    print("NaNs in X_train:", np.any(np.isnan(X_train)))
    print("NaNs in y_train:", np.any(np.isnan(y_train)))

    # param_dist = {
    #     'n_estimators': randint(100, 300),
    #     'max_depth': randint(5, 30),
    #     'min_samples_split': randint(2, 10),
    #     'min_samples_leaf': randint(1, 5),
    #     'max_features': ['sqrt', 'log2']
    # }

    param_dist = {
        'n_estimators': randint(25, 100),
        'max_depth': randint(5, 15),
        'min_samples_split': randint(2, 6),
        'min_samples_leaf': randint(1, 3),
        'max_features': ['sqrt', 'log2']
    }

    rf = RandomForestRegressor(random_state=42)
    random_search = RandomizedSearchCV(
        estimator=rf,
        param_distributions=param_dist,
        n_iter=20,
        cv=2,
        scoring='r2',
        verbose=3,
        n_jobs=os.cpu_count() - 1,
        random_state=42
    )

    print("Fitting RandomizedSearchCV...")
    start = time.time()
    random_search.fit(X_train, y_train)
    duration = time.time() - start

    print(f"Completed in {duration:.2f}s")
    print("Best Parameters:", random_search.best_params_)

    # Predict on X_test instead of X
    y_log_pred_test = random_search.predict(X_test)
    evaluate_model("Randomized RF (Test Set)", y_test, y_log_pred_test)

    y_pred = np.expm1(y_log_pred_test).flatten()
    y_actual = np.expm1(y_test).flatten()

    return y_actual, y_pred

def regressor_pipeline(df):

    y = df[['popularity', 'log_revenue']]

    selected_features = select_features(general_modeling_columns, content=True, genres=True)
    print("\nSelected Features: ", selected_features)

    X = df[selected_features]

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Build the pipeline directly with the RandomForestRegressor
    pipeline = Pipeline(steps=[
        ('random_forest_regressor', RandomForestRegressor(random_state=42))
    ])

    # Fit the model for 'popularity'
    pipeline.fit(X_train, y_train['popularity'])

    # Predict and evaluate for 'popularity'
    y_pred_popularity = pipeline.predict(X_test)
    mse_popularity = mean_squared_error(y_test['popularity'], y_pred_popularity)
    rmse_popularity = mse_popularity ** 0.5
    r2_popularity = r2_score(y_test['popularity'], y_pred_popularity)
    mae_popularity = mean_absolute_error(y_test['popularity'], y_pred_popularity)
    # calculate residuals
    residuals_popularity = y_test['popularity'] - y_pred_popularity

    print(f'\nRMSE for popularity: {rmse_popularity}')

    # Fit the model for 'log_revenue'
    pipeline.fit(X_train, y_train['log_revenue'])

    # Predict and evaluate for 'log_revenue'
    y_pred_log_revenue = pipeline.predict(X_test)
    mse_log_revenue = mean_squared_error(y_test['log_revenue'], y_pred_log_revenue)
    rmse_log_revenue = mse_log_revenue ** 0.5
    r2_log_revenue = r2_score(y_test['log_revenue'], y_pred_log_revenue)
    mae_log_revenue = mean_absolute_error(y_test['log_revenue'], y_pred_log_revenue)
    # calculate residuals
    residuals_log_revenue = y_test['log_revenue'] - y_pred_log_revenue

    print(f'RMSE for log_revenue: {rmse_log_revenue}')

    print("\nResults of Random Forest Regressor")
    print("\n\tDomain: Films with financial info")
    print(f'RMSE for log_revenue: {rmse_log_revenue}')
    print(f'R2 for log_revenue: {r2_log_revenue}')
    print(f'MAE for log_revenue: {mae_log_revenue}')

    print(f'\nRMSE for popularity: {rmse_popularity}')
    print(f'R2 for popularity: {r2_popularity}')
    print(f'MAE for popularity: {mae_popularity}')

    # save this data to measure hyperparameters later.
    df.to_csv(os.path.join(DATA_DIRECTORY, "films_for_hyperparameter_tuning.csv"), index=False)

    feature_importances = pipeline.named_steps['random_forest_regressor'].feature_importances_
    features = X.columns

    # Create a DataFrame for easier visualization
    importance_df = pd.DataFrame({
        'Feature': features,
        'Importance': feature_importances
    })
    importance_df = importance_df.sort_values(by='Importance', ascending=False)  # Sort by importance

    pretty_print_df(importance_df)

    top_features_df = importance_df.head(12)
    # Extract feature names and importances
    features = top_features_df['Feature']
    importances = top_features_df['Importance']

    # Plot feature importances
    plt.figure(figsize=(10, 6))
    plt.barh(features, importances, color='skyblue')
    plt.xlabel('Importance', fontsize=15)
    plt.ylabel('Feature', fontsize=15)
    plt.title('Feature Importance')
    plt.gca().invert_yaxis()  # Invert y-axis to have the most important feature on top
    plt.show()


def do_all_starpower_correlation_transformations(top_with_titles_df, top_financial_with_titles_df):
    highest_correlation_all_films = 0
    title_all_films = ""
    highest_correlation_all_financials = 0
    title_all_financials = ""
    all_correlation_results = []
    all_financial_correlation_results = []

    for first_column in ['sp_sum_previous', 'sp_sum_previous_squared', 'log_sp_sum_previous',
                         'inv_sp_sum_previous', 'sqrt_sp_sum_previous']:
        for second_column in ['sp_squared', 'sp', 'log_sp']:
            title = f"All Films Voted - using {first_column} vs {second_column}"
            correlation_test = starpower_correlation(top_with_titles_df, title,
                        first_column, second_column)
            all_correlation_results.append([first_column, second_column, correlation_test])
            if correlation_test > highest_correlation_all_films:
                highest_correlation_all_films = correlation_test
                title_all_films = title
            title = f"All Films Voted with Revenue & Budget - using {first_column} vs {second_column}"
            correlation_test = starpower_correlation(top_financial_with_titles_df,title,
                                first_column, second_column)
            all_financial_correlation_results.append([first_column, second_column, correlation_test])

            if correlation_test > highest_correlation_all_financials:
                highest_correlation_all_financials = correlation_test
                title_all_financials = title

    # Convert correlation results to DataFrames
    all_correlation_results_df = pd.DataFrame(
        all_correlation_results,
        columns=["First Variable", "Second Variable", "Correlation"]
    ).sort_values(by="Correlation", ascending=False)

    all_financial_correlation_results_df = pd.DataFrame(
        all_financial_correlation_results,
        columns=["First Variable", "Second Variable", "Correlation"]
    ).sort_values(by="Correlation", ascending=False)

    print("\nTop Correlations - All Films Voted:")
    print(pretty_print_df(all_correlation_results_df))

    print("\nTop Correlations - Films with Revenue & Budget:")
    print(pretty_print_df(all_financial_correlation_results_df))

    print(f"Best correlation: {title_all_films}: {highest_correlation_all_films}")
    print(f"Best correlation of financials: {title_all_financials}: {highest_correlation_all_financials}")

