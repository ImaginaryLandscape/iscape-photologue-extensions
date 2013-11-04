import zipfile
import cStringIO

from django import forms, http
from django.core.cache import cache
from django.core import urlresolvers
from django.core.files import base as files
from django.utils import safestring, functional, encoding
from django.utils.translation import ugettext_lazy as _
from django.template import defaultfilters
from django.contrib import admin
from django.contrib.admin.util import unquote
from photologue import models, admin as photologueadmin
from photologueext import settings


class PhotoSelectMultiple(forms.CheckboxSelectMultiple):
    class Media:
        css = {
            'all': (settings.PHOTOLOGUEEXT_MEDIA_URL+'css/photologueext.css',)
        }

    def render(self, name, value, attrs=None, choices=()):
        output = super(PhotoSelectMultiple, self).render(
            name, value, attrs, choices)
        return safestring.mark_safe(
            '<ul class="vPhotoSelectMultiple">' + output[4:])


class PhotoModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = PhotoSelectMultiple
    photo_size = getattr(
        settings, 'PHOTOLOGUEEXT_WIDGET_THUMBNAIL_SIZE', 'admin_thumbnail')

    def __init__(self, *args, **kwargs):
        if 'photo_size' in kwargs:
            self.photo_size = kwargs.pop('photo_size')
        super(PhotoModelMultipleChoiceField, self).__init__(*args, **kwargs)
        self.help_text = ''

    def label_from_instance(self, obj):
        url = getattr(obj, 'get_%s_url' % self.photo_size)()
        try: #FIXME - remove this when decided on django version
            admin_url = urlresolvers.reverse(
                'admin:photologue_photo_change', args=(obj.pk,))
        except urlresolvers.NoReverseMatch, e:
            admin_url =  urlresolvers.reverse(
                admin.site.root, args=('photologue/photo/%s/' % obj.pk,))

        return safestring.mark_safe(u'''
           <a href="%(admin_url)s" title="%(name)s">
             <img src="%(url)s" alt="%(name)s" title="%(name)s" />
           </a>
        ''' % {
            'url': url,
            'name': obj,
#             'admin_url': urlresolvers.reverse(
#                 admin.site.root, args=('photologue/photo/%s/' % obj.pk,))
            'admin_url': admin_url

        })


class GalleryModelForm(forms.ModelForm):
    class Meta:
        model = models.Gallery

    zip_file = forms.FileField(
        label=u'Images file (.zip)', required=False,
        help_text=_(
            'Select a .zip file of images to add to this gallery. '
            'All photos will be given a title made up of '
            'the gallery title + a sequential number.'))
    caption = forms.CharField(
        widget=forms.Textarea, required=False,
        help_text=_(
            'Images uploaded in a zip file or images individually '
            'uploaded above will be given this caption'
    ))

    for n in range(getattr(settings, 'PHOTOLOGUEEXT_GALLERYUPLOAD_NUM_IMAGEFIELDS', 5)):
        locals()['image_%s' % (n + 1)] = forms.ImageField(required=False)

    if getattr(settings, 'PHOTOLOGUEEXT_M2M_THUMBNAILS', False):
        photos = PhotoModelMultipleChoiceField(
            models.Photo.objects.all(), required=False)

    if getattr(settings, 'PHOTOLOGUEEXT_ONE_GALLERY_PER_PHOTO', False):
        def __init__(self, *args, **kwargs):
            super(GalleryModelForm, self).__init__(*args, **kwargs)
            queryset = self.fields['photos'].queryset.filter(galleries__isnull=True)
            if self.instance.pk:
                queryset = queryset | models.Photo.objects.filter(
                    galleries__in=[self.instance.pk])
            self.fields['photos'].queryset = queryset

    def save(self, commit=True):
        gallery = super(GalleryModelForm, self).save(commit)

        zip_file = self.cleaned_data['zip_file']
        image_files = False
        for key, val in self.cleaned_data.items():
            if key.startswith('image_') and val:
                image_files = True
                break

        if zip_file or image_files:
            # we're hooking into photologue's GalleryUpload model to
            # reuse the existing code there for handling zip uploads.
            # since we've added the ability to upload a set of images
            # individually, we're zipping them up and programmatically
            # creating a gallery upload object to get the same
            # functionality.
            gallery.save()
            self.save_m2m()

            galleryupload = models.GalleryUpload(
                gallery=gallery, title=gallery.title,
                caption=self.cleaned_data['caption'])
            if zip_file:
                galleryupload.zip_file.save(zip_file.name, zip_file, save=False)
            else:
                zipfp = cStringIO.StringIO()
                zipobj = zipfile.ZipFile(zipfp, 'w')
                for key, val in self.cleaned_data.items():
                    if key.startswith('image_') and val:
                        zipobj.writestr(val.name.encode('ascii'), val.read())
                zipobj.close()
                zipfp.seek(0)
                zipname = gallery.title_slug
                galleryupload.zip_file.save(
                    '%s.zip' % zipname, files.ContentFile(zipfp.read()), save=False)
            gallery = self.instance = galleryupload.save()
            self.cleaned_data['photos'] = list(gallery.photos.all())

        return gallery


