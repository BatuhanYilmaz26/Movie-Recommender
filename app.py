from classifier import KNearestNeighbours
import streamlit as st
from streamlit_lottie import st_lottie
import json
from bs4 import BeautifulSoup
import requests, io
import PIL.Image
from urllib.request import urlopen
import os
from googleapiclient.discovery import build
import pandas as pd

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# Define a function that we can use to load lottie files from a link.
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_movies = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_cbrbre30.json")

col_lottie, col_title = st.columns([1, 3])
with col_lottie:
    st_lottie(lottie_movies)
with col_title:
    st.title("Movie Recommender")
    st.markdown('''<h5 style='text-align: left; color: #d73b5c;'> This recommendation system is based on the IMDB 5000 Movie Dataset.</h5>''', unsafe_allow_html=True)

# Load the movie data and movie titles
df = pd.read_csv("./Data/movie_metadata.csv")
with open("./Data/movie_data.json", "r+", encoding="utf-8") as f:
    data = json.load(f)
with open("./Data/movie_titles.json", "r+", encoding="utf-8") as f:
    movie_titles = json.load(f)

youtube_api_key = os.environ.get("youtube_api_key")
youtube = build("youtube", "v3", developerKey=youtube_api_key)

def movie_poster_fetcher(imdb_link):
    # Display the movie poster
    url_data = requests.get(imdb_link).text
    s_data = BeautifulSoup(url_data, "html.parser")
    imdb_dp = s_data.find("meta", property="og:image")
    movie_poster_link = imdb_dp.attrs["content"]
    u = urlopen(movie_poster_link)
    raw_data = u.read()
    image = PIL.Image.open(io.BytesIO(raw_data))
    image = image.resize((250, 400), PIL.Image.ANTIALIAS)
    st.image(image)

def get_movie_info(imdb_link):
    # Display the movie information
    url_data = requests.get(imdb_link).text
    s_data = BeautifulSoup(url_data, "html.parser")
    imdb_content = s_data.find("meta", property="og:description")
    movie_description = imdb_content.attrs["content"]
    movie_description = str(movie_description).split(".")
    movie_director = movie_description[0]
    movie_title = s_data.find("meta", property="og:title")
    movie_title = movie_title.attrs["content"]
    movie_year = movie_title.split("(")[1].split(")")[0]
    movie_cast = str(movie_description[1]).replace("With", "Cast: ").strip()
    movie_story= "Plot Summary: " + s_data.find("span", {"data-testid": "plot-xl"}).text
    rating = s_data.find("div", class_="AggregateRatingButton__TotalRatingAmount-sc-1ll29m0-3 jkCVKJ")
    rating = str(rating).split('<div class="AggregateRatingButton__TotalRatingAmount-sc-1ll29m0-3 jkCVKJ')
    rating = str(rating[1]).split("</div>")
    rating = str(rating[0]).replace(''' "> ''', '').replace('">', '')
    # get genres from df if imdb_link are matching
    if imdb_link in df["movie_imdb_link"].values:
        movie_genres = df.loc[df["movie_imdb_link"] == imdb_link, "genres"].values[0]
        # remove |, [, , ] from movie_genres
        chars = ["|", "[", "]"]
        for char in chars:
            movie_genres = movie_genres.replace(char, ", ")
    else:
        movie_genres = "Not Found"
    
    # get duration from df if imdb_link are matching
    if imdb_link in df["movie_imdb_link"].values:
        movie_duration = df.loc[df["movie_imdb_link"] == imdb_link, "duration"].values[0]
    else:
        movie_duration = "Not Found"

    request = youtube.search().list(part="snippet", channelType="any", maxResults=1, q=f"{movie_title} Official Trailer")
    response = request.execute()
    trailer_link = [f"https://www.youtube.com/watch?v={video['id']['videoId']}" \
    for video in response['items']]

    movie_rating = "Total Rating count: " + rating
    return movie_director, movie_cast, movie_story, movie_rating, trailer_link, movie_year, movie_genres, movie_duration


def knn_movie_recommender(test_point, k):
    # Create dummy target variable for the KNN classifier
    target = [0 for item in movie_titles]
    # Instantiate the KNN classifier
    model = KNearestNeighbours(data, target, test_point, k=k)
    # Run the algorithm
    model.fit()
    # Print the list of top k recommended movies
    table = []
    for i in model.indices:
        # Append the movie title and its imdb link
        table.append([movie_titles[i][0], movie_titles[i][2],data[i][-1]])
    print(table)
    return table

def run_recommender():
    genres = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
              'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News',
              'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Thriller', 'War', 'Western']
    movies = [title[0] for title in movie_titles]
    category = ["Select a recommendation type", "Movie based", "Genre based"]
    category_option = st.selectbox("Select a recommendation type", category)
    if category_option == category[0]:
        st.error("Please select a recommendation type")
    elif category_option == category[1]:
        select_movie = st.selectbox("Please select a movie:", movies)
        number_of_rec = st.slider("How many recommendations do you want?", min_value=5, max_value=20, step=1, value=5)
        genres = data[movies.index(select_movie)]
        test_points = genres
        table = knn_movie_recommender(test_points, number_of_rec+1)
        table.pop(0)
        c = 0
        if st.button("Show recommendations"):
            for movie, link, ratings in table:
                c+=1
                director, cast, movie_story, total_rating, trailer_link, movie_year, movie_genres, movie_duration = get_movie_info(link)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"(**{c}**) [**{movie}**]({link}) **({movie_year})**", unsafe_allow_html=True)
                    movie_poster_fetcher(link)
                    st.markdown(f"**{director}**")
                    st.markdown(f"**{cast}**")
                    st.markdown(f"**{movie_story}**")
                    st.markdown(f"**Runtime: {movie_duration:.0f} minutes.**")
                    st.markdown(f"**Genres: {movie_genres} .**")
                    st.markdown(f"**{total_rating}**")
                    st.markdown(f"**IMDB Rating: {str(ratings)} ⭐**")
                with col2:
                    st.video(trailer_link[0])

    elif category_option == category[2]:
        select_genre = st.multiselect("Please select a genre:", genres)
        if select_genre:
            imdb_score = st.slider("Choose an IMDB score:", min_value=1, max_value=10, step=1, value=7)
            number_of_rec = st.slider("How many recommendations do you want?", min_value=5, max_value=20, step=1, value=5)
            test_point = [1 if genre in select_genre else 0 for genre in genres]
            test_point.append(imdb_score)
            table = knn_movie_recommender(test_point, number_of_rec)
            c = 0
            if st.button("Show recomendations"):
                for movie, link, ratings in table:
                    c+=1
                    director, cast, movie_story, total_rating, trailer_link, movie_year, movie_genres, movie_duration = get_movie_info(link)
                    col5, col6 = st.columns(2)
                    with col5:
                        st.markdown(f"(**{c}**) [**{movie}**]({link}) **({movie_year})**")
                        movie_poster_fetcher(link)
                        st.markdown(f"**{director}**")
                        st.markdown(f"**{cast}**")
                        st.markdown(f"**{movie_story}**")
                        st.markdown(f"**Runtime: {movie_duration:.0f} minutes.**")
                        st.markdown(f"**Genres: {movie_genres} .**")
                        st.markdown(f"**{total_rating}**")
                        st.markdown(f"**IMDB Rating: {str(ratings)} ⭐**")
                    with col6:
                        st.video(trailer_link[0])

run_recommender()