"""
URL configuration for mms project.

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
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_accounts_login(request):
    """Redirect /accounts/login/ to /login/ to handle Django's default redirect"""
    next_param = request.GET.get('next', '')
    if next_param:
        return redirect(f'/login/?next={next_param}')
    return redirect('/login/')

urlpatterns = [
    # Django admin is disabled
    # path('admin/', admin.site.urls),
    # Redirect Django's default /accounts/login/ to our custom /login/
    path('accounts/login/', redirect_accounts_login, name='accounts_login_redirect'),
    path('', include('app.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),

]
"""+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)"""
