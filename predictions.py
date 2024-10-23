import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from collections import Counter
from bs4 import BeautifulSoup
import numpy as np

# Load all data from the xml file
def load_xml_data(xml_file):
    with open(xml_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'lxml-xml')

        shows = []

        # Get show details
        for show in soup.find_all('show'):
            date = show.find('date').get_text()
            location = show.find('location').get_text()
            setlist = [song.get_text().strip() for song in show.find_all('song')]  # Clean song titles
            shows.append({
                'date': date,
                'location': location,
                'setlist': setlist
            })

    return pd.DataFrame(shows)

# Preprocess data for machine learning
def preprocess_data(df):
    df['date'] = pd.to_datetime(df['date'])
    df['days_since_last_show'] = df['date'].diff().dt.days.fillna(0)
    
    # Encode location using LabelEncoder
    location_encoder = LabelEncoder()
    df['location_encoded'] = location_encoder.fit_transform(df['location'])
    
    return df, location_encoder

# Train model to predict songs
def train_model(df, all_songs):
    rows = []
    for index, row in df.iterrows():
        # Add all songs (played and not played) for each show
        played_songs = set(row['setlist'])
        for song in all_songs:
            rows.append({
                'location_encoded': row['location_encoded'],
                'days_since_last_show': row['days_since_last_show'],
                'song': song,
                'played': 1 if song in played_songs else 0  # 1 if played, 0 if not played
            })
    train_df = pd.DataFrame(rows)

    X = train_df[['location_encoded', 'days_since_last_show']]
    Y = train_df['played']

    # Split into train and test sets
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

    # Train random forest classifier with class weight balancing
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    clf.fit(X_train, Y_train)

    # Evaluate the model
    y_pred = clf.predict(X_test)
    print(classification_report(Y_test, y_pred))

    return clf

# Predict songs for next show
def predict_next_show(clf, location, days_since_last_show, song_list, location_encoder, max_songs=20):
    # Try to encode the location using the trained LabelEncoder, otherwise use a fallback value (-1)
    try:
        location_encoded = location_encoder.transform([location])[0]
    except ValueError:
        print(f"Warning: Unseen location '{location}' encountered. Using fallback encoding (-1).")
        location_encoded = -1

    # Make DataFrame for songs to be predicted
    predict_df = pd.DataFrame({
        'location_encoded': [location_encoded] * len(song_list),
        'days_since_last_show': [days_since_last_show] * len(song_list)
    })

    # Handle case where location_encoded is -1 by filling with the median of the training data
    if location_encoded == -1:
        predict_df['location_encoded'] = np.median(clf.classes_)

    # Predict if the song will be played
    probabilities = clf.predict_proba(predict_df)[:, 1]  # Probability for class 1 (played)

    # Sort songs by likelihood of being played, then select the top N (max_songs)
    song_prob_pairs = list(zip(song_list, probabilities))
    song_prob_pairs_sorted = sorted(song_prob_pairs, key=lambda x: x[1], reverse=True)

    # Get top max_songs, and clean the song titles (strip whitespace)
    predicted_songs = [song.strip() for song, prob in song_prob_pairs_sorted[:max_songs]]

    return predicted_songs

def main():
    xml_file = 'xml_files/allshows_setlistfm.xml'
    df = load_xml_data(xml_file)

    df, location_encoder = preprocess_data(df)

    all_songs = df['setlist'].explode().unique()

    clf = train_model(df, all_songs)

    # Example data of next show
    location = "Enmarket Arena, Savannah, GA, USA"  # This could be a new location
    days_since_last_show = 120
    predicted_songs = predict_next_show(clf, location, days_since_last_show, all_songs, location_encoder, max_songs=20)

    print("Predicted songs for the next show:", predicted_songs)

if __name__ == "__main__":
    main()
