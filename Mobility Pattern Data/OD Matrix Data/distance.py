import pandas as pd
import googlemaps
import csv
from tqdm import tqdm
from math import radians, cos, sin, sqrt, atan2

# Your Google API key
API_KEY = 'AIzaSyD6NQgAw8rJbMfkCnYY6Y4zC_2W3ZUIMj8'

# Initialize Google Maps client
gmaps = googlemaps.Client(key=API_KEY)

# Read the CSV file
df = pd.read_excel('OD_Matrix_AreaWise_V1.xlsx')

# Initialize Google Maps client1
gmaps = googlemaps.Client(key=API_KEY)


# Function to calculate distance using Google Maps API
def calculate_traveling_distance(home_lat, home_lng, work_lat, work_lng):
    try:
        result = gmaps.distance_matrix(
            origins=f"{home_lat},{home_lng}",
            destinations=f"{work_lat},{work_lng}",
            mode="driving"
        )
        distance = result['rows'][0]['elements'][0]['distance']['value']  # distance in meters
        return distance / 1000  # convert to kilometers
    except Exception as e:
        print(f"Error calculating traveling distance: {e}")
        return None

# Function to calculate direct distance using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Create new columns for distances with tqdm progress bar
traveling_distances = []
direct_distances = []

for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    traveling_distance = calculate_traveling_distance(
        row['HOME_LATITUDE'], row['HOME_LONGITUDE'], row['WORK_LATITUDE'], row['WORK_LONGITUDE']
    )
    direct_distance = haversine(
        row['HOME_LATITUDE'], row['HOME_LONGITUDE'], row['WORK_LATITUDE'], row['WORK_LONGITUDE']
    )
    traveling_distances.append(traveling_distance)
    direct_distances.append(direct_distance)

df['TRAVELING_DISTANCE_KM'] = traveling_distances
df['DIRECT_DISTANCE_KM'] = direct_distances

# Save the updated dataframe to a new CSV file
df.to_csv('OD_Matrix_AreaWise_V1_with_Distances.csv', index=False)

print("Distance calculations (traveling and direct) completed and saved to OD_Matrix_AreaWise_V1_with_Distances.csv")