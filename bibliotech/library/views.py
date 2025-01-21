from datetime import timezone, timedelta
from sqlite3 import IntegrityError

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView, CreateView

from .models import (
    Book,
    Borrowing,
    Category,
    Review,
    Reservation
)

#Vues de base
class HomeView(TemplateView):
    template_name = 'library/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_books'] = Book.objects.all().order_by('-added_date')[:5]
        return context

#Vues liees aux livres
class BookListView(ListView):
    model = Book
    template_name = 'library/book_list.html'
    context_object_name = 'books'
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter les catégories et la catégorie sélectionnée
        context['categories'] = Category.objects.all()
        # Garder la catégorie sélectionnée
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_availability'] = self.request.GET.get('available', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)|
                Q(author__icontains=search_query)|
                Q(isbn__icontains=search_query)
            )

        # Récupérer la catégorie depuis l'URL
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        availability = self.request.GET.get('available')
        if availability == 'yes':
            queryset = queryset.filter(available_copies__gt=0)
        elif availability == 'no':
            queryset = queryset.filter(available_copies=0)

        return queryset




class BookDetailView(DetailView):
    model = Book
    template_name = 'library/book_detail.html'
    context_object_name ='book'

    def get_queryset(self):
        return Book.objects.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all().order_by('-created_at')
        context['borrowing_history'] = Borrowing.objects.filter(
            book = self.object
        ).order_by('-borrowed_date')

        if self.request.user.is_authenticated:
            context['user_has_borrowed'] = Borrowing.objects.filter(
                user = self.request.user,
                book =self.object,
                returned = False
            ).exists()
            context['user_review'] = Review.objects.filter(
                user = self.request.user,
                book = self.object
            ).first()

            if self.request.user.is_authenticated:
                context['user_has_reservation'] = Reservation.objects.filter(
                    user=self.request.user,
                    book= self.object,
                    is_active=True
                ).exists()
                context['reservation_count'] = Reservation.objects.filter(
                    book= self.object,
                    is_active=True
                ).count()
        return context


#Vues liees aux emprunts
class MyBorrowingsView(LoginRequiredMixin, ListView):
    model = Borrowing
    template_name = 'library/my_borrowings.html'
    context_object_name = 'borrowings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

    def get_queryset(self):
        return Borrowing.objects.filter(
            user = self.request.user,
            returned = False
        ).select_related('book').order_by('return_date')




class BorrowBookView(LoginRequiredMixin, View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)

        if book.available_copies <= 0:
            messages.error(request, "Ce livre n'est pas disponible actuellement.")
            return redirect('book_detail', pk=pk)

        if Borrowing.objects.filter(user = request.user, book=book, returned=False).exists():
            messages.warning(request, "Vous avez deja emprunter ce livre.")
            redirect('book_detail', pk=pk)

        return_date = timezone.now() + timedelta(days=14)
        Borrowing.objects.create(
            user = request.user,
            book = book,
            return_date = return_date
        )

        book.available_copies -= 1
        book.save()

        messages.success(request, f"Vous avez emprunter '{book.title}'. A retourner avent le {return_date.date()}" )
        return redirect('my_borrowings')

class ReturnBookView(LoginRequiredMixin, View):
    def post(self, request, borrow_id):
        borrowing = get_object_or_404(Borrowing, id=borrow_id, user=request.user)

        if borrowing.returned:
            messages.warning(request, "Ce livre a deja etait retourner")
        else:
            borrowing.returned = True
            borrowing.save()

        book = borrowing.book
        book.available_copies += 1
        book.save()

        messages.success(request, f"Merci d'avoir retourne '{book.title}'.")
        return redirect('my_borrowings')

#Vues liees aux reservations
class MyReservationsView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'library/my_reservations.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user,
            is_active=True
        )


class ReservationBookView(LoginRequiredMixin, View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)

        if Borrowing.objects.filter(user=request.user, book=book, returned=False).exists():
            messages.warning(request, "Vous avez deja emprunter ce livre.")
            return redirect('book_detail', pk=pk)

        existing_reservation = Reservation.objects.filter(
            user = request.user,
            book=book
        ).first()

        if existing_reservation:
            if existing_reservation.is_active:
                messages.warning(request,"Vous avez deja rserver ce livre.")
            else:
                existing_reservation.is_active = True
                existing_reservation.reservation_date = timezone.now()
                existing_reservation.save()
                messages.success(request, f"Vous avez reserver '{ book.title }.Vous serez notifié quand il sera disponible.")

        else:
            Reservation.objects.create(user=request.user, book=book)
            messages.success(request, f"Vous avez reserver '{book.title}'.Vous serez notifier quand il sera disponible.")

        return redirect('book_detail', pk=pk)


class CancelReservationView(LoginRequiredMixin, View):
    def post(self, request, reservation_id):
        reservation = get_object_or_404(Reservation,user=request.user,id=reservation_id,is_active=True)

        reservation.is_active=False
        reservation.save()

        messages.success(request,f"Votre reservation pour '{reservation.book.title}'a etait annuler")
        return redirect('my_reservations')

#Vues liees aux reviews
class AddReviewView(LoginRequiredMixin, CreateView):
    model = Review
    fields = ['rating', 'comment']
    template_name = 'library/add_review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = get_object_or_404(Book, pk=self.kwargs['book_id'])
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.book_id = self.kwargs['book_id']
        try:
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, "Vous avez déjà évalué ce livre.")
            return redirect('book_detail', pk=self.kwargs['book_id'])

    def get_success_url(self):
        return reverse_lazy('book_detail', kwargs={'pk': self.kwargs['book_id']})

#Vues d'authentification
class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Inscription reussie ! Vous pouvez maintenant vous connectez.")
        return response

#Vues d'administration
class LibrarianDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'library/librarian_dashboard.html'

    def test_func(self):
        return self.request.user.is_staff  # Seuls les bibliothécaires peuvent accéder

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Emprunts en retard
        context['overdue_borrowings'] = Borrowing.objects.filter(
            returned=False,
            return_date__lt=timezone.now()
        ).select_related('user', 'book')

        # Réservations en attente
        context['active_reservations'] = Reservation.objects.filter(
            is_active=True
        ).select_related('user', 'book')

        # Statistiques
        context['total_books'] = Book.objects.count()
        context['books_out'] = Borrowing.objects.filter(returned=False).count()
        context['total_users'] = User.objects.count()
        context['total_borrowings'] = Borrowing.objects.count()

        return context






#Vues de test/debug
class TestMessagesView(View):
    def get(self,request):
        messages.debug(request, "Ceci est un message de debug")
        messages.info(request, "Information : La bibliothèque ferme à 18h")
        messages.success(request, "Super ! Votre livre a été emprunté avec succès")
        messages.warning(request, "Attention : Vous avez un livre en retard")
        messages.error(request, "Erreur : Ce livre n'est pas disponible")

        return redirect('home')


















