from django.contrib import admin
from .models import (
    # Core Models
    Book, Author, Publication, Review,
    
    # New Relationship Models
    BookParticipant, Chapter, ChapterContribution,
    
    # Book Format & Pricing Models
    BookFormat, BookImage, PaperSize, PaperQuality, PerPageRate, BindingCost, PricingRule,
    
    # Author History Model
    AuthorHistory,
    Language
)

# --- Inlines for Richer Admin Interfaces ---

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class AuthorHistoryInline(admin.TabularInline):
    """ Allows editing an Author's history directly on the Author page. """
    model = AuthorHistory
    extra = 1  # Show one extra blank row for a new entry
    fields = ('designation', 'organization', 'bio', 'start_date', 'end_date')

class BookParticipantInline(admin.TabularInline):
    """ Allows editing the main authors/editors directly on the Book page. """
    model = BookParticipant
    extra = 1
    autocomplete_fields = ['author'] # Makes selecting authors easier if you have many

class ChapterContributionInline(admin.TabularInline):
    """ Allows editing a chapter's contributors directly on the Chapter page. """
    model = ChapterContribution
    extra = 1
    autocomplete_fields = ['contributor']

class ChapterInline(admin.StackedInline):
    """ Allows editing Chapters directly on the Book page. """
    model = Chapter
    extra = 1
    show_change_link = True # Adds a link to edit the full chapter on its own page

class BookImageInline(admin.TabularInline):
    """ Allows editing Book Images on the Book page. """
    model = BookImage
    extra = 1

class BookFormatInline(admin.TabularInline):
    """ Allows editing Book Formats on the Book page. """
    model = BookFormat
    extra = 1

# --- Custom Admin Panels (ModelAdmin) ---
@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    # This tells Django what to search for when using the autocomplete widget
    search_fields = ['name', 'director'] 
    list_display = ('name', 'director', 'website')

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """ Custom admin for the Author model. """
    inlines = [AuthorHistoryInline]
    list_display = ('__str__', 'author_id', 'is_author_of_the_month', 'is_author_of_the_year')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'author_id')
    
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """ Custom admin for the Chapter model, including its contributors. """
    inlines = [ChapterContributionInline]
    list_display = ('title', 'book', 'order')
    list_filter = ('book',)
    search_fields = ('title', 'book__title')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """ The main, most powerful admin interface for managing a Book. """
    inlines = [
        BookParticipantInline,
        ChapterInline,
        BookFormatInline,
        BookImageInline
    ]
    list_display = ('title', 'isbn', 'is_featured', 'is_book_of_the_month', 'is_book_of_the_year')
    list_filter = ('is_featured', 'publication')
    search_fields = ('title', 'isbn')
    autocomplete_fields = ['publication'] # Easier to select publication

# --- Registering the remaining models with the default admin ---

# admin.site.register(Publication)
admin.site.register(Review)

# It's good practice to register all your models, even the 'through' ones
admin.site.register(BookParticipant)
admin.site.register(ChapterContribution)

# Pricing and Format Models
admin.site.register(PaperSize)
admin.site.register(PaperQuality)
admin.site.register(PerPageRate)
admin.site.register(BindingCost)
admin.site.register(PricingRule)