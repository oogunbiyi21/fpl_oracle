from flask import Flask, render_template, url_for
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os
from gw_total_points_model import get_model
from data_prep import *

warnings.filterwarnings('ignore')
sns.set()

app = Flask(__name__)

# data_path = os.path.join(app.root_path, 'data')

def get_fpl_bootstrap_data(endpoint):
    url = f'https://fantasy.premierleague.com/api/{endpoint}/'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

bootstrap_data = get_fpl_bootstrap_data('bootstrap-static')
fixtures_df = get_fixtures()
teams_df = get_teams(bootstrap_data)
available_players_df = get_available_players(bootstrap_data)
team_difficulty = get_team_difficulty(fixtures_df, teams_df)
cleaned_gw_data = get_cleaned_gw_all(bootstrap_data)



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/data-overview')
def data_overview():
    players_summary = available_players_df.describe().to_html()
    return render_template('data_overview.html', players_summary=players_summary)

@app.route('/model-prediction')
def model_prediction():
    feature_importances, evaluation, y_test, y_pred = get_model(bootstrap_data)

    plt.figure(figsize=(10, 8))
    sns.barplot(x='importance', y='feature', data=feature_importances)
    plt.title('Feature Importances')
    plot_path = os.path.join(app.root_path, 'static', 'plots', 'feature_importance.png')
    plt.savefig(plot_path)
    plt.close()

    # Generate the Actual vs Predicted Total Points plot
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_test, y=y_pred)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)  # Diagonal line
    plt.xlabel('Actual Total Points')
    plt.ylabel('Predicted Total Points')
    plt.title('Actual vs Predicted Total Points')
    plt.grid(True)
    actual_vs_pred_plot_path = os.path.join(app.root_path, 'static', 'plots', 'actual_vs_pred.png')
    plt.savefig(actual_vs_pred_plot_path)
    plt.close()

    return render_template(
        'model_prediction.html', 
        evaluation=evaluation, 
        feature_importance_plot=url_for('static', filename='plots/feature_importance.png'),
        actual_vs_predicted_plot=url_for('static', filename='plots/actual_vs_pred.png')
    )

