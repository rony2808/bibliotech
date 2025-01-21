from xml.etree.ElementInclude import include

from django.urls import path, include
from . import views
from .views import RegisterView
from django.contrib.auth.views import LogoutView

urlpatterns =[
    path('', views.HomeView.as_view(), name='home'),
    path('book/', views.BookListView.as_view(), name='book_list'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('my-borrowings/', views.MyBorrowingsView.as_view(), name='my_borrowings'),
    path('book/<int:pk>/borrow/', views.BorrowBookView.as_view(), name='borrow_book'),
    path('borrowing/<int:borrow_id>/return', views.ReturnBookView.as_view(), name='return_book'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('test-messages/', views.TestMessagesView.as_view(), name='test_messages'),
    path('book/<int:book_id>/add-review/', views.AddReviewView.as_view(), name='add_review'),
    path('book/<int:pk>/reserve/',views.ReservationBookView.as_view(), name="reserve_book"),
    path('my-reservations/',views.MyReservationsView.as_view(), name="my_reservations"),
    path('accounts/register/', RegisterView.as_view(), name="register"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('reservation/<int:reservation_id>/cancel/', views.CancelReservationView.as_view(), name="cancel_reservation"),
path('librarian-dashboard/', views.LibrarianDashboardView.as_view(), name='librarian_dashboard'),
]