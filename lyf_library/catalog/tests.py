from django.test import TestCase
from catalog.models import Author, Book, Genre, BookInstance
from django.urls import reverse
import datetime
from django.contrib.auth.models import User
from django.test import Client
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from catalog.forms import RenewBookForm

# Create your tests here.

class AuthorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        Author.objects.create(first_name='Big', last_name='Bob')

    def test_first_name_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('first_name').verbose_name
        self.assertEqual(field_label, 'first name')

    def test_date_of_death_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('date_of_death').verbose_name
        self.assertEqual(field_label, 'Died')

    def test_first_name_max_length(self):
        author = Author.objects.get(id=1)
        max_length = author._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 100)

    def test_object_name_is_last_name_comma_first_name(self):
        author = Author.objects.get(id=1)
        expected_object_name = f'{author.last_name}, {author.first_name}'
        self.assertEqual(str(author), expected_object_name)

    def test_get_absolute_url(self):
        author = Author.objects.get(id=1)
        # This will also fail if the urlconf is not defined.
        self.assertEqual(author.get_absolute_url(), '/catalog/author/1')


class BookModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        author = Author.objects.create(first_name='Big', last_name='Bob')
        genre = Genre.objects.create(name='Fiction')
        book = Book.objects.create(
            title='Test Book',
            author=author,
            summary='This is a test book summary.',
            isbn='1234567890123'
        )
        book.genre.add(genre)

    def test_title_label(self):
        book = Book.objects.get(id=1)
        field_label = book._meta.get_field('title').verbose_name
        self.assertEqual(field_label, 'title')

    def test_author_label(self):
        book = Book.objects.get(id=1)
        field_label = book._meta.get_field('author').verbose_name
        self.assertEqual(field_label, 'author')

    def test_title_max_length(self):
        book = Book.objects.get(id=1)
        max_length = book._meta.get_field('title').max_length
        self.assertEqual(max_length, 200)

    def test_summary_max_length(self):
        book = Book.objects.get(id=1)
        max_length = book._meta.get_field('summary').max_length
        self.assertEqual(max_length, 1000)

    def test_isbn_max_length(self):
        book = Book.objects.get(id=1)
        max_length = book._meta.get_field('isbn').max_length
        self.assertEqual(max_length, 13)

    def test_object_name_is_title(self):
        book = Book.objects.get(id=1)
        expected_object_name = book.title
        self.assertEqual(str(book), expected_object_name)

    def test_get_absolute_url(self):
        book = Book.objects.get(id=1)
        self.assertEqual(book.get_absolute_url(), '/catalog/book/1')

    def test_display_genre(self):
        book = Book.objects.get(id=1)
        expected_genre = ', '.join([genre.name for genre in book.genre.all()[:3]])
        self.assertEqual(book.display_genre(), expected_genre)

class GenreModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Genre.objects.create(name='Fantasy')

    def test_name_label(self):
        genre = Genre.objects.get(id=1)
        field_label = genre._meta.get_field('name').verbose_name
        self.assertEqual(field_label, 'name')

    def test_name_max_length(self):
        genre = Genre.objects.get(id=1)
        max_length = genre._meta.get_field('name').max_length
        self.assertEqual(max_length, 200)

    def test_object_name_is_name(self):
        genre = Genre.objects.get(id=1)
        expected_object_name = genre.name
        self.assertEqual(str(genre), expected_object_name)

class BookInstanceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(first_name='Big', last_name='Bob')
        book = Book.objects.create(
            title='Test Book',
            author=author,
            summary='This is a test book summary.',
            isbn='1234567890123'
        )
        # Create a BookInstance
        BookInstance.objects.create(
            book=book,
            imprint='Test Imprint',
            due_back=datetime.date.today() + datetime.timedelta(weeks=3),
            status='o'
        )

    def test_imprint_label(self):
        book_instance = BookInstance.objects.get(id__contains='') # Assuming UUIDField, so get any instance
        field_label = book_instance._meta.get_field('imprint').verbose_name
        self.assertEqual(field_label, 'imprint')

    def test_due_back_label(self):
        book_instance = BookInstance.objects.get(id__contains='')
        field_label = book_instance._meta.get_field('due_back').verbose_name
        self.assertEqual(field_label, 'due back')

    def test_status_label(self):
        book_instance = BookInstance.objects.get(id__contains='')
        field_label = book_instance._meta.get_field('status').verbose_name
        self.assertEqual(field_label, 'status')

    def test_status_max_length(self):
        book_instance = BookInstance.objects.get(id__contains='')
        max_length = book_instance._meta.get_field('status').max_length
        self.assertEqual(max_length, 1)

    def test_object_name_is_book_title_and_id(self):
        book_instance = BookInstance.objects.get(id__contains='')
        expected_object_name = f'{book_instance.id} ({book_instance.book.title})'
        self.assertEqual(str(book_instance), expected_object_name)

    def test_is_overdue_property(self):
        book_instance = BookInstance.objects.get(id__contains='')
        # Set due_back date to past for testing overdue
        book_instance.due_back = datetime.date.today() - datetime.timedelta(days=1)
        self.assertTrue(book_instance.is_overdue)

    def test_is_not_overdue_property(self):
        book_instance = BookInstance.objects.get(id__contains='')
        # Set due_back date to future for testing not overdue
        book_instance.due_back = datetime.date.today() + datetime.timedelta(days=1)
        self.assertFalse(book_instance.is_overdue)

class RenewBookListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 4 users
        cls.test_user1 = User.objects.create_user(username='testuser1', password='12345')
        cls.test_user2 = User.objects.create_user(username='testuser2', password='12345')
        cls.test_user3 = User.objects.create_user(username='testuser3', password='12345')
        cls.test_user4 = User.objects.create_user(username='testuser4', password='12345')

        # Create a Book for instances
        author = Author.objects.create(first_name='Big', last_name='Bob')
        book = Book.objects.create(
            title='Test Book',
            author=author,
            summary='This is a test book summary.',
            isbn='1234567890123'
        )

        # Create 4 BookInstances
        BookInstance.objects.create(book=book, imprint='Imprint 1', due_back=datetime.date.today() - datetime.timedelta(weeks=1), status='o', borrower=cls.test_user1)
        BookInstance.objects.create(book=book, imprint='Imprint 2', due_back=datetime.date.today() + datetime.timedelta(weeks=1), status='o', borrower=cls.test_user2)
        BookInstance.objects.create(book=book, imprint='Imprint 3', due_back=datetime.date.today() + datetime.timedelta(weeks=2), status='o', borrower=cls.test_user3)
        BookInstance.objects.create(book=book, imprint='Imprint 4', due_back=datetime.date.today() + datetime.timedelta(weeks=3), status='o', borrower=cls.test_user4)

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='12345')
        response = self.client.get(reverse('my-borrowed'))
        # Check that we got a 200 response
        self.assertEqual(response.status_code, 200)
        # Check that the correct template was used
        self.assertTemplateUsed(response, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_are_listed(self):
        login = self.client.login(username='testuser1', password='12345')
        response = self.client.get(reverse('my-borrowed'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('bookinstance_list' in response.context)
        self.assertEqual(len(response.context['bookinstance_list']), 1)
        self.assertEqual(response.context['bookinstance_list'][0].borrower.username, 'testuser1')

class RenewBookFormTest(TestCase):
    def test_form_date_field_label(self):
        form = RenewBookForm()
        self.assertTrue(form.fields['renewal_date'].label == None or form.fields['renewal_date'].label == 'renewal date')

    def test_form_date_field_help_text(self):
        form = RenewBookForm()
        self.assertEqual(form.fields['renewal_date'].help_text,
            'Enter a date between now and 4 weeks (default 3).')

    def test_form_date_in_past(self):
        form = RenewBookForm(data={'renewal_date': datetime.date.today() - datetime.timedelta(days=1)})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['renewal_date'], ['Invalid date - renewal in past'])

    def test_form_date_too_far_future(self):
        form = RenewBookForm(data={'renewal_date': datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['renewal_date'], ['Invalid date - renewal more than 4 weeks ahead'])

    def test_form_date_today(self):
        form = RenewBookForm(data={'renewal_date': datetime.date.today()})
        self.assertTrue(form.is_valid())

    def test_form_date_max(self):
        form = RenewBookForm(data={'renewal_date': datetime.date.today() + datetime.timedelta(weeks=4)})
        self.assertTrue(form.is_valid())


class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    @classmethod
    def setUpTestData(cls):
        # Create a librarian user
        cls.test_librarian = User.objects.create_user(username='testlibrarian', password='123')
        cls.test_librarian.is_staff = True
        # Get the 'can_mark_returned' permission
        content_type = ContentType.objects.get_for_model(BookInstance)
        can_mark_returned_permission = Permission.objects.get(
            content_type=content_type,
            codename='can_mark_returned'
        )
        # Assign the permission to the librarian user
        cls.test_librarian.user_permissions.add(can_mark_returned_permission)
        cls.test_librarian.save()

        # Create a regular user
        cls.test_user = User.objects.create_user(username='testuser', password='123')

        # Create a book and instance for testing renewal
        author = Author.objects.create(first_name='Big', last_name='Bob')
        book = Book.objects.create(
            title='Test Book',
            author=author,
            summary='This is a test book summary.',
            isbn='1234567890123'
        )
        cls.test_bookinstance1 = BookInstance.objects.create(
            book=book,
            imprint='Test Imprint',
            due_back=datetime.date.today() + datetime.timedelta(weeks=3),
            status='o',
            borrower=cls.test_user
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_if_logged_in_but_not_librarian(self):
        login = self.client.login(username='testuser', password='123')
        response = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 403)

    # Note: The following tests assume the user has the 'can_mark_returned' permission.
    # You would typically grant this permission to your librarian test user in setUpTestData.
    # For simplicity here, we'll assume the librarian user already has it.

    def test_librarian_can_access_renewal_page_get(self):
        login = self.client.login(username='testlibrarian', password='123')
        response = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/book_renew_librarian.html')

    def test_librarian_can_renew_book_post_valid_date(self):
        login = self.client.login(username='testlibrarian', password='123')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        response = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}), {'renewal_date': valid_date_in_future})
        self.assertRedirects(response, reverse('all-borrowed')) # Assuming redirect to all-borrowed after success

    def test_librarian_cannot_renew_book_post_invalid_date_past(self):
        login = self.client.login(username='testlibrarian', password='123')
        date_in_past = datetime.date.today() - datetime.timedelta(days=1)
        response = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}), {'renewal_date': date_in_past})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        # Manually check form errors instead of using assertFormError
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('renewal_date', form.errors)
        self.assertIn('Invalid date - renewal in past', form.errors['renewal_date'])

    def test_librarian_cannot_renew_book_post_invalid_date_future(self):
        login = self.client.login(username='testlibrarian', password='123')
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        response = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}), {'renewal_date': invalid_date_in_future})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        # Manually check form errors instead of using assertFormError
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('renewal_date', form.errors)
        self.assertIn('Invalid date - renewal more than 4 weeks ahead', form.errors['renewal_date'])


class GeneralViewTests(TestCase):
    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_book_list_view(self):
        response = self.client.get(reverse('books'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/book_list.html')

    def test_author_list_view(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_list.html')
