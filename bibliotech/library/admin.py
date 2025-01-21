from django.contrib import admin
from .models import Category, Book, Borrowing, Review, Reservation


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','description')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author','category', 'available_copies', 'isbn')
    list_filter = ('category', 'available_copies')
    search_fields = ('title', 'author', 'isbn')

@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'borrowed_date', 'return_date', 'returned')
    list_filter = ('returned', 'borrowed_date')
    search_fields = ('user__username', 'book__title')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book_title', 'user_username')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'reservation_date', 'is_active', 'notified')
    list_filter = ('is_active', 'notified', 'reservation_date')
    search_fields = ('user__username', 'book__title')
    date_hierarchy = 'reservation_date'
