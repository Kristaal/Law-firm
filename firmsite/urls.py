from . import views
from django.urls import path


urlpatterns = [
    path('', views.PostList.as_view(), name='home'),
    path('<slug:slug>/', views.PostDetail.as_view(), name='post_detail'),
    path('like/<slug:slug>', views.PostLike.as_view(), name='post_like'),
    path('book', views.BookingModule.as_view(), name="book"),
    path('thankyou', views.ThankYou.as_view(), name="thankyou"),
    path('book-error', views.BookError.as_view(), name="book-error"),
    path('services', views.Services.as_view(), name="services"),
    path('about', views.About.as_view(), name="about"),
    path('contact', views.Contact.as_view(), name="contact"),
]
