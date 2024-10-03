import os
import django
import pandas as pd
from django.core.management.base import BaseCommand
from books.models import Author, Book
import numpy as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

class Command(BaseCommand):
    help = 'Run ML analysis on book data'

# Loading authors data from db to df
    def load_authors_from_db():
        authors = Author.objects.all().values()
        df_authors = pd.DataFrame(authors)
        return df_authors

    # Loading books data from db to df
    def load_books_from_db():
        books = Book.objects.all().values()
        df_books = pd.DataFrame(books)
        return df_books

    # Load the data
    print("Loading authors from database...")
    df_authors = load_authors_from_db()
    print(df_authors.head())

    print("Loading books from database...")
    df_books = load_books_from_db()
    print(df_books.head())


    # Fill missing descriptions with empty strings
df_books['description'] = df_books['description'].fillna('')

# Create the TF-IDF matrix from book descriptions
tfid = TfidfVectorizer(stop_words='english')
tfid_matrix = tfid.fit_transform(df_books['description'])

# Compute the cosine similarity matrix
cosine_sim = linear_kernel(tfid_matrix, tfid_matrix)

# Create a Series that maps book titles to DataFrame indices
indices = pd.Series(df_books.index, index=df_books['title']).drop_duplicates()

# Define the recommendation function
def get_recommendations(title, cosine_sim=cosine_sim):
    # Find the index of the book that matches the title
    idx = indices[title]

    # Get the pairwise similarity scores of all books with that book
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the books based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the indices of the top 5 most similar books
    sim_scores = sim_scores[1:6]

    # Get the book indices
    sim_index = [i[0] for i in sim_scores]

    # Return the titles of the top 5 similar books
    return df_books['title'].iloc[sim_index]
