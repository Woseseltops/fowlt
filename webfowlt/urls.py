from django.conf.urls import patterns, url, include
from django.conf import settings

urlpatterns = patterns('',    
    (r'^$','fowlt.views.start'),
    (r'^early/?$','fowlt.views.start'),
    (r'^info/?$','fowlt.views.about'),
    (r'^redditbot/?$','fowlt.views.redditbot'),
    (r'^help/?$','fowlt.views.help'),
    (r'^process/?$','fowlt.views.process'),
    (r'^(?P<id>D[0-9a-f]+)/correct/?$','fowlt.views.correct'), 
    (r'^(?P<id>D[0-9a-f]+)/ignore/?$','fowlt.views.ignore'), 
    (r'^(?P<id>D[0-9a-f]+)/text/?$','fowlt.views.text'), 
    (r'^(?P<id>D[0-9a-f]+)/xml/?$','fowlt.views.xml'), 
    (r'^(?P<id>D[0-9a-f]+)/log/?$','fowlt.views.log'), 
    (r'^(?P<id>D[0-9a-f]+)/?$','fowlt.views.viewer'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
