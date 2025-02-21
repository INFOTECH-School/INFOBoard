from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from collab.models import ExcalidrawRoom


@login_required
def dashboard(request):
    tables = ExcalidrawRoom.objects.filter(room_created_by=request.user).all()
    return render(request, 'dashboard.html', {'tables': tables})
