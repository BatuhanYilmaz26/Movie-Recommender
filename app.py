from classifier import KNearestNeighbours
import streamlit as st
from streamlit_lottie import st_lottie
import json
from bs4 import BeautifulSoup
import requests, io
import PIL.Image
from urllib.request import urlopen

st.set_page_config(page_title="Movie Recommender", page_icon="🎬")

# Define a function that we can use to load lottie files from a link.
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_movies = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_cbrbre30.json")
st_lottie(lottie_movies, width=200, height=200)

# Load the movie data and movie titles
with open("./Data/movie_data.json", "r+", encoding="utf-8") as f:
    data = json.load(f)
with open("./Data/movie_titles.json", "r+", encoding="utf-8") as f:
    movie_titles = json.load(f)

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
    movie_cast = str(movie_description[1]).replace("With", "Cast: ").strip()
    movie_story = "Story: " + str(movie_description[2]).strip() + "."
    rating = s_data.find("div", class_="AggregateRatingButton__TotalRatingAmount-sc-1ll29m0-3 jkCVKJ")
    rating = str(rating).split('<div class="AggregateRatingButton__TotalRatingAmount-sc-1ll29m0-3 jkCVKJ')
    rating = str(rating[1]).split("</div>")
    rating = str(rating[0]).replace(''' "> ''', '').replace('">', '')

    movie_rating = "Total Rating count: " + rating
    return movie_director, movie_cast, movie_story, movie_rating

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
    st.title("Movie Recommender System")
    st.markdown('''<h5 style='text-align: left; color: #d73b5c;'> This recommendation system is based on the IMDB 5000 Movie Dataset.</h5>''', unsafe_allow_html=True)
    genres = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
              'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News',
              'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Thriller', 'War', 'Western']
    movies = [title[0] for title in movie_titles]
    category = ["Select recommendation type", "Movie based", "Genre based"]
    category_option = st.selectbox("Select recommendation type", category)
    if category_option == category[0]:
        st.write("Please select a recommendation type")
    elif category_option == category[1]:
        select_movie = st.selectbox("Please select a movie:", ['--Select--'] + movies)
        poster = st.radio("Do you want to see the movie posters?", ("Yes", "No"))
        st.markdown('''<h5 style='text-align: left; color: #d73b5c;'> Fetching the movie poster...</h5>''', unsafe_allow_html=True)
        if poster == "No":
            if select_movie == '--Select--':
                st.write("No poster will be displayed")
            else:
                number_of_rec = st.slider("How many recommendations do you want?", min_value=5, max_value=20, step=1)
                genres = data[movies.index(select_movie)]
                test_points = genres
                table = knn_movie_recommender(test_points, number_of_rec+1)
                table.pop(0)
                c = 0
                st.success("The recommended movies are:")
                for movie, link, ratings in table:
                    c+=1
                    director, cast, story, total_rating = get_movie_info(link)
                    st.markdown(f"({c}) [{movie}]({link})")
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rating)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
        else:
            if select_movie == '--Select--':
                st.warning("Please select a movie")
            else:
                number_of_rec = st.slider("How many recommendations do you want?", min_value=5, max_value=20, step=1)
                genres = data[movies.index(select_movie)]
                test_points = genres
                table = knn_movie_recommender(test_points, number_of_rec+1)
                table.pop(0)
                c = 0
                st.success("The recommended movies are:")
                for movie, link, ratings in table:
                    c+=1
                    st.markdown(f"({c}) [{movie}]({link})")
                    movie_poster_fetcher(link)
                    director, cast, story, total_rating = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rating)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
    elif category_option == category[2]:
        select_genre = st.multiselect("Please select a genre:", genres)
        poster = st.radio("Do you want to see the movie posters?", ("Yes", "No"))
        st.markdown('''<h5 style='text-align: left; color: #d73b5c;'> Fetching the movie poster...</h5>''', unsafe_allow_html=True)
        if poster == "No":
            if select_genre:
                imdb_score = st.slider("Choose an IMDB score:", min_value=1, max_value=10, step=1)
                number_of_rec = st.slider("How many recommendations do you want?", min_value=5, max_value=20, step=1)
                test_point = [1 if genre in select_genre else 0 for genre in genres]
                test_point.append(imdb_score)
                table = knn_movie_recommender(test_point, number_of_rec)
                c = 0
                st.success("The recommended movies are:")
                for movie, link, ratings in table:
                    c+=1
                    st.markdown(f"({c}) [{movie}]({link})")
                    director, cast, story, total_rating = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rating)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
        else:
            if select_genre:
                imdb_score = st.slider("Choose an IMDB score:", min_value=1, max_value=10, step=1)
                number_of_rec = st.slider("How many recommendations do you want?", min_value=5, max_value=20, step=1)
                test_point = [1 if genre in select_genre else 0 for genre in genres]
                test_point.append(imdb_score)
                table = knn_movie_recommender(test_point, number_of_rec)
                c = 0
                st.success("The recommended movies are:")
                for movie, link, ratings in table:
                    c+=1
                    st.markdown(f"({c}) [{movie}]({link})")
                    movie_poster_fetcher(link)
                    director, cast, story, total_rating = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rating)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')

run_recommender()