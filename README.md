# Top Restaurants Finder

This script fetches the top 10 restaurants in a city using Google Places API.

## Setup

1. Copy `.env.example` to `.env` and add your API key.
2. Install dependencies:
   pip3 install requests python-dotenv
3. Running the Script
    python3 top_restaurants_google_places.py
       Enter the name of the city when prompted.
       The script will fetch and display the top 10 restaurants.
       The results will be saved in a JSON file in the same folder.
4. Notes
     Ensure your API key has access to the Google Places API.
