from decouple import config
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .tokens import account_activation_token


def home(request: HttpRequest):
    return render(request, 'index.html')

def signup(request: HttpRequest):
    if request.method != 'POST':
        return render(request, 'signup.html')

    if User.objects.filter(username=request.POST['username']):
        messages.error(request, 'Username already exist')
        return render(request, 'signup.html')

    if User.objects.filter(email=request.POST['email']):
        messages.error(request, 'Email already registered!')
        return render(request, 'signup.html')

    if len(request.POST['username']) > 10:
        messages.error(request, 'Username must be 10 characters!')
        return render(request, 'signup.html')

    if request.POST['pass'] != request.POST['passc']:
        messages.error(request, 'Passwords did not match!')
        return render(request, 'signup.html')

    if not request.POST['username'].isalnum():
        messages.error(request, 'Username must be Alpha-Numeric!')
        return render(request, 'signup.html')

    user = User.objects.create_user(request.POST['username'],
                                       request.POST['email'],
                                       request.POST['pass'])
    user.first_name = request.POST['fname']
    user.last_name = request.POST['lname']
    user.is_active = False
    user.save()

    messages.success(request, ('Successfully created. '
                               f'Please check your {request.POST["email"]}.'))

    message = render_to_string(
        'email_confirmation.html',
        {
            'name': user.first_name,
            'domain': get_current_site(request).domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user)
        }
    )
    email = EmailMessage(config('SUBJECT'), message,
                         config('EMAIL_HOST_USER'), [user.email])
    email.fail_silently = True
    email.send()
    return redirect('signin')

def signin(request: HttpRequest):
    if request.method != 'POST':
        return render(request, 'signin.html')
    user = authenticate(username=request.POST['username'],
                        password=request.POST['pass'])
    if not user:
        messages.error(request, 'Bad Credentials')
        return redirect('home')
    login(request, user)
    messages.success(request, 'Logged In')
    return redirect('home')

def signout(request: HttpRequest):
    logout(request)
    messages.success(request, 'Logged Out')
    return redirect('home')

def activate(request: HttpRequest, uidb64, token):
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')
    return render(request, 'activation_failed.html')
