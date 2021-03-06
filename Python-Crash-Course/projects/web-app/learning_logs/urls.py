"""
Defines URL patterns for learning_logs app.
"""
# Maps URLs to views
from django.urls import path
# import the views from the current directory (i.e. dot)
from . import views

app_name = "learning_logs"

# The pages that can be requested by this app.
urlpatterns = [
    # Home Page
    # 1st arg = Routing string, ignores base URL (e.g. http://localhost:8000)
    # 2nd arg = What function to call
    # 3rd arg = URL pattern name, used internally as a reference.
    path("", views.index, name="index"),
    # Topics page
    path("topics/", views.topics, name="topics"),
    # Pages for each topic, based on DB ID
    # Matches a number between // and stores it in the variable topic_id
    # This is passed as an arg to the topic view.
    path("topics/<int:topic_id>/", views.topic, name="topic"),
    path("new_topic/", views.new_topic, name="new_topic")
]