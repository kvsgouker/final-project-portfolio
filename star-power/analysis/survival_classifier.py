"""
Project Name: Star Power
File: survival_classifier.py

Implements profitability prediction and regression models for films using PCA and ensemble learning.
Includes confusion matrix visualizations, feature importance plots, and pipeline for tuning.

Author: Kyle Salgado-Gouker

"""

import os.path
import time
import warnings

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from access.paths import DATA_DIRECTORY
from analysis.genres import found_genres
from analysis.plotting import graph_survival_confusion, graph_survival_importance, show_pca_heatmap
from processing.modeling import select_features
from processing.star_power import general_modeling_columns, content_modeling_cols
from utils.utilities import pretty_print_df, show_df_info


def fit_sample_and_reduce(sample_rate, df, target, n_components=3, genres=False, content=False):
    # Resetting index for consistency
    # Ensure df is a DataFrame and reset index
    if isinstance(df, pd.DataFrame):
        df = df.reset_index(drop=True)
    else:
        raise ValueError("df must be a pandas DataFrame")

    # Ensure target is a Series and reset index
    if isinstance(target, pd.Series):
        target = target.reset_index(drop=True)
    else:
        raise ValueError("target must be a pandas Series")

    # Define features
    column_names = select_features(main_labels = general_modeling_columns, genres=genres, content=content)

    features = df[column_names]

    print(f"fit sample at rate {sample_rate} & reduce to {n_components} using pca. Input features: {column_names}")

    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features)
    scaled_features_df = pd.DataFrame(scaled_features, columns=features.columns)

    # Sampling
    if sample_rate > 0:
        sampled_features_df = scaled_features_df.sample(frac=sample_rate, random_state=42)
    else:
        sampled_features_df = scaled_features_df

    # Ensuring target index matches the sampled features
    sampled_target = target.loc[sampled_features_df.index].reset_index(drop=True)
    sampled_features_df = sampled_features_df.reset_index(drop=True)

    if n_components > 0:
        # Applying PCA
        pca = PCA(n_components=n_components)
        reduced_features_sampled = pca.fit_transform(sampled_features_df)
        pca_columns = [f"PC{ i +1}" for i in range(n_components)]  # Dynamic column names based on number of components

        # Loadings are in pca.components_
        loadings_df = pd.DataFrame(pca.components_.T, columns=pca_columns, index=features.columns)

        reduced_features_sampled_df = pd.DataFrame(reduced_features_sampled, columns=pca_columns)
        return reduced_features_sampled_df, sampled_target, loadings_df, pca
    else:
        return sampled_features_df, sampled_target


def fit_data_for_testing(df, fitted_pca, n_components=3, genres=False, content=False):
    # Define features
    column_names = select_features(main_labels = general_modeling_columns, genres=genres, content=content)

    features = df[column_names]

    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features)

    if fitted_pca:
        # Applying PCA
        reduced_features = fitted_pca.fit_transform(scaled_features)
        pca_columns = [f"PC{ i +1}" for i in range(n_components)]  # Dynamic column names based on number of components
        reduced_features_sampled_df = pd.DataFrame(reduced_features, columns=pca_columns)
        return reduced_features_sampled_df
    else:
        scaled_features_df = pd.DataFrame(scaled_features, columns=features.columns)
        return scaled_features_df


def survival_test(df, target, pca_components = 5, genres=False, content=False):
    # Record the start time
    start_time = time.time()

    #  Many films are unprofitable.
    #  This imbalance can cause classifiers to "play it safe" and predict almost everything as unprofitable,
    #  which might boost accuracy — but not usefulness. class_weight = balanced!
    extra_trees = ExtraTreesClassifier(
        n_estimators=300,
        max_depth=30,
        min_samples_leaf=1,
        min_samples_split=10,
        max_features=None,
        class_weight='balanced', # penalize errors on profitable films more heavily
        random_state=42
    )

    if pca_components > 0:
        X, Y, loadings_df, pca = fit_sample_and_reduce(0, df, target, pca_components, genres=genres,content=content)
    else:
        X, Y = fit_sample_and_reduce(0, df, target, 0, genres=genres, content=content)
        loadings_df = None
        pca = None

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2,
                                                        random_state=42)

    # Training data in X_train and corresponding labels in y_train
    extra_trees.fit(X_train, Y_train)
    predictions = extra_trees.predict(X_test)

    # Record the end time
    end_time = time.time()

    # X_train is the training dataset
    num_rows, num_columns = X_train.shape

    print("Number of rows in X_train:", num_rows)
    print("Number of columns in X_train:", num_columns)

    # Calculate evaluation metrics
    extra_trees_accuracy = accuracy_score(Y_test, predictions)
    extra_trees_precision = precision_score(Y_test, predictions)
    extra_trees_recall = recall_score(Y_test, predictions)
    f1_score = 2 * (extra_trees_precision * extra_trees_recall ) /(extra_trees_recall
                                                                 + extra_trees_precision)

    # Calculate confusion matrix
    conf_matrix = confusion_matrix(Y_test, predictions)
    tn, fp, fn, tp = conf_matrix.ravel()
    # Calculate specificity
    specificity = tn / (tn + fp)

    print("Improved Extra Trees Classifier Accuracy:", extra_trees_accuracy)
    print("Improved Extra Trees Classifier Precision:", extra_trees_precision)
    print("Improved Extra Trees Classifier Recall:", extra_trees_recall)
    print("Improved Extra Trees Classifier F1 Score:", f1_score)
    print("Improved Extra Trees Classifier Specificity:", specificity)

    # Calculate the elapsed time
    elapsed_time = end_time - start_time

    feature_importances = extra_trees.feature_importances_
    features = X_train.columns

    # Create a DataFrame for easier visualization of feature importances
    importance_df = pd.DataFrame({
        'Feature': features,
        'Importance': feature_importances
    })
    importance_df = importance_df.sort_values(by='Importance', ascending=False)  # Sort by importance

    print("Elapsed time:", elapsed_time, "seconds")

    all_predictions = extra_trees.predict(X)

    return (extra_trees, conf_matrix, extra_trees_accuracy, extra_trees_precision, extra_trees_recall, specificity,
            importance_df, loadings_df, pca, X, Y, all_predictions)


