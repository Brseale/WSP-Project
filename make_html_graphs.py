from bs4 import BeautifulSoup
from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from collections import Counter
import seaborn as sns
from geopy.geocoders import Nominatim
import geopandas as gpd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.drawing.image import Image as ExcelImage
import os

# Create a folder to store the plots
if not os.path.exists('plots'):
    os.makedirs('plots')

# Read in the cover songs
def read_cover_songs(file_path):
    with open(file_path, 'r') as f:
        cover_songs = [line.strip() for line in f.readlines()]
    return cover_songs

# Parse the xml file of all the shows
def parse_xml(xml_file):
    with open(xml_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'lxml-xml')

        shows = []

        # Extract show details
        for show in soup.find_all('show'):
            date = show.find('date').get_text()
            location = show.find('location').get_text()
            setlist = [song.get_text() for song in show.find_all('song')]
            shows.append({
                'date': date,
                'location': location,
                'setlist': setlist,
                'num_songs': len(setlist)
            })

    return shows

# create the dataframe
def create_dataframe(shows):
    data = {
        'date': [],
        'location': [],
        'num_songs': [],
        'setlist': []
    }
    for show in shows:
        data['date'].append(show['date'])
        data['location'].append(show['location'])
        data['num_songs'].append(show['num_songs'])
        data['setlist'].append(show['setlist'])

    df = pd.DataFrame(data)
    return df

# Get stats for cover songs
def get_cover_song_stats(df, cover_songs):
    cover_song_counts = Counter()

    normalized_cover_songs = [song.lower().strip() for song in cover_songs]

    for setlist in df['setlist']:
        for song in setlist:
            normalized_song = song.lower().strip()

            if normalized_song in normalized_cover_songs:
                cover_song_counts[song] += 1 

    return cover_song_counts

def plot_num_songs_per_show(df):
    df['date'] = pd.to_datetime(df['date'])
    df_sorted = df.sort_values('date')
    
    fig = go.Figure(data=go.Bar(x=df_sorted['date'], y=df_sorted['num_songs']))
    fig.update_layout(title='Number of Songs Per Show', xaxis_title='Date', yaxis_title='Number of Songs')
    fig.write_html("templates/num_songs_per_show.html")

def plot_song_distribution_across_locations_bar(df, top_n=20):
    location_counts = df['location'].value_counts().head(top_n)
    data = pd.DataFrame({'Location': location_counts.index, 'Shows': location_counts.values})
    fig = px.bar(data, x='Shows', y='Location', orientation='h', title=f'Top {top_n} Locations by Number of Shows', color_discrete_sequence=['blue'])
    fig.update_layout(xaxis_title="Number of Shows", yaxis_title="Location")
    fig.write_html("templates/song_distribution_locations.html")

def plot_song_repetition_over_time(df, song_name="Disco"):
    df['date'] = pd.to_datetime(df['date'])
    dates = df['date']
    song_played = [1 if song_name in setlist else 0 for setlist in df['setlist']]
    
    fig = go.Figure(data=go.Scatter(x=dates, y=song_played, mode='lines+markers'))
    fig.update_layout(title=f'Repetition of "{song_name}" Over Time', xaxis_title='Date', yaxis_title=f'{song_name} Played (1 = Yes, 0 = No)')
    fig.write_html("templates/song_repetition_over_time.html")

def plot_most_popular_closing_songs(df):
    closing_songs = [setlist[-1] for setlist in df['setlist'] if setlist]
    closing_song_counts = Counter(closing_songs).most_common(10)
    song_names, song_counts = zip(*closing_song_counts)

    data = pd.DataFrame({'Song': song_names, 'Plays': song_counts})
    fig = px.bar(data, x='Song', y='Plays', title='Top 10 Most Popular Closing Songs', color_discrete_sequence=['orange'])
    fig.write_html("templates/most_popular_closing_songs.html")

def plot_most_frequent_opening_songs(df):
    opening_songs = [setlist[0] for setlist in df['setlist'] if setlist]
    opening_song_counts = Counter(opening_songs).most_common(10)
    song_names, song_counts = zip(*opening_song_counts)

    data = pd.DataFrame({'Song': song_names, 'Plays': song_counts})
    fig = px.bar(data, x='Song', y='Plays', title='Top 10 Most Popular Opening Songs', color_discrete_sequence=['green'])
    fig.write_html("templates/most_frequent_opening_songs.html")

