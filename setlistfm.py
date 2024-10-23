import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter

# Base URL template to plug in years
# base_list_url = "https://widespreadpanic.com/shows/past/?sf_paged={page_num}"
base_list_url = "https://www.setlist.fm/setlists/widespread-panic-13d6ad15.html?page={page_num}"
base_domain = "https://www.setlist.fm"

# get all of the show links
def get_all_show_links():
    print("Getting all show links...")
    all_show_links = []
    for page_num in range(78, 304):
        list_url = base_list_url.format(page_num=page_num)
        response = requests.get(list_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        for link in soup.find_all('a', class_='summary url'):
            url = link['href']
            full_url = base_domain + url.lstrip("..")
            all_show_links.append(full_url)
            print(f"Found show link: {full_url}")

    return all_show_links



def get_show_data(show_url):
    response = requests.get(show_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get show location
    h1_tag = soup.find('h1')
    if h1_tag:
        a_tags = h1_tag.find_all('a')

        # Ensure there are enough <a> tags to access the second one
        if len(a_tags) > 1:
            location_span = a_tags[1].find('span')
            location = location_span.get_text() if location_span else "Unknown location"
        else:
            location = "Unknown location"
    else:
        location = "Unknown location"
    
    # Get show date
    month_span = soup.find('span', class_='month')
    day_span = soup.find('span', class_='day')
    year_span = soup.find('span', class_='year')
    if month_span and day_span and year_span:
        month = month_span.get_text()
        day = day_span.get_text()
        year = year_span.get_text()
        date = f"{month} {day}, {year}"
    else:
        date = "Unknown date"

    # Find all songs in setlist
    song_tags = soup.find_all('a', class_='songLabel')
    setlist = []

    for songs in song_tags:
        song_title = songs.get_text()
        setlist.append(song_title)

    return {
        'date': date,
        'location': location,
        'setlist': setlist
    }

def save_to_xml(show_data):
    # Create a new BeautifulSoup object for building XML using lxml-xml parser
    soup = BeautifulSoup('<?xml version="1.0" encoding="UTF-8"?>', 'lxml-xml')
    # Create the root element
    wsp_data = soup.new_tag('wsp_data')
    soup.append(wsp_data)

    for show in show_data:
        show_tag = soup.new_tag('show')

        location = soup.new_tag('location')
        location.string = show['location']

        date = soup.new_tag('date')
        date.string = show['date']

        setlist = soup.new_tag('setlist')
        if show['setlist']:
            for song_title in show['setlist']:
                song = soup.new_tag('song')
                song.string = song_title
                setlist.append(song)

        show_tag.append(location)
        show_tag.append(date)
        show_tag.append(setlist)
        wsp_data.append(show_tag)
    
    with open('allshows_setlistfm_2008.xml', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

def main():
    all_show_links = get_all_show_links()
    all_show_data = []

    if not all_show_links:
        print("No show links found on the page.")
    
    for show in tqdm(all_show_links, desc="Processing shows"):
        show_data = get_show_data(show)
        all_show_data.append(show_data)

    save_to_xml(all_show_data)

if __name__ == "__main__":
    main()


# https://www.setlist.fm/setlists/widespread-panic-13d6ad15.html?page=2
# ../setlist/widespread-panic/2024/hard-rock-hotel-riviera-maya-mexico-7bab9ad0.html" 