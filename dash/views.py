from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from collab.models import ExcalidrawRoom


@login_required
def my_tables(request):
    tables = ExcalidrawRoom.objects.filter(room_created_by=request.user).all()
    year = datetime.now().year
    return render(request, 'my_whiteboards.html', {'tables': tables, 'year': year})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.add_message(request, 20, f'Pomyślnie zalogowano!')
            return redirect('my')  # Zmień na właściwy URL po zalogowaniu
        else:
            messages.add_message(request, 30, 'Nieprawidłowa nazwa lub hasło', 'danger')
            return render(request, 'login.html')

    return render(request, 'login.html')
