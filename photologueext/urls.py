from django.conf import settings
from django.conf.urls import *
from django.views.generic import ListView, DetailView
from photologue.models import Gallery

# Number of random images from the gallery to display.
SAMPLE_SIZE = ":%s" % getattr(settings, 'GALLERY_SAMPLE_SIZE', 5)

urlpatterns = patterns('django.views.generic',
    url(r'^$', ListView.as_view(model=Gallery, queryset=Gallery.objects.filter(
        is_public=True), template_name='photologue/gallery_list.html'),
        name='pl-gallery-index'),

    url(r'^(?P<title_slug>[\-\d\w]+)/$', DetailView.as_view(model=Gallery,
        template_name='photologue/gallery_detail.html'),
        name='pl-gallery'),
)
