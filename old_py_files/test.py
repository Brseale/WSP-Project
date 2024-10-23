import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter

# Base URL template to plug in years
base_list_url = "https://widespreadpanic.com/shows/past/?sf_paged={page_num}"

# get all of the show links
def get_all_show_links():
    print("Getting all show links...")
    all_show_links = []
    for page_num in range(1, 66):
        list_url = base_list_url.format(page_num=page_num)
        response = requests.get(list_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        for link in soup.find_all('a', class_='gig-info-link'):
            url = link['href']
            all_show_links.append(url)
            print(f"Found show link: {url}")

    return all_show_links

def get_show_data(show_url):
    response = requests.get(show_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get location and date with .strip() to remove extra spaces and newlines
    location_tag = soup.find('h1', class_='entry-title')
    date_tag = soup.find('div', class_='full-date')

    location = location_tag.get_text().strip() if location_tag else "Unknown location"
    date = date_tag.get_text().strip() if date_tag else "Unknown date"

    # Find all setlist items
    setlist_items = soup.find_all('div', class_='setlist-item')
    setlist = []

    for songs in setlist_items:
        song_title_tag = songs.find('div', class_='setlist-item-title')
        if song_title_tag:
            # Get song title text and remove any leading numbers (e.g., 1Greta or 1. Greta)
            song_title = song_title_tag.get_text(strip=True)
            # Updated regex to remove any leading numbers, with or without dots or spaces
            song_title = re.sub(r'^\d+\s*', '', song_title)
            setlist.append(song_title)
        else:
            setlist.append("Unknown song")

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
    
    with open('allshows.xml', 'w', encoding='utf-8') as f:
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