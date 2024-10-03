import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from books.models import UserFavorites

# Books DataFrame
books = pd.read_csv('BX-Books.csv', sep=';', error_bad_lines=False, encoding="latin-1")

def get_user_favorites(user_id):
    # Geting user favorites if there's any

    user_favorites = UserFavorites.objects.filter(user=user_id).first()
    if user_favorites:
        favorite_books = user_favorites.favorites.all()
        return [book.id for book in favorite_books]
    return []

# Function to recommend books
# Hybrid Approach: Combines both the author and description. 
def recommended_books(user_favorites, books, top_n=5):
    # Combine all favorite books descriptions
    favorite_books = books[books['id'].isin(user_favorites)]

    if favorite_books.empty:
        return 'No recommendations found'

    # Creating a TfidfVectorizer to convert text to vectors
    # This transforms the descriptions into a vector space where the 
    # importance of words is measured by how unique they are across all books.
    
    tfidf = TfidfVectorizer(stop_words='english')
    book_desc_matrix = tfidf.fit_transform(favorite_books['description'])

    # Calculating cosine similarity
    # Measures the similarity between the favorite books 
    # and all others based on their description.
    desc_similarity = cosine_similarity(book_desc_matrix)

    # Creating empty recommendation list
    recommended_books = []

    # For each fav book, get the most similar books
    for book_id in user_favorites:
        book_idx = books[books['id'] == book_id].index[0]
        similar_books = list(enumerate(desc_similarity[book_idx]))

        # Sort books by similarity scode (excluding the book itself)
        similar_books = sorted(similar_books, key=lambda x: x[1], reverse=True)[1:]

        # Collect similar books based on their descr
        for sim_book in similar_books:
            book_idx = sim_book[0]
            if books.iloc[book_idx]['id'] not in user_favorites and books.iloc[book_idx]['id'] not in recommended_books:
                recommended_books.append(books.iloc[book_idx]['id'])
                
                if len(recommended_books) >= top_n:
                    break

    return books[books['id'].isin(recommended_books)][['id', 'title', 'author']]

# Example of fav books
user_favorites = get_user_favorites(1)

# Get recommendations
recommendations = recommended_books(user_favorites, books)
print(recommendations)