def survival_run(df, pca_components, genres, content):
    print("Attempt to Predict Film Profitability\n")

    (fitted_classifier, conf_matrix, extra_trees_accuracy, extra_trees_precision, extra_trees_recall, specificity,
     importance_df, loadings_df, pca, X, Y, all_predictions) = \
            survival_test(df, df['is_profitable'], pca_components, genres, content)
    return  (
        fitted_classifier, conf_matrix, extra_trees_accuracy, extra_trees_precision, extra_trees_recall, specificity,
        importance_df, loadings_df, pca, X, Y, all_predictions)



def show_survival(df, pca_components=5, genres=False, content=False):

    (fitted_classifier, conf_matrix, extra_trees_accuracy, extra_trees_precision, extra_trees_recall, specificity,
            importance_df, loadings_df, pca, X, Y, all_predictions) = survival_run(df, pca_components, genres, content)

    graph_survival_confusion(conf_matrix)
    graph_survival_importance(importance_df)
    label_map = {
        'log_budget_adj': 'Log Budget',
        'sp_sum_previous_mean': 'Sum Star Power (Prev)',
        'log_sum_prev_revenue_mean': 'Log Sum Revenue (Prev)',
        'log_mean_prev_revenue_mean': 'Log Mean Revenue (Prev)',
        'log_mean_prev_budget_mean': 'Log Mean Budget (Prev)',
        'rev_to_budget_ratio': 'Rev/Budget Ratio',
        'rev_per_prev_sp': 'Revenue / Prev SP',
        'release_year': 'Year',
        'Sex - Report Count': 'Sex Reports',
        'Violence - Report Count': 'Violence Reports',
        'Profanity - Report Count': 'Profanity Reports',
        'Drugs - Report Count': 'Drug Reports',
        'Intense - Report Count': 'Intense Reports'
    }

    show_pca_heatmap(5, loadings_df, label_map)

    return (fitted_classifier, conf_matrix, extra_trees_accuracy, extra_trees_precision, extra_trees_recall, specificity,
            importance_df, loadings_df, pca, X, Y, all_predictions)


def survival_classifier_main():
    modeling_data_df = pd.read_csv(os.path.join(DATA_DIRECTORY, "data_to_model.csv"))
    if modeling_data_df.empty:
        print("Build modeling data before executing classifier.")
        return

    # remove Metropolis (bad record in DM)
    modeling_data_df = modeling_data_df[modeling_data_df['budget_adj']<1000000000]

    print(show_df_info(modeling_data_df, "Data to Model for Survival"))
    (fitted_classifier, conf_matrix, extra_trees_accuracy, extra_trees_precision, extra_trees_recall, specificity,
        importance_df, loadings_df, pca, X, Y, all_predictions) = (
            show_survival(modeling_data_df, 5,True, True))

    # - Y: true labels
    # - predictions: predicted labels

    # Reset index to align properly
    modeling_data_df = modeling_data_df.reset_index(drop=True)

    Y = Y.reset_index(drop=True)
    predictions = pd.Series(all_predictions).reset_index(drop=True)

    # Create conditions
    conditions = [
        (Y == 1) & (predictions == 1),
        (Y == 0) & (predictions == 0),
        (Y == 1) & (predictions == 0),
        (Y == 0) & (predictions == 1),
    ]

    choices = ['TP', 'TN', 'FN', 'FP']

    modeling_data_df['prediction_type'] = np.select(conditions, choices, default='UNKNOWN')

    modeling_data_df.to_csv(os.path.join(DATA_DIRECTORY, "augmented_data_to_model.csv"))

    modeling_data_df['profit'] = (
            modeling_data_df['revenue_adj'] - modeling_data_df['budget_adj'])
    top_financial_with_titles_df = modeling_data_df.sort_values(['profit'], ascending=False)

    missed_hits = modeling_data_df[modeling_data_df['prediction_type'] == 'FN']
    top_missed_hits = missed_hits.sort_values(by='profit', ascending=False).head(10)

    bad_greenlights = modeling_data_df[modeling_data_df['prediction_type'] == 'FP']
    top_bad_greenlights = bad_greenlights.sort_values(by='profit', ascending=True).head(10)

    top_missed_hits.to_csv("top_missed_hits.csv", index=False)
    top_bad_greenlights.to_csv("top_bad_greenlights.csv", index=False)

    interesting_columns = ['title', 'budget_adj', 'revenue_adj', 'profit', 'sp', 'sp_sum_previous_mean', 'release_date', 'imdb_id', 'tmdb_id']
    currency_columns = ['budget_adj', 'revenue_adj', 'profit']
    rounded_columns = ['sp', 'sp_sum_previous_mean']

    print("\nMissed Hits\n")
    print(pretty_print_df(top_missed_hits, rows=10, interesting_columns=interesting_columns,
                          headers='keys', currency_cols=currency_columns, rounded_cols=rounded_columns))

    print("\nBad Greenlights\n")
    print(pretty_print_df(top_bad_greenlights, rows=10, interesting_columns=interesting_columns,
                          headers='keys', currency_cols=currency_columns, rounded_cols=rounded_columns))


if __name__ == '__main__':
    survival_classifier_main()
