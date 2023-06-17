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

from dashboard.views.edit_user_data_views import UpdateOrderView, DeleteUserDataRepresentation, \
    CreateUserDataRepresentationView
from dashboard.views.location_data_views import AllocationView
from dashboard.views.main_views import DashboardView, create_data_representation

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', DashboardView.as_view()),

    path("update/order", UpdateOrderView.as_view()),
    path("delete/user-data-representation", DeleteUserDataRepresentation.as_view()),
    path("create/user-data_representation", CreateUserDataRepresentationView.as_view()),
    path("create/", create_data_representation),

    path("get_data/<str:location_type>/<str:theme_type>/<str:time_type>/", AllocationView.as_view())
]
