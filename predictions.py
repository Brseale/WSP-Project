from bs4 import BeautifulSoup
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import numpy as np

# 1. Parse XML Data into DataFrame
def parse_xml(xml_file):
    with open(xml_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'lxml-xml')
        shows = []

        # Extract show details
        for show in soup.find_all('show'):
            date = show.find('date').get_text()
            location = show.find('location').get_text().strip()
            setlist = [song.get_text().strip() for song in show.find_all('song')]
            shows.append({
                'date': date,
                'location': location,
                'setlist': setlist,
                'num_songs': len(setlist)
            })

    return pd.DataFrame(shows)

# Function to retrieve the songs from the last three shows
def get_recent_songs(df):
    df['date'] = pd.to_datetime(df['date'])
    sorted_df = df.sort_values(by='date', ascending=False)
    recent_shows = sorted_df.head(3)
    recent_songs = [song for setlist in recent_shows['setlist'] for song in setlist]
    return list(set(recent_songs))

# Function to add a feature for whether the song was played recently
def add_recently_played_feature(df, recent_songs):
    df['recently_played'] = df['song'].apply(lambda song: 1 if song in recent_songs else 0)
    return df

# Prepare data for training
def prepare_data(df):
    data = []
    for _, row in df.iterrows():
        for song in row['setlist']:
            data.append({
                'date': row['date'],
                'location': row['location'].strip(),
                'song': song
            })
    prepared_df = pd.DataFrame(data)
    prepared_df['date'] = pd.to_datetime(prepared_df['date'])
    return prepared_df

# Load data
xml_file = 'xml_files/allshows_setlistfm.xml'
df_original = parse_xml(xml_file)

# Prepare a flat format of the data for training
df = prepare_data(df_original)

# Encode categorical features and target
location_encoder = LabelEncoder()
song_encoder = LabelEncoder()

# Fit location encoder on all locations from the original DataFrame
location_encoder.fit(df_original['location'].str.strip())  # Encode all locations
df['location_encoded'] = location_encoder.transform(df['location'].str.strip())
df['song_encoded'] = song_encoder.fit_transform(df['song'])

# Get recent songs from the last 3 shows using the original DataFrame
recent_songs = get_recent_songs(df_original)

# Add 'recently_played' feature
df = add_recently_played_feature(df, recent_songs)

# Split data for training
X = df[['date', 'location_encoded', 'recently_played']].copy()  # Avoid SettingWithCopyWarning
y = df['song_encoded']

# Convert 'date' to integer format using ordinals to avoid FutureWarning
X['date'] = X['date'].apply(lambda x: x.toordinal())

# Split into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict the next setlist
def predict_next_setlist(model, date, location, recent_songs, num_songs=20):
    location = location.strip()  # Ensure no extraneous whitespace
    # Check if location is in the LabelEncoder's classes
    if location not in location_encoder.classes_:
        print(f"Warning: Location '{location}' not found in training data.")
        location_encoded = -1  # Placeholder for unknown location
    else:
        location_encoded = location_encoder.transform([location])[0]
    
    # Prepare the 'recently_played' feature based on recent songs
    recently_played_values = [1 if song in recent_songs else 0 for song in song_encoder.classes_]
    recently_played = recently_played_values[:num_songs]
    
    # Ensure all columns have length equal to num_songs
    prediction_data = pd.DataFrame({
        'date': [date.toordinal()] * num_songs,
        'location_encoded': [location_encoded] * num_songs,
        'recently_played': recently_played
    })
    
    # Predict song probabilities and get top N predictions
    song_probabilities = model.predict_proba(prediction_data)
    top_songs_indices = song_probabilities.mean(axis=0).argsort()[-num_songs:][::-1]
    predicted_songs = song_encoder.inverse_transform(top_songs_indices)
    
    # Format the output list
    return [song.strip() for song in predicted_songs]

# Usage example
date = datetime.strptime("2025-02-14", "%Y-%m-%d")
location = "Township Auditorium, Columbia, SC, USA"
predicted_songs = predict_next_setlist(model, date, location, recent_songs)

print("Predicted Setlist:", predicted_songs)
