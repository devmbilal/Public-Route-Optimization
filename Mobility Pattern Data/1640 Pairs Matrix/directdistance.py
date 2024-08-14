import pandas as pd
from math import radians, cos, sin, sqrt, atan2
from tqdm import tqdm

# Read the CSV file
df = pd.read_excel('1640 Pairs Matrix.xlsx')

# Function to calculate direct distance using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Calculate the direct distance and add it as a new column
df['DIRECT_DISTANCE_KM'] = df.apply(lambda row: haversine(
    row['HOME_LATITUDE'], row['HOME_LONGITUDE'], row['WORK_LATITUDE'], row['WORK_LONGITUDE']
), axis=1)

# Save the updated dataframe to a new CSV file
df.to_csv('1640 Pairs Matrix_Direct_Distances.csv', index=False)

print("Direct distance calculation completed and saved to 1640 Pairs Matrix_with_Direct_Distances.csv")
