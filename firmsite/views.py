from django.shortcuts import render, get_object_or_404, reverse
from django.views import generic, View
from django.http import HttpResponseRedirect
from .models import Post, Appointment, Planning
from .forms import CommentForm,  AppointmentForm, ContactForm
from datetime import datetime, timedelta
import json
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.template.loader import render_to_string


class PostList(generic.ListView):
    model = Post
    queryset = Post.objects.filter(status=1).order_by('-created_on')
    template_name = 'index.html'
    paginate_by = 6


class PostDetail(View):

    def get(self, request, slug, *args, **kwargs):
        queryset = Post.objects.filter(status=1)
        post = get_object_or_404(queryset, slug=slug)
        comments = post.comments.filter(approved=True).order_by('created_on')
        liked = False
        if post.likes.filter(id=self.request.user.id).exists():
            liked = True

        return render(
            request,
            "post_detail.html",
            {
                "post": post,
                "comments": comments,
                "commented": False,
                "liked": liked,
                "comment_form": CommentForm()
            },
        )

    def post(self, request, slug, *args, **kwargs):
        queryset = Post.objects.filter(status=1)
        post = get_object_or_404(queryset, slug=slug)
        comments = post.comments.filter(approved=True).order_by('created_on')
        liked = False
        if post.likes.filter(id=self.request.user.id).exists():
            liked = True

        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            comment_form.instance.email = request.user.email
            comment_form.instance.name = request.user.username
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.save()
        else:
            comment_form = CommentForm()

        return render(
            request,
            "post_detail.html",
            {
                "post": post,
                "comments": comments,
                "commented": True,
                "liked": liked,
                "comment_form": CommentForm()
            },
        )


class PostLike(View):

    def post(self, request, slug, *args, **kwargs):
        post = get_object_or_404(Post, slug=slug)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)

        return HttpResponseRedirect(reverse('post_detail', args=[slug]))


class HomePage(View):
    """
    View to render homepage.
    """
    def get(self, request):
        """
        gets all the services from database and returns them as context.
        """
        queryset = list(Service.objects.filter(
            display=True).order_by("title").values())
        services = {"services": queryset, "is_home": True}
        return render(request, "index.html", context=services)


class BookingModule(View):
    """
    View to render the booking page and data.
    """

    def get(self, request):
        """
        Gets all necessary data: Appointments, Services and Planning.
        Passes it as context while rendering book.html.
        """
        user_dict = {}
        if request.user.is_authenticated:
            user_dict = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number}
        else:
            user_dict = {}

        yesterday = datetime.today() - timedelta(days=1)
        appointmentQueryset = list(Appointment.objects.filter(
            date_time__gt=yesterday).order_by("date_time").values())
        planningQueryset = list(Planning.objects.filter(
            active=True).order_by("title").values())

        for dict in appointmentQueryset:
            dict["date_time"] = dict["date_time"].isoformat()
            dict["duration"] = int(Service.objects.get(
                id=dict['service_name_id']).duration)

        form = AppointmentForm(initial=user_dict)
        context = {
            "planning": json.dumps(planningQueryset),
            "appointments": json.dumps(appointmentQueryset),
            "appointment_form": form}
        return render(request, "book.html", context=context)

    def post(self, request):
        """
        Post method for booking an appointment.
        Checks if forms is valid and takes appropriate action.
        """
        form = AppointmentForm(request.POST)
        if form.is_valid():
            subject = "De Jure Law Firm booking"
            if form.cleaned_data['phone_number']:
                phone = form.cleaned_data['phone_number']
            else:
                phone = "-"
            merge_data = {
                'service': form.cleaned_data['service_name'].title,
                'date': form.cleaned_data['date_time'].strftime(
                    "%A %d %B %Y, %H:%M"),
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'phone': phone,
            }
            html_body = render_to_string(
                "email/email-book-inlined.html", context=merge_data)
            text_body = "\n".join(merge_data.values())
            form.save()
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email='chrisorlichenko@gmail.com',
                    to=[form.cleaned_data['email']]
                    )
                msg.attach_alternative(html_body, "text/html")
                msg.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return HttpResponseRedirect("thankyou")
        else:
            form = AppointmentForm()
            return HttpResponseRedirect("book-error")


class ThankYou(View):
    """
    Simple view to render the booked.html page for successful bookings.
    """

    def get(self, request):
        """
        Get method, renders booked.html.
        """
        return render(request, "booked.html")


class BookError(View):
    """
    View to render page in case of unsuccessful booking.
    """

    def get(self, request):
        """
        Get method for rendering book-error html.
        """
        return render(request, "book-error.html")


class Services(View):
    """
    View to render services page.
    """

    def get(self, request):
        """
        Get method, taking services from database with 'display' set to true.
        """
        queryset = list(Service.objects.filter(
            display=True).order_by("title").values())
        services = {"services": queryset}
        return render(request, "services.html", context=services)


class About(View):
    """
    View to render about page.
    """

    def get(self, request):
        """
        Get method, to render about html.
        """
        return render(request, "about.html")


class Contact(View):
    """
    View to render contact page.
    """

    def get(self, request):
        """
        Gets user data if logged in and renders contact form with initial data.
        """
        user_dict = {}
        if request.user.is_authenticated:
            user_dict = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name}
        else:
            user_dict = {}
        form = ContactForm(initial=user_dict)
        context = {"contact_form": form}
        return render(request, "contact.html", context=context)

    def post(self, request):
        """
        Posts the contact form, by sending it as an email
        """
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                subject = "De Jure Law Firm website question"
                merge_data = {
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'email': form.cleaned_data['email'],
                    'subject': form.cleaned_data['subject'],
                    'message': form.cleaned_data['message'],
                }
                html_body = render_to_string(
                    "email/email-contact-inlined.html", context=merge_data
                    )
                text_body = "\n".join(merge_data.values())
                try:
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_body,
                        from_email='chrisorlichenko@gmail.com',
                        to=[form.cleaned_data['email']])
                    msg.attach_alternative(html_body, "text/html")
                    msg.send()
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
                return HttpResponseRedirect('contact')
