import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, BaseUserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from django.conf import settings

from dashboard.models import User, UserDataRepresentation, Ward, Room, DataRepresentation
from dashboard.services import Hl7MessageParser


def parse_hl7(request):
    Hl7MessageParser.parse_hl7_message_from_directory(settings.HL7_DIRECTORY)
    return HttpResponse()


class CustomUserCreationForm(BaseUserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User


class RegistrationView(View):
    def get(self, request):
        return render(request, "registration.html", {
            "form": CustomUserCreationForm()
        })

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            return redirect("login")


class LoginView(View):
    def get(self, request):
        return render(request, "login.html", {
            "form": AuthenticationForm()
        })

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect("home")
        return render(request, "login.html", {
            "form": form
        })


class LogoutView(View):
    def get(self, request):
        logout(request)

        return redirect("login")


@method_decorator(login_required, name="get")
class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self):
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
