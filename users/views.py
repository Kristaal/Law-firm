from datetime import datetime, timedelta
import json
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from users.forms import EditUserForm
from users.forms import EditAppointmentForm
from salon.models import Appointment, Service, Planning


class Dashboard(View):
    """
    View to with get and post method for User dashboard.
    """

    def get(self, request):
        """
        Get method to get user data and their appointments.
        Data is formatted server side to be displayed in a user readable way.
        """
        user_dict = {}
        if request.user.is_authenticated:
            user_dict = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number
                }
        else:
            return HttpResponseRedirect(reverse("account_login"))

        user_form = EditUserForm(initial=user_dict)

        yesterday = datetime.today() - timedelta(days=1)

        appointment_queryset_1 = Appointment.objects.filter(
            date_time__gt=yesterday).filter(
                user__email=request.user.email).order_by(
                    "date_time").values()
        appointment_queryset_2 = Appointment.objects.filter(
            date_time__gt=yesterday).filter(
                email=request.user.email).order_by(
                    "date_time").values()
        appointment_queryset = list(
            appointment_queryset_1 | appointment_queryset_2)

        for dict in appointment_queryset:
            date = dict["date_time"]
            check_date = datetime.now() + timedelta(days=2)

            if date <= check_date:
                # appointments that are closer than 48 hours cannot be canceled
                dict["not_cancellable"] = True
                dict["date_time_short"] = dict[
                    "date_time"].strftime("%A %d %B, %H:%M")
                dict["date_time"] = dict[
                    "date_time"].strftime("%A %d %B %Y, %H:%M")
                dict["duration"] = int(Servise.objects.get(
                    id=dict['servise_name_id']).duration)
                dict["service_name"] = Service.objects.get(
                    id=dict['service_name_id']).title
        context = {"user_form": user_form, "appointments": appointment_queryset}
        return render(request, "user-dashboard.html", context=context)

    def post(self, request):
        """
        Post method for user dashboard, with multiple options:
        - Posting new user data (changed name, phone or email),
        - posting a canceled appointment to database (removing the object),
        """

        yesterday = datetime.today() - timedelta(days=1)

        appointment_queryset_1 = Appointment.objects.filter(
            date_time__gt=yesterday).filter(
                user__email=request.user.email).order_by(
                    "date_time").values()
        appointment_queryset_2 = Appointment.objects.filter(
            date_time__gt=yesterday).filter(
                email=request.user.email).order_by(
                    "date_time").values()
        appointment_queryset = list(
            appointment_queryset_1 | appointment_queryset_2)

        for dict in appointment_queryset:
            dict["date_time_short"] = dict[
                "date_time"].strftime("%A %d %B, %H:%M")
            dict["date_time"] = dict[
                "date_time"].strftime("%A %d %B %Y, %H:%M")
            dict["duration"] = int(Service.objects.get(id=dict[
                'service_name_id']).duration)
            dict["service_name"] = Service.objects.get(id=dict[
                'service_name_id']).title

        if request.POST.get('appointment_id', default=None):
            # deletes appointment and sends email to user
            appointment_id = request.POST.get('appointment_id')
            appointment = Appointment.objects.get(id=appointment_id)
            if request.user.email == appointment.email:
                appointment.delete()
                subject = "De Jure Law Firm appointment canceled."
                merge_data = {
                    'service': appointment.service_name.title,
                    'date': appointment.date_time.strftime(
                        "%A %d %B %Y, %H:%M"),
                    'first_name': appointment.first_name,
                    'last_name': appointment.last_name,
                    'email': appointment.email,
                }
                html_body = render_to_string(
                    "email/email-book-canceled-inlined.html", context=merge_data
                    )
                text_body = "\n".join(merge_data.values())
                try:
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_body,
                        from_email='chrisorlichenko@gmail.com',
                        to=[appointment.email])
                    msg.attach_alternative(html_body, "text/html")
                    msg.send()
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
                return HttpResponseRedirect("dashboard")
            else:
                return HttpResponseRedirect("dashboard")

        if request.POST.get('first_name', default=None):
            # edit user info and save to database, then re-render dashboard
            form = EditUserForm(data=request.POST, instance=request.user)
            if form.is_valid():
                user = form.save(commit=False)
                user.save(update_fields=[
                    'first_name', 'last_name', 'phone_number'])

                user_dict = {}
                if request.user.is_authenticated:
                    user_dict = {
                        'email': request.user.email,
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'phone_number': request.user.phone_number
                        }
                else:
                    user_dict = {}

                user_form = EditUserForm(initial=user_dict)

                context = {
                    "user_form": user_form,
                    "appointments": appointment_queryset,
                    "saved": True}
                return render(request, "user-dashboard.html", context=context)
            else:
                user_dict = {
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'phone_number': request.user.phone_number
                    }
                user_form = EditUserForm(initial=user_dict)

                context = {
                    "user_form": user_form,
                    "appointments": appointment_queryset,
                    "not_saved": True}
                return render(request, "user-dashboard.html", context=context)


