"""
URL configuration for HospitalBed project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from dashboard.views.edit_user_data_views import ManageUserDataRepresentationView
from dashboard.views.location_data_views import LocationDataResponseView
from dashboard.views.main_views import DashboardView, RegistrationView, \
    LoginView, LogoutView

urlpatterns = [
    # could be used later: path('admin/', admin.site.urls),

    # main dashboard template
    path('', DashboardView.as_view(), name="home"),

    # authentication
    path("registration/", RegistrationView.as_view()),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view()),

    # managing of UserDataRepresentation
    path("update/order", ManageUserDataRepresentationView.as_view()),
    path("delete/user-data-representation", ManageUserDataRepresentationView.as_view()),
    path("create/user-data_representation", ManageUserDataRepresentationView.as_view()),

    # data response for the template
    path("get_data/<str:location_type>/<str:theme_type>/<str:time_type>/", LocationDataResponseView.as_view())
]
