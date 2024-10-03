import ijson
import json
from django.core.management.base import BaseCommand
from books.models import Book, Author
from django.db import transaction

class Command(BaseCommand):
    help = 'This is made to load books from the books.json file'

    def handle(self, *args, **kwargs):
        file_paths = {
            'books': '/Users/luisfaria/Downloads/archive/books.json/books.json',
        }
        batch_size = 1000

        # Process books.json
        print("Starting to process books.json...")
        self.process_file(file_paths['books'], self.process_book, batch_size)

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

    def process_book(self, book_data, batch):
        try:
            # Ensure required fields are present
            if not book_data.get('work_id') or not book_data.get('author_id'):
                self.stdout.write(f"Missing work_id or author_id for book: {book_data.get('title', 'Unknown title')}")
                return

            # Extract and process the authors
            primary_author = Author.objects.filter(id=book_data.get('author_id')).first()
            if not primary_author:
                self.stdout.write(f"Primary author not found for book: {book_data.get('title', 'Unknown title')}")
                return

            # Handle empty or invalid num_pages field
            num_pages = book_data.get('num_pages', 0)
            if num_pages == '' or num_pages is None:
                num_pages = 0  # Default to 0 if empty

            # Create the book entry
            book, created = Book.objects.get_or_create(
                work_id=book_data.get('work_id'),
                defaults={
                    'title': book_data.get('title', 'No Title'),
                    'author': primary_author,
                    'book_id': book_data.get('id'),
                    'isbn': book_data.get('isbn', ''),
                    'isbn13': book_data.get('isbn13', ''),
                    'average_rating': book_data.get('average_rating', 0.0),
                    'ratings_count': book_data.get('ratings_count', 0),
                    'publication_date': book_data.get('publication_date', ''),
                    'num_pages': num_pages,  # Ensuring valid num_pages
                    'language': book_data.get('language', ''),
                    'description': book_data.get('description', ''),
                }
            )
            if created:
                batch.append(book)
                self.stdout.write(f"Processed book: {book.title}")
        except Exception as e:
            self.stdout.write(f"Error processing book: {e}")

    @transaction.atomic
    def save_batch(self, batch):
        if isinstance(batch[0], Book):
            Book.objects.bulk_create(batch, ignore_conflicts=True)
        print(f"Batch of {len(batch)} books saved successfully.")