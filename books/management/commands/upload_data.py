import csv
from django.core.management.base import BaseCommand
from django.utils import timezone
from books.models import Book, Author, Publication, Chapter, BookParticipant, ChapterContribution
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Uploads book and author data from a CSV file'

    def handle(self, *args, **kwargs):
        # The path to your CSV file, relative to manage.py
        csv_file_path = 'Candidate.csv'
        self.stdout.write(self.style.SUCCESS(f"Starting data upload from {csv_file_path}..."))

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # --- Get or Create Publication ---
                publication_name = row['Publication Name'].strip()
                publication, created = Publication.objects.get_or_create(name=publication_name)
                if created:
                    self.stdout.write(f"Created new Publication: {publication.name}")

                # --- Get or Create Book ---
                book_title = row['Book Title'].strip()
                isbn = row['ISBN No.'].strip()
                
                # We use 'defaults' to provide data only if the book is being created
                book, created = Book.objects.get_or_create(
                    isbn=isbn,
                    defaults={
                        'title': book_title,
                        'publication': publication,
                        'pages': 0, # Default value, can be updated later
                        'publication_date': timezone.now().date() # Placeholder date
                    }
                )
                if created:
                    self.stdout.write(f"Created new Book: {book.title}")
                
                # --- Get or Create Author/User ---
                candidate_name = row['Candidate Name'].strip()
                first_name = candidate_name.split(' ')[0]
                last_name = ' '.join(candidate_name.split(' ')[1:]) if ' ' in candidate_name else ''
                designation = row['Candidate Designation'].strip()
                organization = row['University'].strip()
                
                # We create a unique username based on the name to avoid conflicts
                unique_username = f"{first_name.lower()}{last_name.lower().replace(' ', '')}"
                
                user, user_created = CustomUser.objects.get_or_create(
                    username=unique_username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'author' # We assume everyone is an author for now
                    }
                )

                author, author_created = Author.objects.get_or_create(
                    user=user
                )
                if author_created:
                    self.stdout.write(f"Created new Author: {user.get_full_name()}")

                # --- Handle Roles (Author, Editor, Contributor) ---
                role = row['Candidate Title'].strip()
                chapter_name = row['Chapter Name'].strip()

                if role.lower() in ['author', 'editor']:
                    # This person is a main participant of the book
                    BookParticipant.objects.get_or_create(
                        book=book,
                        author=author,
                        role=role.lower()
                    )
                
                elif role.lower() == 'contributor' and chapter_name and chapter_name.lower() != 'nil':
                    # This person is a contributor to a specific chapter
                    chapter, chapter_created = Chapter.objects.get_or_create(
                        book=book,
                        title=chapter_name
                    )
                    
                    ChapterContribution.objects.get_or_create(
                        chapter=chapter,
                        contributor=author
                    )

        self.stdout.write(self.style.SUCCESS("Data upload completed successfully!"))