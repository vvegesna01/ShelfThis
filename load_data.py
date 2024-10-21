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
@st.cache_data(ttl=86400)  # Cache the results for 24 hours
def get_book_cover(isbn):
    if pd.isna(isbn):
        return None
    url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
    response = requests.get(url)
    
    # Error handling and checking response status
    if response.status_code == 200:
        book_data = response.json()
        if 'items' in book_data:
            image_links = book_data['items'][0]['volumeInfo'].get('imageLinks', {})
            cover_url = image_links.get('thumbnail', None)
            
            # Ensure the URL is using HTTPS
            if cover_url and cover_url.startswith("http:"):
                cover_url = cover_url.replace("http:", "https:")
            
            return cover_url
    
    # Return None if the API call fails or no cover is found
    return None

# Function to render a scrollable book shelf with book covers
def render_bookshelf(book_isbns):
    # Custom CSS to make the shelf scrollable horizontally
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

    # Create a list to hold book cover URLs
    cover_images = []
    
    # Loop through each ISBN, get the cover URL, and append to list
    for isbn in book_isbns:
        cover_url = get_book_cover(isbn)
        if cover_url:
            cover_images.append(cover_url)
        else:
            # Placeholder image for books without a cover
            cover_images.append('https://via.placeholder.com/120x180.png?text=No+Cover')

    # Use st.image() to display covers
    st.image(cover_images, width=120, use_column_width=False)

# Load data
data_load_state = st.text('Loading data...')
data = load_data(300)
data_load_state.text('Loading data...done!')

# Extract the year from 'last date read'
data['read_year'] = data['last date read'].dt.year


st.header("Shelf This 📚")
st.subheader("Keerthana's Reading Dashboard")
st.markdown("""
I've used my imported <a class="footer-link" href="https://app.thestorygraph.com/" target="_blank">Storygraph</a> data to build this dashboard! Just a fun project to see my reading insights.
""", unsafe_allow_html=True)

years = sorted(data['read_year'].dropna().unique(), reverse=True)
years.insert(0, "All years")  # Add "All years" option at the beginning
selected_year = st.selectbox('Select Year', years)

# selet year filter
if selected_year != "All years":
    filtered_data = data[data['read_year'] == selected_year]
else:
    filtered_data = data


st.write('---')

# highest-rated books section
st.subheader("My Highest Rated Reads")
highest_rated_books = data.nlargest(10, 'star rating')  # Adjust number to show more or less
highest_rated_isbns = highest_rated_books['isbn/uid'].dropna().unique()
render_bookshelf(highest_rated_isbns)

st.write("---")

# total books read
total_books = len(filtered_data)
st.subheader(f"Total Books Read: {total_books}")


if 'star rating' in filtered_data.columns and 'format' in filtered_data.columns:

    col1, col2 = st.columns(2)
    
    # my star ratings (pie chart) section
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

    # books by format (also pie chart) section
    with col2:
        format_counts = filtered_data['format'].value_counts()
        fig_format_pie = px.pie(
            names=format_counts.index,
            values=format_counts.values,
            title='Books by Format',
            hole=0.3
        )
        st.plotly_chart(fig_format_pie)

# get the most used format
most_used_format_name = format_counts.idxmax()  # Get the name of the most used format
most_used_format_count = format_counts.max()     # Get the count of the most used format
st.write(f"**Most Used Format**: {most_used_format_name} ({most_used_format_count} books)")

st.write('---')

st.subheader('Bookshelf')
book_isbns = filtered_data['isbn/uid'].dropna().unique()
render_bookshelf(book_isbns)

st.write('---')

#bar chart for books read each year
books_per_year = data.groupby('read_year').size()
fig_books_year = px.bar(
    x=books_per_year.index,
    y=books_per_year.values,
    labels={'x': 'Year', 'y': 'Number of Books'},
    title='Books Read by Year'
)

fig_books_year.update_xaxes(tickvals=books_per_year.index)
st.plotly_chart(fig_books_year)

# Raw Data Section
st.subheader('Raw Book Data')
st.write(filtered_data[['title', 'authors', 'format', 'star rating']])


# Reading Pace Section
st.subheader('My Reading Pace Through the Years')

# month and date to get reading pace 
data['read_year'] = data['last date read'].dt.year
data['read_month'] = data['last date read'].dt.month
years = sorted(data['read_year'].dropna().unique(), reverse=True)

# selectbox for the selected year
selected_year = st.selectbox('Select Year for Reading Pace', years)
filtered_data = data[data['read_year'] == selected_year]

# books read per month count
books_per_month = filtered_data.groupby('read_month').size().reset_index(name='books_read')

# scatter plot
fig_reading_pace = px.line(
    books_per_month,
    x='read_month',
    y='books_read',
    labels={'read_month': 'Month', 'books_read': 'Books Read'},
    title=f'Reading Pace - Books Read Per Month in {selected_year}',
    markers=True,  # This adds the dots at each data point
    category_orders={"read_month": list(range(1, 13))}  # Ensures months are ordered correctly
)


fig_reading_pace.update_xaxes(
    tickvals=list(range(1, 13)),
    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
)


fig_reading_pace.update_traces(
    line=dict(color='grey', width=2),  # Line color and width
    marker=dict(size=10, color='skyblue', opacity=0.8, line=dict(width=2, color='DarkSlateGrey'))  # Marker properties
)

st.plotly_chart(fig_reading_pace)

# Contact Footer
st.write('---')
st.subheader("About the author!")


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
 <a class="footer-link" href="https://keerthana-vegesna.vercel.app/" target="_blank"><i class="fas fa-laptop footer-icon"></i> Portfolio Website</a>
 <a class="footer-link" href="https://www.linkedin.com/in/keerthana-vegesna/" target="_blank"><i class="fab fa-linkedin footer-icon"></i> LinkedIn</a>
""", unsafe_allow_html=True)

# Copyright notice
st.markdown("<p style='font-style: italic;'>© 2024 Keerthana Vegesna. All rights reserved.</p>", unsafe_allow_html=True)
