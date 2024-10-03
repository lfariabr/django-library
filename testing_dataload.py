import os
import django
import pandas as pd
from books.models import Author, Book
from django.conf import settings
settings.configure()

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.library.settings')
django.setup()

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
df_authors = load_authors_from_db()
df_books = load_books_from_db()

# Display first rows to check
print(df_authors.head())
print(df_books.head())