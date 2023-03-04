from .models import Comment
from django import forms
from datetime import datetime
from .models import Appointment, Service


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body',)


class AppointmentForm(forms.ModelForm):
    """
    Form to make appointment.
    """
    def __init__(self, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        services = Service.objects.filter(
            active=True).order_by("title").values()
        services_tuples = [("", "---------------")]
        services_tuples = services_tuples + [(str(
            i["id"]) + "," + str(
                i["duration"]), i["title"] + " - " + str(
                    i["duration"]) + " min - €" + str(
                        i["price"])) for i in services]
        self.fields['service_name'] = forms.ChoiceField(
            choices=services_tuples)
        self.fields['date_time'].required = True
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['service_name'].label = "Service"
        self.fields['date_time'] = forms.CharField()
        self.fields['date_time'].label = "Date"
        for fieldname, field in self.fields.items():
            field.widget.attrs.update({'class': 'custom-form-field'})

    class Meta:
        """
        Class to properly label fields.
        """
        model = Appointment
        fields = ('service_name', 'date_time', 'email', 'first_name', 'last_name', 'phone_number')
        labels = {
            'phone_number': ('Phone number (optional)')
        }

    def clean(self):
        cleaned_data = super().clean()
        service_value = cleaned_data["service_name"].split(",")
        service_id = int(service_value[0])
        service_name = Service.objects.get(id=service_id)
        cleaned_data["service_name"] = service_name
        cleaned_data["date_time"] = datetime.strptime(
            cleaned_data["date_time"], '%d-%m-%Y %H:%M')
        return cleaned_data


class ContactForm(forms.Form):
    """
    Form for contacting owner.
    """
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField(max_length=150)
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'custom-form-field'
        }), max_length=2000)
    email.required = True
    first_name.required = True
    last_name.required = True
    first_name.widget.attrs.update({'class': 'custom-form-field'})
    last_name.widget.attrs.update({'class': 'custom-form-field'})
    email.widget.attrs.update({'class': 'custom-form-field'})
    subject.widget.attrs.update({'class': 'custom-form-field'})
