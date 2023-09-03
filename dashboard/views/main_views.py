import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, BaseUserCreationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from django.conf import settings

from dashboard.models import User, UserDataRepresentation, Ward, Room, DataRepresentation
from dashboard.services import HL7MessageParser


class CustomUserCreationForm(BaseUserCreationForm):
    """UserCreationForm for the new User-model."""
    class Meta(UserCreationForm.Meta):
        model = User


class RegistrationView(View):
    """View for the registration of a user."""

    def get(self, request):
        """Returns the template with the registration form."""

        return render(request, "registration.html", {
            "form": CustomUserCreationForm()
        })

    def post(self, request):
        """Gets the registration data from the form validates it, creates the user and login this new user."""

        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')

            user = authenticate(request, username=username, password=password)

            # redirect to the login if the user does not exist
            if user is not None:
                login(request, user)
                return redirect('home')
            return redirect("login")


class LoginView(View):
    """View for the login of a user."""

    def get(self, request):
        """Returns the template with the login form."""

        return render(request, "login.html", {
            "form": AuthenticationForm()
        })

    def post(self, request):
        """Gets the login data from the form validates it authenticates login the user."""

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect("home")

        # redirect to the login if the form is not valid
        return render(request, "login.html", {
            "form": form
        })


class LogoutView(View):
    """View for the logout of a user."""

    def get(self, request):
        """Logs out a user."""

        logout(request)

        return redirect("login")


@method_decorator(login_required, name="get")
class DashboardView(TemplateView):
    """TemplateView for the main template of the dashboard."""

    template_name = "dashboard.html"

    def get_context_data(self):
        """Returns the context for the dashboard template."""

        context = dict()
        user = self.request.user
        context["user"] = user

        user_data_representations = UserDataRepresentation.objects.filter(user=user) \
            .select_related("data_representation")
        context["user_data_representations"] = user_data_representations

        context["wards"] = Ward.objects.all()
        context["rooms"] = Room.objects.all()
        context["now"] = timezone.now()

        context[
            "structured_data_representations"] = DataRepresentation.objects.structured_data_representations()

        return context
