from photologue import models


def _index(self):
    for photo in self.public().filter(tags__icontains='index'):
        if 'index' in photo.tags.split():
            return photo
    photos = self.sample(count=1)
    if photos:
        return photos[0]


models.Gallery.index_photo = _index
