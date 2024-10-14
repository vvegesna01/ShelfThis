# Import necessary libraries
import pandas as pd
import streamlit as st
import plotly.express as px
import requests

# Define the path or URL to your CSV file
DATA_URL = './books.csv'

# Date columns for special processing
DATE_COLUMNS = ['Date Added', 'Last Date Read', 'Dates Read']

# Function to load data
@st.cache_data
def load_data(nrows):
    # Read the CSV file
    data = pd.read_csv(DATA_URL, nrows=nrows)
    
    # Convert column names to lowercase
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)

    # Convert relevant date columns to datetime
    for date_column in DATE_COLUMNS:
        if date_column.lower() in data.columns:
            data[date_column.lower()] = pd.to_datetime(data[date_column.lower()], errors='coerce')
    
    # Filter books with read_status as 'read'
    data = data[data['read status'].str.lower() == 'read']
    
    return data

# Function to get book cover image URL from Google Books API using ISBN
@st.cache_data
def get_book_cover(isbn):
    url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
    response = requests.get(url)
    if response.status_code == 200:
        book_data = response.json()
        if 'items' in book_data:
            return book_data['items'][0]['volumeInfo']['imageLinks'].get('thumbnail', None)
    return None

# Load data
data_load_state = st.text('Loading data...')
data = load_data(300)
data_load_state.text('Loading data...done!')

# Extract the year from 'last date read'
data['read_year'] = data['last date read'].dt.year

# Add filter for year on the main page
st.header("Shelf This")
st.subheader("Keerthana's Reading Dashboard")
st.markdown("""
I've used my imported <a class="footer-link" href="https://app.thestorygraph.com/" target="_blank">Storygraph</a> data to build this dashboard! Just a fun project to see my reading insights.
""", unsafe_allow_html=True)

# Create a selectbox for year filtering with "All years" as default
years = sorted(data['read_year'].dropna().unique(), reverse=True)
years.insert(0, "All years")  # Add "All years" option at the beginning
selected_year = st.selectbox('Select Year', years)

# Filter data based on the selected year (or show all data if "All years" is selected)
if selected_year != "All years":
    filtered_data = data[data['read_year'] == selected_year]
else:
    filtered_data = data

# Bookshelf for highest-rated books of all time
st.write('---')
st.subheader("My Highest Rated Reads")

# Filter for highest-rated books
highest_rated_books = data.nlargest(10, 'star rating')  # Adjust number to show more or less
highest_rated_isbns = highest_rated_books['isbn/uid'].dropna().unique()

# Generate the HTML for the scrollable shelf of highest-rated books
highest_rated_covers_html = '<div class="scrollable-shelf">'
for isbn in highest_rated_isbns:
    cover_url = get_book_cover(isbn)
    if cover_url:
        highest_rated_covers_html += f'<img src="{cover_url}" width="120" height="180"/>'
highest_rated_covers_html += '</div>'

# Render the HTML for the highest-rated shelf
st.markdown(highest_rated_covers_html, unsafe_allow_html=True)

st.write("---")

# Total books read
total_books = len(filtered_data)
st.subheader(f"Total Books Read: {total_books}")

### Visualization 4: Pie Chart for Star Ratings and Format
if 'star rating' in filtered_data.columns and 'format' in filtered_data.columns:
    # Create two columns
    col1, col2 = st.columns(2)
    
    # Star Ratings Pie Chart
    with col1:
        star_rating_counts = filtered_data['star rating'].value_counts()
        fig_star_rating_pie = px.pie(
            names=star_rating_counts.index,
            values=star_rating_counts.values,
            title='Star Ratings Breakdown',
            hole=0.3
        )
        st.plotly_chart(fig_star_rating_pie)
        # Average Rating Display
        avg_rating = filtered_data['star rating'].mean()
        st.write(f"**Average Star Rating**: {avg_rating:.2f}")

    # Books by Format Pie Chart
    with col2:
        format_counts = filtered_data['format'].value_counts()
        fig_format_pie = px.pie(
            names=format_counts.index,
            values=format_counts.values,
            title='Books by Format',
            hole=0.3
        )
        st.plotly_chart(fig_format_pie)

# Get the most used format
most_used_format_name = format_counts.idxmax()  # Get the name of the most used format
most_used_format_count = format_counts.max()     # Get the count of the most used format
st.write(f"**Most Used Format**: {most_used_format_name} ({most_used_format_count} books)")

st.write('---')
# Display book cover shelf for all books at the top
st.subheader('Bookshelf')
book_isbns = filtered_data['isbn/uid'].dropna().unique()

# Create a scrollable horizontal shelf of book covers
st.markdown("""
    <style>
    .scrollable-shelf {
        display: flex;
        overflow-x: scroll;
        padding: 10px;
        white-space: nowrap;
    }
    .scrollable-shelf img {
        margin-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Generate the HTML for the scrollable shelf
book_covers_html = '<div class="scrollable-shelf">'
for isbn in book_isbns:
    cover_url = get_book_cover(isbn)
    if cover_url:
        book_covers_html += f'<img src="{cover_url}" width="120" height="180"/>'
book_covers_html += '</div>'

# Render the HTML for the shelf
st.markdown(book_covers_html, unsafe_allow_html=True)

### Additional Insights:
st.write('---')
### Visualization 3: Bar Chart for Number of Books Read by Year
books_per_year = data.groupby('read_year').size()
fig_books_year = px.bar(
    x=books_per_year.index,
    y=books_per_year.values,
    labels={'x': 'Year', 'y': 'Number of Books'},
    title='Books Read by Year'
)

# Update x-axis to show only integer year values
fig_books_year.update_xaxes(tickvals=books_per_year.index)
st.plotly_chart(fig_books_year)

# Show table of filtered data
st.subheader('Raw Book Data')
st.write(filtered_data[['title', 'authors', 'format', 'star rating']])

# Contact Footer
st.write('---')
st.subheader("Here's some links")

# Adding Font Awesome for icons
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<style>
    .footer-link {
        text-decoration: none;
        color: black;
        margin-right: 15px;
    }
    .footer-link:hover {
        color: #0073e6;
    }
    .footer-icon {
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Using Font Awesome icons
st.markdown("""
 <a class="footer-link" href="https://github.com/vvegesna01" target="_blank"><i class="fab fa-github footer-icon"></i> GitHub</a>
 <a class="footer-link" href="https://localhost-keerthana.vercel.app/" target="_blank"><i class="fas fa-laptop footer-icon"></i> Portfolio Website</a>
 <a class="footer-link" href="https://www.linkedin.com/in/keerthana-vegesna/" target="_blank"><i class="fab fa-linkedin footer-icon"></i> LinkedIn</a>
""", unsafe_allow_html=True)

# Copyright notice
st.markdown("<p style='font-style: italic;'>© 2024 Keerthana Vegesna. All rights reserved.</p>", unsafe_allow_html=True)