@app.route('/eda')
def eda():
    plots = []

    # EDA Plot 1: Cost vs Total Points
    plt.figure(figsize=(10, 6))
    plt.scatter(available_players_df['now_cost'], available_players_df['total_points'])
    plt.xlabel('Player Cost (in millions)')
    plt.ylabel('Total Points')
    plt.title('Cost vs Total Points')
    plot_path_1 = os.path.join(app.root_path, 'static', 'plots', 'cost_vs_points.png')
    plt.savefig(plot_path_1)
    plt.close()
    plots.append('cost_vs_points.png')

    # EDA Plot 2: Distribution of Player Points by Position
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='position', y='total_points', data=available_players_df)
    plt.xlabel('Position')
    plt.ylabel('Total Points')
    plt.title('Distribution of Player Points by Position')
    plot_path_2 = os.path.join(app.root_path, 'static', 'plots', 'points_by_position.png')
    plt.savefig(plot_path_2)
    plt.close()
    plots.append('points_by_position.png')

    # EDA Plot 3: Average Points per Game by Position
    avg_points_per_game = available_players_df.groupby('position')['points_per_game'].mean().reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='position', y='points_per_game', data=avg_points_per_game)
    plt.xlabel('Position')
    plt.ylabel('Average Points per Game')
    plt.title('Average Points per Game by Position')
    plot_path_3 = os.path.join(app.root_path, 'static', 'plots', 'avg_points_per_game.png')
    plt.savefig(plot_path_3)
    plt.close()
    plots.append('avg_points_per_game.png')

    # EDA Plot 4: Top 20 Players by Total Points
    top_players = available_players_df.nlargest(20, 'total_points')
    plt.figure(figsize=(10, 6))
    sns.barplot(x='total_points', y='web_name', data=top_players)
    plt.xlabel('Total Points')
    plt.ylabel('Player')
    plt.title('Top 20 Players by Total Points')
    plot_path_4 = os.path.join(app.root_path, 'static', 'plots', 'top_players.png')
    plt.savefig(plot_path_4)
    plt.close()
    plots.append('top_players.png')

    # EDA Plot 5: ROI vs Points per Game
    plt.figure(figsize=(10, 6))
    plt.scatter(available_players_df['roi'], available_players_df['points_per_game'])
    plt.xlabel('ROI (Points per Million)')
    plt.ylabel('Points per Game')
    plt.title('ROI vs Points per Game')
    plot_path_5 = os.path.join(app.root_path, 'static', 'plots', 'roi_vs_points_per_game.png')
    plt.savefig(plot_path_5)
    plt.close()
    plots.append('roi_vs_points_per_game.png')

    # EDA Plot 6: Fixture Difficulty for Each Team
    plt.figure(figsize=(12, 8))
    sns.barplot(x='team', y='avg_difficulty', data=team_difficulty, palette='viridis')
    plt.xlabel('Average Fixture Difficulty')
    plt.ylim(2.5)
    plt.ylabel('Team')
    plt.xticks(rotation=45)
    plt.title('Average Fixture Difficulty for Each Team')
    plot_path_6 = os.path.join(app.root_path, 'static', 'plots', 'fixture_difficulty.png')
    plt.savefig(plot_path_6)
    plt.close()
    plots.append('fixture_difficulty.png')

    # EDA Plot 7: Fixture Difficulty for a Chosen Gameweek
    gameweek = 1  # Change this as needed
    gw_fixtures_df = fixtures_df[fixtures_df['event'] == gameweek]
    plt.figure(figsize=(14, 8))
    sns.barplot(x='team_h', y='team_h_difficulty', data=gw_fixtures_df, color='blue', label='Home Team Difficulty')
    sns.barplot(x='team_a', y='team_a_difficulty', data=gw_fixtures_df, color='red', label='Away Team Difficulty')
    plt.xlabel('Team')
    plt.ylabel('Difficulty')
    plt.title(f'Fixture Difficulty for Gameweek {gameweek}')
    plt.xticks(rotation=45)
    plt.legend()
    plot_path_7 = os.path.join(app.root_path, 'static', 'plots', 'fixture_difficulty_gw.png')
    plt.savefig(plot_path_7)
    plt.close()
    plots.append('fixture_difficulty_gw.png')

    # EDA Plot 8: Distribution of Total Points
    plt.figure(figsize=(10, 6))
    sns.histplot(cleaned_gw_data['total_points'], bins=20, kde=True)
    plt.xlabel('Total Points')
    plt.ylabel('Frequency')
    plt.title('Distribution of Total Points')
    plt.grid(True)
    plot_path_8 = os.path.join(app.root_path, 'static', 'plots', 'total_points_distribution.png')
    plt.savefig(plot_path_8)
    plt.close()
    plots.append('total_points_distribution.png')

    # EDA Plot 9: ICT Index Distribution by Position
    plt.figure(figsize=(12, 8))
    sns.boxplot(x='position', y='ict_index', data=cleaned_gw_data)
    plt.xlabel('Position')
    plt.ylabel('ICT Index')
    plt.title('ICT Index Distribution by Position')
    plt.grid(True)
    plot_path_9 = os.path.join(app.root_path, 'static', 'plots', 'ict_index_by_position.png')
    plt.savefig(plot_path_9)
    plt.close()
    plots.append('ict_index_by_position.png')

    # EDA Plot 10: Average Total Points by Team
    team_avg_points = cleaned_gw_data.groupby('team')['total_points'].mean().sort_values()
    plt.figure(figsize=(12, 8))
    sns.barplot(x=team_avg_points.index, y=team_avg_points.values, palette='viridis')
    plt.xlabel('Team')
    plt.ylabel('Average Total Points')
    plt.title('Average Total Points by Team')
    plt.xticks(rotation=45)
    plt.grid(True)
    plot_path_10 = os.path.join(app.root_path, 'static', 'plots', 'avg_points_by_team.png')
    plt.savefig(plot_path_10)
    plt.close()
    plots.append('avg_points_by_team.png')

    # EDA Plot 11: Correlation Heatmap
    plt.figure(figsize=(12, 8))
    print(cleaned_gw_data.columns)
    corr_matrix = cleaned_gw_data[['total_points', 'ict_index', 'transfers_balance', 'value',
                              'avg_home_difficulty', 'avg_away_difficulty', 'avg_difficulty',
                              'opponent_team_difficulty']].corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f')
    plt.title('Correlation Heatmap')
    plot_path_11 = os.path.join(app.root_path, 'static', 'plots', 'correlation_heatmap.png')
    plt.savefig(plot_path_11)
    plt.close()
    plots.append('correlation_heatmap.png')

    return render_template('eda.html', plots=plots)

if __name__ == '__main__':
    app.run(debug=True)
