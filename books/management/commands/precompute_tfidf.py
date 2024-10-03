import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.core.management.base import BaseCommand
from books.models import Book

class Command(BaseCommand):
    help = 'Precompute TF-IDF matrix and cosine similarity for the first 10,000 book descriptions'

    def handle(self, *args, **kwargs):

        # first 10,000 books and create the DataFrame
        books = Book.objects.all().values('id', 'title', 'description')[:10000] 
        df_books = pd.DataFrame(books)
        self.stdout.write('Fetched books from database.')

        # Fill missing descriptions
        df_books['description'] = df_books['description'].fillna('')
        self.stdout.write('Filled missing descriptions.')

        # Computing TF-IDF matrix
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df_books['description'])
        self.stdout.write('Computed the TF-IDF matrix.')

        # Computing cosine similarity matrix
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        self.stdout.write('Computed cosine similarity.')

        # Saving the matrix and DataFrame
        with open('tfidf_matrix_10k.pkl', 'wb') as f:
            pickle.dump(tfidf_matrix, f)
        self.stdout.write('Saved TF-IDF matrix.')

        with open('cosine_sim_matrix_10k.pkl', 'wb') as f:
            pickle.dump(cosine_sim, f)
        self.stdout.write('Saved cosine similarity matrix.')

        with open('df_books_10k.pkl', 'wb') as f:
            pickle.dump(df_books, f)
        self.stdout.write('Saved books DataFrame.')

        self.stdout.write(self.style.SUCCESS('Successfully precomputed and saved TF-IDF and cosine similarity for the first 10,000 books.'))