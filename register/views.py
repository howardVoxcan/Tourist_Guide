from .forms import RegisterForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save()
    else: 
        form = RegisterForm()

    return render(response, "signup/signup.html",{
        "form": form
    })

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('homepage')  # hoặc URL bạn muốn chuyển hướng đến

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('homepage')  # hoặc sử dụng 'next' nếu có
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})