from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',    
    (r'^$','webvalkuil.valkuil.views.start'),
    (r'^info/?$','webvalkuil.valkuil.views.about'),
    (r'^help/?$','webvalkuil.valkuil.views.help'),
    (r'^process/?$','webvalkuil.valkuil.views.process'),
    (r'^(?P<id>D[0-9a-f]+)/correct/?$','webvalkuil.valkuil.views.correct'), 
    (r'^(?P<id>D[0-9a-f]+)/ignore/?$','webvalkuil.valkuil.views.ignore'), 
    (r'^(?P<id>D[0-9a-f]+)/text/?$','webvalkuil.valkuil.views.text'), 
    (r'^(?P<id>D[0-9a-f]+)/xml/?$','webvalkuil.valkuil.views.xml'), 
    (r'^(?P<id>D[0-9a-f]+)/log/?$','webvalkuil.valkuil.views.log'), 
    (r'^(?P<id>D[0-9a-f]+)/?$','webvalkuil.valkuil.views.viewer'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
