from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# Create your views here.
from .models import Book, Author, BookInstance, Genre
from django.contrib.auth.decorators import permission_required

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse, reverse_lazy
import datetime
from django.utils.translation import gettext_lazy as _

from .forms import RenewBookForm
def index(request):
    """
    View function for home page of site.
    """
    # Generate counts of some of the main objects
    num_books=Book.objects.all().count()
    num_instances=BookInstance.objects.all().count()
    # Available books (status = 'a')
    num_instances_available=BookInstance.objects.filter(status__exact='a').count()
    num_authors=Author.objects.count()  # The 'all()' is implied by default.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_books':num_books,'num_instances':num_instances,'num_instances_available':num_instances_available,'num_authors':num_authors,
            'num_visits':num_visits}, # num_visits appended
    )

'''
class BookListView(generic.ListView):
    model = Book
    # paginate_by = 10
    # context_object_name = 'my_book_list'  # your own name for the list as a template variable
    # queryset = Book.objects.filter(title__icontains='war')[:5]  # Get 5 books containing the title war
    # template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location
    def get_queryset(self):
        return Book.objects.filter(title__icontains='war')[:5]  # Get 5 books containing the title war
'''
class BookListView(generic.ListView):
    model = Book
    paginate_by = 5 # 添加这行，只要你有超过5条记录，视图就会开始对它发送到模板的数据，进行分页

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BookListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context

class BookDetailView(generic.DetailView):
    model = Book


class Http404:
    pass


def book_detail_view(request,pk):
    try:
        book_id=Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        raise Http404("Book does not exist")

    #book_id=get_object_or_404(Book, pk=pk)

    return render(
        request,
        'catalog/book_detail.html',
        context={'book':book_id,}
    )

class AuthorListView(generic.ListView):
    """
    Generic class-based view for a list of authors.
    """
    model = Author
    paginate_by = 5 # 可以根据需要调整每页显示的作者数量


class AuthorDetailView(generic.DetailView):
    """
    Generic class-based detail view for an author.
    """
    model = Author
    paginate_by = 5

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class BorrowedBooksListView(generic.ListView, PermissionRequiredMixin):
    """Generic class-based view listing all borrowed books.
    Only visible to users with can_mark_returned permission."""
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_librarian.html'
    paginate_by = 10

    def get_queryset(self):
        # Filter by book instances that are not available
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    # Manual permission check
    if not request.user.has_perm('catalog.can_mark_returned'):
        return HttpResponseForbidden("You do not have permission to renew books.")

    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )
        else:
            # If form is not valid, render the template with the form and errors
            return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    # Render the template for GET requests
    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})

class AuthorCreate(generic.CreateView):
    model = Author
    fields = '__all__'

class AuthorUpdate(generic.UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorDelete(generic.DeleteView):
    model = Author
    success_url = reverse_lazy('authors')

class BookCreate(generic.CreateView):
    model = Book
    fields = '__all__'

class BookUpdate(generic.UpdateView):
    model = Book
    fields = '__all__' # Or specify a list of fields like for AuthorUpdate

class BookDelete(generic.DeleteView):
    model = Book
    success_url = reverse_lazy('books') # Redirect to the book list after deletion
