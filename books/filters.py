import django_filters
from .models import Book

class BookFilter(django_filters.FilterSet):
    # --- Text/ID Based Filters ---
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    isbn = django_filters.CharFilter(field_name='isbn', lookup_expr='icontains')

    # --- Relational Filters ---
    publication = django_filters.NumberFilter(field_name='publication__id')
    category = django_filters.NumberFilter(field_name='categories__id')

    # --- Complex Filters for Authors/Editors ---
    # Search by the Author's name (first or last)
    participant_name = django_filters.CharFilter(method='filter_by_participant_name', label="Search by Author/Editor Name")

    # --- Range Filters ---
    publication_date_after = django_filters.DateFilter(field_name='publication_date', lookup_expr='gte')
    publication_date_before = django_filters.DateFilter(field_name='publication_date', lookup_expr='lte')
    
    pages_min = django_filters.NumberFilter(field_name='pages', lookup_expr='gte')
    pages_max = django_filters.NumberFilter(field_name='pages', lookup_expr='lte')

    # --- Choice Filter for Book Type ---
    book_type = django_filters.ChoiceFilter(
        choices=(('authored', 'Authored'), ('edited', 'Edited')),
        method='filter_by_book_type',
        label='Book Type (Authored/Edited)'
    )

    class Meta:
        model = Book
        # List only the fields that are being used for exact matches or simple lookups
        fields = []

    # --- Custom Filter Methods ---
    def filter_by_participant_name(self, queryset, name, value):
        # This allows searching for a book if any of its authors' or editors' names contain the value
        # The .distinct() call should be at the very end.
        return (queryset.filter(
            bookparticipant__author__user__first_name__icontains=value
        ) | queryset.filter(
            bookparticipant__author__user__last_name__icontains=value
        )).distinct()

    def filter_by_book_type(self, queryset, name, value):
        if value == 'authored':
            return queryset.filter(bookparticipant__role='author').distinct()
        if value == 'edited':
            return queryset.filter(bookparticipant__role='editor').distinct()
        return queryset