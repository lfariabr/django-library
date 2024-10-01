import json
from django.core.management.base import BaseCommand
from books.models import Book, Author

class Command(BaseCommand):
    help = 'This will load authors and their related books from a large JSON file'

    def handle(self, *args, **kwargs):
        file_path = '/Users/luisfaria/Library/CloudStorage/GoogleDrive-lfariabr@gmail.com/My Drive/LUIS/WORK/18digital/pro-corpo/Lab Programação/dev/library/books/books.json'
        # line_limit = 10  # Limit the number of lines for testing
        line_count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Stop after processing the limit
                # if line_count >= line_limit:
                #     break

                # Each line is a separate JSON object representing an author
                author_data = json.loads(line)
                self.process_author(author_data)

                line_count += 1
    
    def process_author(self, author_data):
        # Process author's details
        author, created = Author.objects.get_or_create(
            id=author_data.get('id'),  
            defaults={
                'name': author_data.get('name'),
                'ratings_count': author_data.get('ratings_count', 0),  # Default value if missing
                'average_rating': author_data.get('average_rating', 0.0),  # Default value if missing
                'text_reviews_count': author_data.get('text_reviews_count', 0),
                'works_count': author_data.get('works_count', 0),
                'image_url': author_data.get('image_url', ''),
                'about': author_data.get('about', ''),
                'fans_count': author_data.get('fans_count', 0),
            }
        )

        # Process related books
        for work_id, book_id in zip(author_data.get('work_ids', []), author_data.get('book_ids', [])):
            Book.objects.get_or_create(
                work_id=work_id,  # work_id from the author's data
                defaults={
                    'author': author,
                    'book_id': book_id,
                    'title': f"Book with work_id {work_id}",  # Placeholder title (change this if you have titles)
                }
            )

        # Log the processed author
        self.stdout.write(f'Processed author: {author.name}')