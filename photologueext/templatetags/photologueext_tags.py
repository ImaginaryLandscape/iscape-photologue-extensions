from django import template
from django.db.models import get_model

register = template.Library()

class NextPreviousInGalleryNode(template.Node):
    def __init__(self, next_or_previous, photo, gallery, asvar):
        self.next_or_previous = next_or_previous
        self.photo = template.Variable(photo)
        self.gallery = template.Variable(gallery)
        self.asvar = asvar

    def render(self, context):
        photo = self.photo.resolve(context)
        gallery = self.gallery.resolve(context)
        context[self.asvar] = getattr(
            photo, 'get_%s_in_gallery' % self.next_or_previous)(gallery)
        return u''

def next_in_gallery(parser, token):
    tokens = token.split_contents()
    if len(tokens) != 5:
        raise template.TemplateSyntaxError('incorrect number of arguments')
    tag, photo, gallery, x, asvar = tokens
    return NextPreviousInGalleryNode('next', photo, gallery, asvar)


def previous_in_gallery(parser, token):
    tokens = token.split_contents()
    if len(tokens) != 5:
        raise template.TemplateSyntaxError('incorrect number of arguments')
    tag, photo, gallery, x, asvar = tokens
    return NextPreviousInGalleryNode('previous', photo, gallery, asvar)


class GalleryObjectNode(template.Node):

    def __init__(self, gallery_name, count, var_name):
        self.gallery_name = gallery_name
        self.count = int(count)
        self.var_name = var_name

    def render(self, context):
        try:
            model = get_model('photologue', 'Gallery')
        except:
            raise TemplateSyntaxError, "Failed to retrieve model"

        try:
            gallery = model.objects.get(title_slug=self.gallery_name)
        except:
            # if the gallery doesn't exist, fetch a random one
            gallery = model.objects.order_by("?")[:1].get()

        ## Then we grab the images from the galleries, and randomly sort them
        ## The random sorting is to confuse them so they don't escape...
        images = gallery.photos.all()
        images = images.order_by("?")

        ## Now we make sure we have the proper quantity of images
        if images.count() > self.count:
            images = images[:self.count]

        context.update({self.var_name: images, 'gallery': gallery})
        return ''

def fetch_gallery(parser, token):
    """
    TODO: MORE images
    """
    try:
        tag_name, gallery_name, count, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("Object Tag requires 3 variables")

    return GalleryObjectNode(gallery_name[1:-1], count[1:-1], var_name[1:-1])

register.tag('next_in_gallery', next_in_gallery)
register.tag('previous_in_gallery', previous_in_gallery)
register.tag('fetch_gallery', fetch_gallery)
