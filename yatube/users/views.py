from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class LogoutView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/logged_out.html'


class LoginView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/login.html'


class PasswordChangeView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:password_change')
    template_name = 'users/password_change_form.html'


class PasswordChangeDoneView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_done.html'


class PasswordResetView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:password_reset')
    template_name = 'users/password_reset_form.html'


class PasswordResetDoneView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:password_reset_done')
    template_name = 'users/password_reset_done.html'


class PasswordResetConfirmView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:password_reset_confirm')
    template_name = 'users/password_reset_confirm.html'


class PasswordResetCompleteView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:password_reset_complete')
    template_name = 'users/password_reset_complete.html'
