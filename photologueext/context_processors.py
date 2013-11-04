from photologueext import settings

def media(request):
    """
    Adds media-related context variables to the context.
    """
    PHOTOLOGUEEXT_MEDIA_URL = settings.PHOTOLOGUEEXT_MEDIA_URL

    return {'PHOTOLOGUEEXT_MEDIA_URL': PHOTOLOGUEEXT_MEDIA_URL}
