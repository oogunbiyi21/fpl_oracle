import pandas as pd
import os
import requests
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score



def fetch_fixtures():
    url = 'https://fantasy.premierleague.com/api/fixtures/'
    response = requests.get(url)
    data = response.json()
    return data

def fetch_teams():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url)
    data = response.json()
    teams = {team['id']: team['name'] for team in data['teams']}
    return teams

def get_fixtures():
    fixtures = fetch_fixtures()
    fixtures_df = pd.DataFrame(fixtures)
    return fixtures_df

def get_teams(bootstrap_data):
    teams = {team['id']: team['name'] for team in bootstrap_data['teams']}
    teams_df = pd.DataFrame(list(teams.items()), columns=['team_id', 'team'])
    return teams_df

def get_available_players(bootstrap_data):
    
    players_df = pd.DataFrame(bootstrap_data['elements'])
    positions_df = pd.DataFrame(bootstrap_data['element_types'])

    players_df = players_df[['id', 'web_name', 'team', 'element_type', 'now_cost', 'total_points', 'minutes', 'points_per_game', 'value_season', 'status']]
    players_df['now_cost'] = players_df['now_cost'] / 10  # Convert cost to millions
    players_df['value_season'] = pd.to_numeric(players_df['value_season'], errors='coerce')
    available_players_df = players_df[players_df['status'] == 'a']
    available_players_df['roi'] = available_players_df['total_points'] / (available_players_df['now_cost'] / 10)
    
    position_mapping = positions_df.set_index('id')['singular_name_short'].to_dict()
    available_players_df['position'] = available_players_df['element_type'].map(position_mapping)

    available_players_df['points_per_game'] = pd.to_numeric(available_players_df['points_per_game'], errors='coerce')
    available_players_df = available_players_df.dropna(subset=['points_per_game'])

    return available_players_df

def get_team_difficulty(fixtures_df, teams_df):

    teams = fetch_teams()
    
    fixtures_df['team_h'] = fixtures_df['team_h'].map(teams)
    fixtures_df['team_a'] = fixtures_df['team_a'].map(teams)

    team_h_difficulty = fixtures_df.groupby('team_h')['team_h_difficulty'].mean().reset_index()
    team_a_difficulty = fixtures_df.groupby('team_a')['team_a_difficulty'].mean().reset_index()

    team_h_difficulty.columns = ['team', 'avg_home_difficulty']
    team_a_difficulty.columns = ['team', 'avg_away_difficulty']

    team_difficulty = pd.merge(team_h_difficulty, team_a_difficulty, on='team', how='outer')

    team_difficulty['avg_difficulty'] = team_difficulty[['avg_home_difficulty', 'avg_away_difficulty']].mean(axis=1)

    team_difficulty = team_difficulty.merge(teams_df, on="team")
    return team_difficulty


def get_cleaned_gw_all(bootstrap_data):
    
    
    fixtures_df = get_fixtures()
    teams_df = get_teams(bootstrap_data)

    team_difficulty = get_team_difficulty(fixtures_df, teams_df)

    team_difficulty_mapping = team_difficulty.set_index('team_id')['avg_difficulty'].to_dict()

    fixtures_df['opponent_team_difficulty'] = fixtures_df['team_a'].map(team_difficulty_mapping)

    player_data_with_difficulty = pd.read_csv('data/gw_all_with_difficulty.csv') # TODO: add logic to update this file

    # new_player_data_with_difficulty = pd.merge(new_player_data, team_difficulty, on='team', how='inner')
    # player_data_with_difficulty = pd.concat([player_data_with_difficulty, new_player_data_with_difficulty])

    player_data_with_difficulty['opponent_team_difficulty'] = player_data_with_difficulty['opponent_team'].map(team_difficulty_mapping)

    columns_to_drop = [
        'goals_scored', 'assists', 'clean_sheets', 
        'goals_conceded', 'own_goals', 'penalties_missed', 'penalties_saved', 
        'red_cards', 'saves', 'team_a_score', 'team_h_score', 
        'yellow_cards', 'round', 'kickoff_time', 'selected', 
        'transfers_in', 'transfers_out',
        'expected_assists', 'expected_goal_involvements', 'expected_goals',
        'expected_goals_conceded', 'creativity', 'influence', 'bonus',
        'bps', 'minutes', 'xP', 'element', 'fixture', 'threat'
    ]

    cleaned_gw_all = player_data_with_difficulty.drop(columns=columns_to_drop)

    cleaned_gw_all.to_csv('data/cleaned_gw_all.csv', index=False)
    return cleaned_gw_all


