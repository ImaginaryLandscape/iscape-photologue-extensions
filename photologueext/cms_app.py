from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class Photologue(CMSApp):
    name = _("Photologue")
    urls = ["photologueext.urls"]

apphook_pool.register(Photologue)
