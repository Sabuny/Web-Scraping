import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import sqlite3
from datetime import datetime

# Product mapping
products = {
    1: "Dry Maize",
    163: "White Irish Potatoes",
    158: "Dry Onions",
    150: "Watermelons",
    226: "Ripe Bananas",
    127: "Oranges",
    147: "Mangoes",
    154: "Kales",
    161: "Regular Spinach",
    255: "Cooking Bananas"
}

# Base URL
base_url = "https://amis.co.ke/site/market/0?product={product}&per_page=3000"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# Initialize an empty list to store the data
all_data = []

# Scrape the latest data for all products
for product_id, product_name in products.items():
    print(f"Scraping latest data for {product_name} (Product ID: {product_id})...")
    url = base_url.format(product=product_id)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = bs(response.content, "html.parser")
        table = soup.find("table", class_="table table-bordered table-condensed")
        if table:
            for row in table.find("tbody").find_all("tr"):
                cells = [td.text.strip() for td in row.find_all("td")]
                all_data.append(cells)
        else:
            print(f"No table found for {url}")
    else:
        print(f"Failed to retrieve {url}, status code: {response.status_code}")

# Extracting column headers
columns = [th.text.strip() for th in table.find("thead").find_all("th")]

# Creating a DataFrame
df = pd.DataFrame(all_data, columns=columns)
df.columns = ["Product", "Classification", "Grade", "Sex", "Market Area", "Wholesale Price", "Retail Price", "Quantity Supplied", "County Area", "Date"]

# Data cleaning
df = df.drop(columns=["Classification", "Grade", "Sex"])  # Drop unnecessary columns
df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")  # Convert Date to datetime

for col in ["Wholesale Price", "Retail Price", "Quantity Supplied"]:
    df[col] = df[col].str.extract(r"([\d\.]+)", expand=False)  # Extract numeric values
    df[col] = df[col].astype(float)

# Filter for specific counties
counties = ["Nairobi", "Nyandarua", "Nakuru", "Meru", "Kirinyaga"]
df = df[df["County Area"].isin(counties)]
df = df.dropna()

db_path = r"C:\Users\USER\Markets.db"
conn = sqlite3.connect(db_path)

# Insert data into the table without overwriting
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS Crops (
    Product TEXT,
    Market Area TEXT,
    Wholesale Price REAL,
    Retail Price REAL,
    Quantity Supplied REAL,
    County Area TEXT,
    Date DATE
);
""")
conn.commit()

# Append only new rows
existing_data = pd.read_sql_query("SELECT * FROM Crops", conn)
merged_data = pd.concat([existing_data, df]).drop_duplicates()
merged_data.to_sql("Crops", conn, if_exists="replace", index=False)

print("Database updated successfully.")

conn.commit()
conn.close()