def plot_num_songs_trend_over_time(df):
    df['date'] = pd.to_datetime(df['date'])
    df_sorted = df.sort_values('date')
    
    fig = go.Figure(data=go.Scatter(x=df_sorted['date'], y=df_sorted['num_songs'], mode='lines+markers'))
    fig.update_layout(title='Trend of Number of Songs Per Show Over Time', xaxis_title='Date', yaxis_title='Number of Songs')
    fig.write_html("templates/num_songs_trend_over_time.html")

def plot_shows_heatmap(df, top_n=20):
    df['month'] = pd.to_datetime(df['date']).dt.month
    location_month_counts = df.groupby(['location', 'month']).size().unstack(fill_value=0)
    top_locations = location_month_counts.sum(axis=1).nlargest(top_n).index
    location_month_counts = location_month_counts.loc[top_locations]

    fig = px.imshow(location_month_counts, labels=dict(x="Month", y="Location", color="Shows"), x=location_month_counts.columns, y=location_month_counts.index, color_continuous_scale="Viridis")
    fig.update_layout(title='Number of Shows by Location and Month (Top Locations)')
    fig.write_html("templates/shows_heatmap.html")

def plot_least_frequent_songs(df):
    all_songs = [song for setlist in df['setlist'] for song in setlist]
    song_counter = Counter(all_songs)
    least_common_songs = song_counter.most_common()[:-21:-1]
    song_names, song_counts = zip(*least_common_songs) if least_common_songs else ([], [])

    data = pd.DataFrame({'Song': song_names, 'Plays': song_counts})
    fig = px.bar(data, x='Song', y='Plays', title='Top 20 Least Frequently Played Songs', color_discrete_sequence=['red'])
    fig.write_html("templates/least_frequent_songs.html")

def plot_popular_cover_songs(cover_song_counts, top_n=20):
    most_common_covers = cover_song_counts.most_common(top_n)
    if most_common_covers:
        song_names, play_counts = zip(*most_common_covers)
        data = pd.DataFrame({'Cover Songs': song_names, 'Plays': play_counts})
        
        # Interactive Plotly figure
        fig = px.bar(data, x='Cover Songs', y='Plays', title=f'Top {top_n} Most Frequently Played Cover Songs', color_discrete_sequence=['blue'])
        fig.write_html("templates/popular_cover_songs.html")

# Plot 11: Least popular cover songs (interactive)
def plot_least_popular_cover_songs(cover_song_counts):
    least_common_covers = cover_song_counts.most_common()[:-21:-1]  # Gets 20 least common
    if least_common_covers:
        song_names, play_counts = zip(*least_common_covers)
        data = pd.DataFrame({'Cover Songs': song_names, 'Plays': play_counts})
        
        # Interactive Plotly figure
        fig = px.bar(data, x='Cover Songs', y='Plays', title='Top 20 Least Frequently Played Cover Songs', color_discrete_sequence=['blue'])
        fig.write_html("templates/least_popular_cover_songs.html")

if __name__ == "__main__":

    # Read in cover songs
    cover_songs_file = 'txt_files/all_covers.txt'
    cover_songs = read_cover_songs(cover_songs_file)

    # Parse the XML file
    xml_file = 'xml_files/allshows_setlistfm.xml'
    shows = parse_xml(xml_file)

    # Create a DataFrame from the shows
    df = create_dataframe(shows)
    cover_song_counts = get_cover_song_stats(df, cover_songs)

    #plot_num_songs_per_show(df)
    plot_song_distribution_across_locations_bar(df, top_n=20)
    # plot_song_repetition_over_time(df, song_name="Disco")
    # plot_most_popular_closing_songs(df)
    # plot_most_frequent_opening_songs(df)
    # plot_num_songs_trend_over_time(df)
    # plot_shows_heatmap(df, top_n=20)
    # plot_least_frequent_songs(df)
    # plot_popular_cover_songs(cover_song_counts, top_n=20)
    # plot_least_popular_cover_songs(cover_song_counts)
    