class GalleryAdmin(photologueadmin.GalleryAdmin):
    class Media:
        js = [
            (settings.PHOTOLOGUEEXT_MEDIA_URL + 'js/jquery.js'),
            (settings.PHOTOLOGUEEXT_MEDIA_URL + 'js/jquery.uploadProgress.js'),
            (settings.PHOTOLOGUEEXT_MEDIA_URL + 'js/uploadprogress.js'),
        ]
        css = {'all': (settings.PHOTOLOGUEEXT_MEDIA_URL+'css/uploadprogress.css',)}

    form = GalleryModelForm
    change_form_template = 'admin/change_form_uploadprogress.html'
    fieldsets = (
        (None, {'fields': (
            'date_added', 'title', 'title_slug', 'description', 'is_public', 'tags',)}),
        (u'Existing photos', {'fields': ('photos',)}),
        (u'Option A: Upload a zip file of images', {'fields': ('zip_file',)}),
        (u'Option B: Select and upload images individually', {
            'fields': tuple('image_%s' % (n + 1) for n in range(
                getattr(settings, 'PHOTOLOGUEEXT_GALLERYUPLOAD_NUM_IMAGEFIELDS', 5)))}),
        (None, {'fields': ('caption',)}),
    )

    def __call__(self, request, url):
        if url is not None and url.endswith('progress'):
            return self.progress_view(request)
        else:
            return super(GalleryAdmin, self).__call__(request, url)

    def progress_view(self, request):
        progress_id = ''
        if 'X-Progress-ID' in request.GET:
            progress_id = request.GET['X-Progress-ID']
        elif 'X-Progress-ID' in request.META:
            progress_id = request.META['X-Progress-ID']
        if progress_id:
            from django.utils import simplejson
            cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
            data = cache.get(cache_key)
            return http.HttpResponse(simplejson.dumps(data))
        else:
            return http.HttpResponseServerError(
                'Server Error: You must provide X-Progress-ID header or query param.')


class ImageWidget(forms.FileInput):
    class Media:
        css = {'all': (settings.PHOTOLOGUEEXT_MEDIA_URL+'css/photologueext.css',)}

    def __init__(self, photo_size=None, attrs={}):
        self.photo_size = photo_size or getattr(
            settings, 'PHOTOLOGUEEXT_WIDGET_THUMBNAIL_SIZE', 'admin_thumbnail')
        super(ImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        from django.utils.translation import ugettext as _
        if hasattr(value, 'instance'):
            output = []
            if value and hasattr(value, "url"):
                output = (
                    '<div class="vPhotoField">'
                    '%s <a target="_blank" href="%s">'
                    '<img src="%s" /></a> <br />%s %s</div>' ) % (
                        _('Currently:'), value.url,
                        getattr(value.instance, 'get_%s_url' % self.photo_size)(),
                        _('Change:'),
                        super(ImageWidget, self).render(name, value, attrs))
            return safestring.mark_safe(output)
        else:
            return super(ImageWidget, self).render(name, value, attrs)


class PhotoModelForm(forms.ModelForm):
    class Meta:
        model = models.Photo

    image = forms.ImageField(widget=ImageWidget)


class PhotoAdmin(photologueadmin.PhotoAdmin):
    form = PhotoModelForm

    def __call__(self, request, url):
        if url is not None and url.endswith('/thumbnail'):
            return self.thumbnail_view(request, unquote(url[:-10]))
        else:
            return super(PhotoAdmin, self).__call__(request, url)

    def thumbnail_view(self, request, object_id, extra_context=None):
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            obj = None

        if obj is None:
            raise http.Http404(
                _('%(name)s object with primary key %(key)r does not exist.') % {
                    'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        return http.HttpResponseRedirect(obj.get_admin_thumbnail_url())
if getattr(settings, 'PHOTOLOGUEEXT_DISABLE_WATERMARKS', False):
    class PhotoSizeModelForm(forms.ModelForm):
        class Meta:
            model = models.PhotoSize
            exclude = ('watermark',)


    class PhotoSizeAdmin(admin.ModelAdmin):
        form = PhotoSizeModelForm
        list_display = (
            'name', 'width', 'height', 'crop', 'pre_cache', 'effect', 'increment_count')
        fieldsets = (
            (None, {'fields': ('name', 'width', 'height', 'quality')}),
            ('Options', {'fields': ('upscale', 'crop', 'pre_cache', 'increment_count')}),
            ('Enhancements', {'fields': ('effect',)}),
        )

    admin.site.unregister(models.Watermark)
    admin.site.unregister(models.PhotoSize)
    admin.site.register(models.PhotoSize, PhotoSizeAdmin)


admin.site.unregister(models.Gallery)
admin.site.unregister(models.Photo)
admin.site.unregister(models.GalleryUpload)

admin.site.register(models.Gallery, GalleryAdmin)
admin.site.register(models.Photo, PhotoAdmin)
