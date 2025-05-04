import warnings

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from utils.utilities import pretty_print_df


def plot_feature_importance(model, model_name, feature_names):
    """
    Plot and optionally return/save feature importances from a fitted model.

    Args:
        model: Trained model with .feature_importances_ attribute (e.g., RandomForest).
        model_name: Name of model for title plot.
        feature_names (list): List of column names used in training.

    Returns:
        pd.DataFrame: DataFrame of features and importance scores.
    """
    # Get feature importances
    importances = model.feature_importances_

    # Create and sort DataFrame
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False)

    # Plot
    plt.figure(figsize=(8, 5))
    sns.heatmap(
        importance_df.set_index('Feature').T,
        cmap="YlGnBu",
        cbar_kws={'label': 'Importance Score'},
        linewidths=1,
        annot=True,
        fmt=".2f"
    )
    plt.title(f"Feature Importance Heatmap ({model_name})")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()
    return importance_df


def regression_visualisations(modeling_df, y_actual, y_pred):
    # visualizations

    plt.figure(figsize=(8,6))
    plt.scatter(y_actual, y_pred, alpha=0.5)
    plt.plot([y_actual.min(), y_actual.max()], [y_actual.min(), y_actual.max()], 'r--')  # perfect line
    plt.xlabel('Actual Revenue ($)')
    plt.ylabel('Predicted Revenue ($)')
    plt.title('Actual vs Predicted Revenue')
    plt.grid(True)
    plt.show()

    # --- 1. Prepare a 'performance' column ---

    def classify_performance(row):
        if row['revenue_adj'] >= 4 * row['budget_adj']:
            return 'massive_success'
        elif row['revenue_adj'] >= 2 * row['budget_adj']:
            return 'success'
        elif row['revenue_adj'] >= row['budget_adj']:
            return 'breakeven'
        else:
            return 'failure'

    modeling_df['performance'] = modeling_df.apply(classify_performance, axis=1)

    # --- 2. Extract release year ---
    modeling_df['release_year'] = pd.to_datetime(
        modeling_df['release_date'], errors='coerce'
    ).dt.year

    # Optional: filter out rows without a valid year
    modeling_df = modeling_df.dropna(subset=['release_year'])
    modeling_df['release_year'] = modeling_df['release_year'].astype(int)

    # --- 3. Group by year and performance ---

    performance_counts = modeling_df.groupby(['release_year', 'performance']).size().unstack(fill_value=0)

    # --- 4. Plotting ---

    plt.figure(figsize=(12, 8))

    # Plot each performance category
    if 'massive_success' in performance_counts.columns:
        plt.plot(performance_counts.index, performance_counts['massive_success'], label='Massive Success (≥4x)', color='green', linestyle='-')
    if 'success' in performance_counts.columns:
        plt.plot(performance_counts.index, performance_counts['success'], label='Success (2–4x)', color='lime', linestyle='--')
    if 'breakeven' in performance_counts.columns:
        plt.plot(performance_counts.index, performance_counts['breakeven'], label='Breakeven (1–2x)', color='blue', linestyle='-')
    if 'failure' in performance_counts.columns:
        plt.plot(performance_counts.index, performance_counts['failure'], label='Failure (<1x)', color='red', linestyle='-')

    plt.xlabel("Release Year")
    plt.ylabel("Number of Films")
    plt.title("Film Performance Over Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


    # --- 1. Calculate profit or loss per film ---
    # I actually already did this. # remove?
    modeling_df['profit'] = (
        modeling_df['revenue_adj'] - modeling_df['budget_adj']
    )

    # --- 2. Extract release year ---
    modeling_df['release_year'] = pd.to_datetime(
        modeling_df['release_date'], errors='coerce'
    ).dt.year

    # Remove rows with missing year
    modeling_df = modeling_df.dropna(subset=['release_year'])
    modeling_df['release_year'] = modeling_df['release_year'].astype(int)

    # --- 3. Group by year ---
    profit_by_year = modeling_df.groupby('release_year')['profit'].sum()

    # --- 4. Plotting ---
    plt.figure(figsize=(14, 8))
    bars = plt.bar(profit_by_year.index, profit_by_year.values, color=['green' if v >= 0 else 'red' for v in profit_by_year.values])

    plt.xlabel("Release Year")
    plt.ylabel("Total Profit (Adjusted $)")
    plt.title("Film Industry Profit or Loss by Year")
    plt.axhline(0, color='black', linewidth=0.8)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()


    plt.figure(figsize=(10, 8))
    plt.scatter(modeling_df['log_budget_adj'],
                modeling_df['log_revenue_adj'], alpha=0.4)
    plt.plot([10, 30], [10, 30], color='black', linestyle='--')  # Reference line where revenue = budget
    plt.xlabel("Log(Budget Adjusted)")
    plt.ylabel("Log(Revenue Adjusted)")
    plt.title("Log-Log Plot: Budget vs Revenue")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

    # histogram of profitability.
    plt.figure(figsize=(10, 6))
    plt.hist(modeling_df['profit'] / 1e6, bins=100, color='skyblue', edgecolor='black')  # in millions
    plt.xlabel("Profit (Million $ Adjusted)")
    plt.ylabel("Number of Films")
    plt.title("Distribution of Film Profits")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

    # histogram of revenue too budget ratio.
    plt.figure(figsize=(10, 6))
    plt.hist(modeling_df['rev_to_budget_ratio'],
             bins=np.linspace(0, 10, 50), color='gold', edgecolor='black')
    plt.xlabel("Revenue to Budget Ratio")
    plt.ylabel("Number of Films")
    plt.title("Revenue-to-Budget Ratio Distribution")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

    # moving average
    profit_by_year.rolling(window=5).mean().plot(figsize=(12, 6))
    plt.xlabel("Year")
    plt.ylabel("5-Year Moving Avg Profit")
    plt.title("Smoothed Film Industry Profit Trend")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

    # stacked success
    # Group and pivot
    performance_counts = modeling_df.groupby(['release_year', 'performance']).size().unstack(fill_value=0)

    # Normalize to proportions
    performance_props = performance_counts.div(performance_counts.sum(axis=1), axis=0)

    # --- Plot ---
    plt.figure(figsize=(14, 8))

    # Plot stacked area
    plt.stackplot(
        performance_props.index,
        performance_props['failure'],
        performance_props['breakeven'],
        performance_props['success'],
        performance_props['massive_success'],
        labels=['Failure (<1x)', 'Breakeven (1–2x)', 'Success (2–4x)', 'Massive Success (≥4x)'],
        colors=['red', 'blue', 'lime', 'green'],
        alpha=0.7
    )

    plt.xlabel("Release Year")
    plt.ylabel("Proportion of Films")
    plt.title("Stacked Success/Failure Rates Over Time")
    plt.legend(loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()


def graph_survival_confusion(conf_matrix):
    # Define true and predicted labels for each matrix
    true_labels = ['Actually Unprofitable', 'Actually Profitable']
    predicted_labels = ['Predicted Unprofitable', 'Predicted Profitable']

    # Create a figure to hold the subplots
    plt.figure(figsize=(24, 12))  # Adjust the overall size of the figure

    # Plot the first confusion matrix
    plt.subplot(1, 2, 1)  # 1 row, 2 columns, 1st subplot
    sns.heatmap(conf_matrix, annot=True, cmap='Reds', fmt='d',
                xticklabels=predicted_labels, yticklabels=true_labels,
                annot_kws={"size": 20})  # Adjust annotation text size
    plt.xlabel('Predicted', fontsize=18)
    plt.ylabel('Actual', fontsize=18)
    plt.title('Confusion Matrix for Profit Predictions', fontsize=20)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    # Display the plots
    plt.show()


def graph_survival_importance(importance_df):
    print(pretty_print_df(importance_df))

    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Plotting the feature importances for better visual interpretation
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df.head(10))
    plt.title('Feature Importances')
    plt.xlabel('Importance')
    plt.ylabel('Features')
    plt.show()

    warnings.filterwarnings("error", category=DeprecationWarning)


def show_pca_heatmap(pca_components, loadings_df, label_map=None):
    if pca_components > 0:
        plt.figure(figsize=(12, 6))

        # Optionally rename row labels
        if label_map:
            loadings_df = loadings_df.rename(index=label_map)

        sns.heatmap(loadings_df, annot=True, cmap='coolwarm')
        plt.title('PCA Component Loadings Heat Map')
        plt.tight_layout()
        plt.show()


def pie_chart_for_milestone():
    # Re-create the pie chart after environment reset
    labels = ['Budget (73%)', 'Release Year (8%)', 'Star Power + Content Tags (19%)']
    sizes = [73, 8, 19]
    explode = (0.1, 0, 0)

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.0f%%', explode=explode, shadow=True, startangle=140)
    plt.title('Feature Importance: Revenue Regression Model')
    plt.tight_layout()
    plt.show()
