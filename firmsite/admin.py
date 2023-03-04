from django.contrib import admin
from .models import Post, Comment, Service, Planning, Appointment
from django_summernote.admin  import SummernoteModelAdmin
from datetime import timedelta


@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):

    list_display = ('title', 'slug', 'status', 'created_on')
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('status', 'created_on')
    summernote_fields = ('content')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = ('name', 'body', 'post', 'created_on', 'approved')
    list_filter = ('approved', 'created_on')
    search_fields = ('name', 'email', 'body')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):

    list_display = ('title', 'appointment_type')
    list_filter = ('appointment_type', 'price')
    search_fields = ['title', 'description', 'appointment_type']

@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):

    list_display = ['title']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = ['date_time', 'get_end_time', 'get_service_title', 'first_name', 'last_name', 'email']
    list_filter = ('first_name', 'last_name', 'email')
    search_fields = ['first_name', 'last_name', 'email']
    ordering = ['-date_time']

    @admin.display(description="Service")
    def get_service_title(self, obj):
        return obj.service_name.title

    @admin.display(description="Duration")
    def get_service_duration(self, obj):
        return obj.service_name.duration

    @admin.display(description="End Time")
    def get_end_time(self, obj):
        start_time = obj.date_time
        duration = int(obj.service_name.duration)
        end_time = start_time + timedelta(minutes=duration)
        return end_time
