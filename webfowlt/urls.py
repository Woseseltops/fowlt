from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',    
    (r'^$','webfowlt.fowlt.views.start'),
    (r'^info/?$','webfowlt.fowlt.views.about'),
    (r'^help/?$','webfowlt.fowlt.views.help'),
    (r'^process/?$','webfowlt.fowlt.views.process'),
    (r'^(?P<id>D[0-9a-f]+)/correct/?$','webfowlt.fowlt.views.correct'), 
    (r'^(?P<id>D[0-9a-f]+)/ignore/?$','webfowlt.fowlt.views.ignore'), 
    (r'^(?P<id>D[0-9a-f]+)/text/?$','webfowlt.fowlt.views.text'), 
    (r'^(?P<id>D[0-9a-f]+)/xml/?$','webfowlt.fowlt.views.xml'), 
    (r'^(?P<id>D[0-9a-f]+)/log/?$','webfowlt.fowlt.views.log'), 
    (r'^(?P<id>D[0-9a-f]+)/?$','webfowlt.fowlt.views.viewer'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
