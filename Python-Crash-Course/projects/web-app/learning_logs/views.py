from django.shortcuts import render
# Import the model with the data that we need.
# Which is from models.py in the current directory.
from .models import Topic

# Page name from urls.py
def index(request):
    """
    The home page for the Learning Log.
    """
    return render(request, "learning_logs/index.html")


def topics(request):
    """
    Show all topics.
    """
    # Get the data from the database, this must be an object so we can access its properties.
    topics = Topic.objects.order_by("date_added")
    # A dictionary containing keys are the names of templates to access data
    # The values are the data we need for the template.
    # Get the topics to display.
    context = {"topics": topics}
    return render(request, "learning_logs/topics.html", context)


# This requires an additional argument that is used in the database.
def topic(request, topic_id):
    """
    Show the details from a single topic.
    """
    topic = Topic.objects.get(id=topic_id)
    entries = topic.entry_set.order_by("-date_added")
    context = {"topic": topic, "entries": entries}
    return render(request, "learning_logs/topic.html", context)
