from django.conf import settings
from django.conf.urls import *
from django.views.generic import ListView, DetailView
from photologue.models import Gallery
from photologue.views import GalleryDetailView
from photologue.urls import urlpatterns as pl_urlpatterns

# Number of random images from the gallery to display.
SAMPLE_SIZE = ":%s" % getattr(settings, 'GALLERY_SAMPLE_SIZE', 5)

urlpatterns = patterns('django.views.generic',
    url(r'^$', ListView.as_view(model=Gallery, queryset=Gallery.objects.filter(
        is_public=True), template_name='photologue/gallery_list.html'),
        name='pl-gallery-index'),

#    url(r'^(?P<slug>[\-\d\w]+)/$', GalleryDetailView.as_view(), name='pl-gallery'),
) + pl_urlpatterns
