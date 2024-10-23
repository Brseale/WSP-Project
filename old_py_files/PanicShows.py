import requests
from bs4 import BeautifulSoup
import csv

# Base URL template to plug in years
base_list_url = "https://widespreadpanic.com/shows/past/?sf_paged={page_num}"

# Function to get all show URLs from a paginated list of shows
def get_all_show_links():
    all_show_links = []
    for page_num in range(1, 66):  # Loop through pages 1 to 65
        list_url = base_list_url.format(page_num=page_num)
        response = requests.get(list_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the links to individual show pages
        for link in soup.find_all('a', class_='gig-info-link'):
            url = link['href']
            if "widespreadpanic.com/shows" in url:  # Ensure it's a valid show link
                all_show_links.append(url)
                print(f"Found show URL: {url}")
    
    return all_show_links

# Function to scrape data from a show page
def scrape_show_data(show_url):
    response = requests.get(show_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the date and location
    location = soup.find('h1', class_='entry-title').text.strip() if soup.find('h1', class_='entry-title') else "N/A"
    time_tag = soup.find('time', class_='dtstart')
    date = time_tag['datetime'].strip() if time_tag else "N/A"

    # Find the setlist
    setlist_data = {}
    
    # Find all set titles (e.g., "Set I", "Set II", "Encore")
    set_titles = soup.find_all('div', class_='set-title')

    # Loop through each set and get its songs
    for set_title in set_titles:
        current_set = set_title.text.strip()
        setlist_data[current_set] = []  # Initialize an empty list for songs in this set

        # Get the song titles following the set title
        setlist_items = set_title.find_next_siblings('div', class_='setlist-item')
        
        for item in setlist_items:
            # Safely extract the song title, or skip if not found
            song_title_tag = item.find('div', class_='setlist-item-title')
            if song_title_tag:
                song_title = song_title_tag.text.strip()
                setlist_data[current_set].append(song_title)
            else:
                print(f"Warning: Missing song title for set {current_set} on {show_url}")
    
    # Print for debugging purposes
    print(f"Scraped Show: Location: {location}, Date: {date}")
    for set_name, songs in setlist_data.items():
        print(f"{set_name}: {', '.join(songs)}")
    
    # Return the data in a dictionary
    return {
        'location': location,
        'date': date,
        'setlist': setlist_data
    }

# Save the data to a CSV file
def save_to_csv(show_data):
    with open('widespread_panic_shows.csv', 'w', newline='') as csvfile:
        fieldnames = ['date', 'location', 'setlist']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for show in show_data:
            # Flatten the setlist dictionary into a string
            setlist_string = "\n".join([f"{set_name}: {', '.join(songs)}" for set_name, songs in show['setlist'].items()])
            writer.writerow({
                'date': show['date'],
                'location': show['location'],
                'setlist': setlist_string
            })

# Main function to orchestrate scraping and saving
def main():
    all_show_links = get_all_show_links()  # Get all the show URLs
    all_show_data = []
    
    for show_link in all_show_links:
        show_data = scrape_show_data(show_link)
        all_show_data.append(show_data)
    
    # Save all the scraped data to CSV
    save_to_csv(all_show_data)

# Run the main function
if __name__ == "__main__":
    main()

