from django.contrib import admin
from django.urls import path, include
import os
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [ 
    path('admin/', admin.site.urls),
    path("", include("store.urls", namespace="store")),  # This line connects store/urls.py
]

# serve media files in development
if settings.DEBUG:
     urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    