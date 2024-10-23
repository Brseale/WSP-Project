import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter

def read_file(file_path):
    with open(file_path,'r') as f:
        songs = [line.strip() for line in f.readlines()]

    return songs

if __name__ == "__main__":
    file = "all_covers.txt"
    songs = read_file(file)
    print(songs)