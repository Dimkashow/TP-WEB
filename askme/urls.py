"""askme URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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

from django.urls import path
from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from app import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('ask/', views.ask, name='ask'),
    path('login/', views.login, name='login'),
    path('singup/', views.singup, name='singup'),
    path('question/<int:qid>', views.question, name='question'),
    path('ajax/like', views.ajax_like, name='ajaxlike'),
    path('ajax/correct', views.ajax_correct, name='ajaxcorrect'),
    path("ajax/search", views.ajax_search, name="ajaxsearch"),
    path('tag/<str:tag>', views.tag, name='tag'),
    path('hot/', views.hot, name='hot'),
    path('logout_view/', views.logout_view, name='logout'),
    path('settings/', views.settings, name='settings'),
    path('', views.base, name='base'),
    url(r'^admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

