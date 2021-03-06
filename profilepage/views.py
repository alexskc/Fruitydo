import json
from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django_markup.markup import formatter
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from .models import Task, Event
from userprefs.models import Userpreference
from django.contrib.auth.decorators import login_required

NOEVENT = "Nothing happened on this date."
ERROR = "An unexpected error occured"

@login_required
def profile(request):
    """Returns the profile/todo page"""
    tasks = Task.objects.filter(User=request.user).order_by('due_date')
    incompletetasks = tasks.filter(complete=False)
    for task in tasks:
        task.overdue = True
    return render(request, 'profilepage/index.html', {'incompletetasks':incompletetasks})

@login_required
def done(request):
    """Returns the complete tasks page."""
    tasks = Task.objects.filter(User=request.user)
    completetasks = tasks.filter(complete=True)
    return render(request, 'profilepage/completed.html', {'completetasks':completetasks})

@login_required
def create(request):
    """Creates a task"""
    entered_title = request.POST['task_title']
    entered_date = request.POST['duedate']
    if valid_title(entered_title):
        task = Task(
            User=request.user,
            task_title=entered_title,
            pub_date=datetime.now(),
            recurring=0,
            complete=0,
            due_date=entered_date)
        task.save()
    else:
        messages.error(request, "Not a valid task name.")
    return HttpResponseRedirect(reverse('profilepage:profile'))

def valid_title(title):
    """Checks if a task title is correct."""
    if not 2 < len(title) < 64:
        return False
    return True

@login_required
def event_create(request):
    """Creates an event for a task."""
    completed = bool("markcomplete" in request.POST)
    print(completed)
    entered_description = request.POST['event_description']
    entered_task = request.POST['task']
    entered_date = request.POST['pub_date']
    task = Task.objects.get(id=entered_task)
    if task.User != request.user:
        return HttpResponse("An unexpected error occured.")
    returnevent = Event.objects.filter(pub_date=entered_date, Task_id=entered_task)
    if not returnevent:
        event = Event(
            event_description=entered_description,
            pub_date=entered_date,
            Task=get_object_or_404(Task, pk=entered_task))
        event.save()
        task.complete = completed
        task.save()
    else:
        returnevent[0].event_description = entered_description
        task.complete = completed
        returnevent[0].save()
        task.save()
    return HttpResponseRedirect(reverse('profilepage:profile'))

@login_required
def event_dates(request):
    """Returns dates where events occured for a given task in a given month"""
    user = request.user
    task = get_object_or_404(Task, User_id=user.id, id=request.POST['task'])
    yymm = request.POST['month']
    yymm = yymm.split("-")
    year = yymm[0]
    month = yymm[1]
    events = Event.objects.filter(Task_id=task.id, pub_date__year=year, pub_date__month=month)
    eventdates = []
    for event in events:
        eventdates.append(event.pub_date)
    alldates = {'eventdates': eventdates, 'due_date': [task.due_date]}
    data = json.dumps(alldates, cls=DjangoJSONEncoder)
    return HttpResponse(data)

@login_required
def task_delete(request):
    """Delete the given task."""
    user = request.user
    task = get_object_or_404(Task, User_id=user.id, id=request.POST['task'])
    task.delete()
    return HttpResponseRedirect(reverse('profilepage:profile'))

@login_required
def event_fetch(request):
    """Return the description for the given event."""
    user = request.user
    date = request.POST['date']
    try:
        task = Task.objects.get(id=request.POST['task'], User_id=user.id)
    except Task.DoesNotExist:
        responsedata = {'fancy': ERROR, 'raw': ERROR}
    try:
        returnevent = Event.objects.get(pub_date=date, Task_id=task.id)
    except Event.DoesNotExist:
        responsedata = {'fancy': NOEVENT, 'raw': NOEVENT}
    else:
        fancy = formatter(returnevent.event_description, filter_name='markdown')
        raw = returnevent.event_description
        if user.userpreference.encryption == False:
            responsedata = {'fancy': fancy, 'raw':raw}
        else:
            responsedata = {'raw': raw}
    finalresponse = json.dumps(responsedata, cls=DjangoJSONEncoder)
    return HttpResponse(finalresponse)

@login_required
def event_fetch_fancy(request):
    """Return a markdown-formatted version of the requested event."""
    string = event_fetch(request)
    string = formatter(string, filter_name='markdown')
    return HttpResponse(string)

@login_required
def event_fetch_raw(request):
    """Return an unformatted version of the requested event."""
    string = event_fetch(request)
    return HttpResponse(string)
