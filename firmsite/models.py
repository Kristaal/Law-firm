from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from users.models import User
from django.core.validators import RegexValidator


STATUS = ((0, "Draft"), (1, "Published"))


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    featured_image = CloudinaryField('image', default='placeholder')
    excerpt = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATUS, default=0)
    likes = models.ManyToManyField(
        User, related_name='blog_likes', blank=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return self.title

    def number_of_likes(self):
        return self.likes.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments")
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_on"]

    def __str__(self):
        return f"Comment {self.body} by {self.name}"


class Service(models.Model):
    """
    Service model.
    """
    appointment_type = models.CharField(max_length=150)
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=225)
    image = CloudinaryField('image', default='placeholder')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DecimalField(max_digits=3, decimal_places=0)
    display = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    def __str__(self):
        #  Returns a string of title of service
        return f"{self.title}"


class Appointment(models.Model):
    """
    Appointment model
    """
    user = models.ForeignKey(
        User,
        related_name="user",
        on_delete=models.PROTECT,
        null=True,
        blank=True
        )
    email = models.EmailField(max_length=254, blank=True, null=True)
    first_name = models.CharField(max_length=254, null=True, blank=True)
    last_name = models.CharField(max_length=254, null=True, blank=True)
    phone_number = models.CharField(max_length=16, null=True, blank=True)
    service_name = models.ForeignKey(
        Service,
        related_name="service_name",
        on_delete=models.PROTECT,
        null=True
        )
    date_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.date_time = self.date_time.replace(tzinfo=None)
        super(Appointment, self).save(*args, **kwargs)


class Planning(models.Model):
    """
    Planning model used to manage bookable times in datapicker.
    Allow_times is a comma seperated string of times.
    Disabled_dates is a comma seperated string of dates.
    Disabled_weekdays is a comme seperated string of numbers,
    representing weekdays.
    """
    validate_times = RegexValidator(
        r'^(?:[01]\d|2[1-3]):[0-5]\d(?::[0-5]\d)?(?:,(?:[01]\d|2[1-3]):[0-5]\d(?::[0-5]\d)?)*$',
        'Please enter comma seperated times, without spaces, like so: 12:00,13:15'
        )
    validate_dates = RegexValidator(
        r'^(\s{0,})(\d{2}\.\d{2}\.\d{4})(,\d{2}\.\d{2}\.\d{4}){1,}(\s){0,}$',
        "Please enter comma seperated dates (dd.mm.yyyy), "
        "without spaces, like so: 01.11.2028,02.11.2028"
        )
    validate_weekdays = RegexValidator(
        r'^[0-6](,[0-6])*$',
        "Please enter valid numbers for weekdays, seperated by comma's. "
        "Values from 0-6, starting with sunday at value 0 (0,1,3 for example)."
        )

    title = models.CharField(max_length=150, unique=True)
    allow_times = models.TextField(default="", validators=[validate_times])
    disabled_dates = models.TextField(default="", validators=[validate_dates])
    disabled_weekdays = models.TextField(
        default="", validators=[validate_weekdays])
    active = models.BooleanField(default=False)
