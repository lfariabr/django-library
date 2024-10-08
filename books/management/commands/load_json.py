import ijson
import json
from django.core.management.base import BaseCommand
from books.models import Book, Author
from django.db import transaction

class Command(BaseCommand):
    help = 'This will load authors, books, series, and lists from large JSON files'

    def handle(self, *args, **kwargs):
        file_paths = {
            'authors': '/Users/luisfaria/Downloads/archive/authors.json/authors.json',
            'books': '/Users/luisfaria/Downloads/archive/books.json/books.json',
            'series': '/Users/luisfaria/Downloads/archive/series.json/series.json',
            'lists': '/Users/luisfaria/Downloads/archive/list.json/list.json',
        }
        batch_size = 1000

        # Process authors.json
        # print("Starting to process authors.json...")
        # self.process_file(file_paths['authors'], self.process_author, batch_size)

        # Process books.json
        print("Starting to process books.json...")
        self.process_file(file_paths['books'], self.process_book, batch_size)

        # Process series.json
        print("Starting to process series.json...")
        self.process_file(file_paths['series'], self.process_series, batch_size)

        # Process list.json
        print("Starting to process list.json...")
        self.process_file(file_paths['lists'], self.process_list, batch_size)

    def process_file(self, file_path, process_func, batch_size):
        batch = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())  # Parse each line separately
                    process_func(obj, batch)

                    if len(batch) >= batch_size:
                        self.save_batch(batch)
                        print(f"Saved a batch of {batch_size} items.")
                        batch.clear()

                except json.JSONDecodeError as e:
                    self.stderr.write(f"Skipping line due to error: {e}")

            if batch:
                self.save_batch(batch)
                print(f"Saved the last batch of {len(batch)} items.")

    # def process_author(self, author_data, batch):
    #     author, created = Author.objects.get_or_create(
    #         id=author_data.get('id'),
    #         defaults={
    #             'name': author_data.get('name'),
    #             'ratings_count': author_data.get('ratings_count', 0),
    #             'average_rating': author_data.get('average_rating', 0.0),
    #             'text_reviews_count': author_data.get('text_reviews_count', 0),
    #             'works_count': author_data.get('works_count', 0),
    #             'image_url': author_data.get('image_url', ''),
    #             'about': author_data.get('about', ''),
    #             'fans_count': author_data.get('fans_count', 0),
    #         }
    #     )
    #     if created:
    #         batch.append(author)
    #     print(f"Processed author: {author.name}")

    def process_book(self, book_data, batch):
        try:
            # Ensure required fields are present
            if not book_data.get('work_id') or not book_data.get('author_id'):
                self.stdout.write(f"Missing work_id or author_id for book: {book_data.get('title', 'Unknown title')}")
                return  # Skip the book if required fields are missing

            # Extract and process the authors
            authors = book_data.get('authors', [])
            if authors:
                primary_author_id = book_data.get('author_id')
                primary_author = Author.objects.filter(id=primary_author_id).first()
                if not primary_author:
                    self.stdout.write(f"Primary author not found for book: {book_data.get('title', 'Unknown title')}")
                    return

            # Create the book entry
            book, created = Book.objects.get_or_create(
                work_id=book_data.get('work_id'),
                defaults={
                    'title': book_data.get('title', 'No Title'),
                    'author': primary_author,
                    'book_id': book_data.get('id'),  # Use `id` from the JSON as the book_id
                    'isbn': book_data.get('isbn', ''),
                    'isbn13': book_data.get('isbn13', ''),
                    'average_rating': book_data.get('average_rating', 0.0),
                    'ratings_count': book_data.get('ratings_count', 0),
                    'publication_date': book_data.get('publication_date', ''),
                    'num_pages': book_data.get('num_pages', 0),
                    'language': book_data.get('language', ''),
                    'description': book_data.get('description', ''),
                }
            )
            if created:
                batch.append(book)
                self.stdout.write(f"Processed book: {book.title}")
        except Exception as e:
            self.stdout.write(f"Error processing book: {e}")

    def process_series(self, series_data, batch):
        pass

    def process_list(self, list_data, batch):
        pass

    # @transaction.atomic
    # def save_batch(self, batch):
    #     if isinstance(batch[0], Author):
    #         Author.objects.bulk_create(batch, ignore_conflicts=True)
    #     elif isinstance(batch[0], Book):
    #         Book.objects.bulk_create(batch, ignore_conflicts=True)

    @transaction.atomic
    def save_batch(self, batch):
        if isinstance(batch[0], Book):
            Book.objects.bulk_create(batch, ignore_conflicts=True)
        print(f"Batch of {len(batch)} books saved successfully.")