class EditAppointment(View):
    """
    View to allow user to edit appointment info
    """

    def get(self, request, slug):
        """
        Gets all data for selected appointment (slug)
        """
        if request.user.email == Appointment.objects.get(id=slug).email:
            # checks if user requesting the change is same as appointment user
            service_id = Appointment.objects.get(id=slug).service_name
            appointment_date = Appointment.objects.get(id=slug).date_time
            appointment_date = appointment_date.strftime("%d-%m-%Y %H:%M")
            user_dict = {}
            services = Service.objects.filter(
                title=service_id).order_by("title").values()
            services_tuple = [(str(
                i["id"]) + "," + str(
                    i["duration"]), i["title"] + " - " + str(
                        i["duration"]) + " min - €" + str(
                            i["price"])) for i in services]
            user_dict = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number,
                'date_time': appointment_date
                }

            yesterday = datetime.today() - timedelta(days=1)
            appointment_queryset = list(Appointment.objects.filter(
                date_time__gt=yesterday).order_by("date_time").values())
            planning_queryset = list(Planning.objects.filter(
                active=True).order_by("title").values())

            for dict in appointment_queryset:
                dict["date_time"] = dict["date_time"].isoformat()
                dict["duration"] = int(Servise.objects.get(
                    id=dict['service_name_id']).duration)

            form = EditAppointmentForm(initial=user_dict)
            form.fields["service_name"].choices = services_tuple
            context = {
                "planning": json.dumps(planning_queryset),
                "appointments": json.dumps(appointment_queryset),
                "appointment_form": form
                }
            return render(request, "edit-appointment.html", context=context)
        else:
            return render(request, "book-error.html")

    def post(self, request, slug):
        """
        Post edited appointment data to database
        """
        form = EditAppointmentForm(
            request.POST, instance=Appointment.objects.get(id=slug))
        if form.is_valid():
            subject = "De Jure Law Firm updated booking"
            if form.cleaned_data['phone_number']:
                phone = form.cleaned_data['phone_number']
            else:
                phone = "-"
            merge_data = {
                'services': form.cleaned_data[
                    'service_name'].title,
                'date': form.cleaned_data[
                    'date_time'].strftime("%A %d %B %Y, %H:%M"),
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'phone': phone,
            }
            html_body = render_to_string(
                "email/email-book-edited-inlined.html", context=merge_data
                )
            text_body = "\n".join(merge_data.values())
            form.save()
            try:
                msg = EmailMultiAlternatives(
                    subject=subject, body=text_body,
                    from_email='chrisorlichenko@gmail.com',
                    to=[form.cleaned_data['email']]
                    )
                msg.attach_alternative(html_body, "text/html")
                msg.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            form.save()
            return HttpResponseRedirect(reverse("dashboard"))
        else:
            form = EditAppointmentForm()
            return HttpResponseRedirect("book-error")
