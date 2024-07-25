import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from data_prep import get_cleaned_gw_all

def get_model(bootstrap_data):

    cleaned_gw_all = get_cleaned_gw_all(bootstrap_data)
    numerical_cols = cleaned_gw_all.select_dtypes(include=['float64', 'int64']).columns
    categorical_cols = cleaned_gw_all.select_dtypes(include=['object']).columns

    label_encoders = {}
    for column in ['position', 'team']:
        le = LabelEncoder()
        cleaned_gw_all[column] = le.fit_transform(cleaned_gw_all[column])
        label_encoders[column] = le

    numerical_imputer = SimpleImputer(strategy='mean')  # or 'median', 'most_frequent'
    cleaned_gw_all[numerical_cols] = numerical_imputer.fit_transform(cleaned_gw_all[numerical_cols])

    categorical_imputer = SimpleImputer(strategy='most_frequent')
    cleaned_gw_all[categorical_cols] = categorical_imputer.fit_transform(cleaned_gw_all[categorical_cols])

    X = cleaned_gw_all.drop(['name', 'total_points'], axis=1)
    y = cleaned_gw_all['total_points']  
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    importances = model.feature_importances_
    feature_names = X.columns
    feature_importances = pd.DataFrame({'feature': feature_names, 'importance': importances})
    feature_importances = feature_importances.sort_values(by='importance', ascending=False)


    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    evaluation = f"MSE: {mse}, R2 Score: {r2}"

    return feature_importances, evaluation, y_test, y_pred

if __name__ == '__main__':
    feature_importances, evaluation = get_model()
    print(evaluation)