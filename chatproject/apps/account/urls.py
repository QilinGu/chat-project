from django.conf.urls import patterns, url
from . import api


account_v1 = patterns('',
    url(r'^$', api.AccountCreate.as_view(), name='user-account-create'),
    url(r'^(?P<username>[a-zA-Z]+)/$', api.AccountDetail.as_view(),
        name='user-account-detail'),
    url(r'^login/authtoken/$', api.ObtainExpiringAuthToken.as_view(),
        name='login-token'),
    url(r'^login/session/$', api.SessionAuthentication.as_view(),
        name='login-session'),
    url(r'^logout/session/$', api.SessionLogout.as_view(),
        name='logout-session'),
    url(r'^logout/authtoken/$', api.TokenLogout.as_view(),
        name='logout-token'),
    url(r'^forgot-my-password/$', api.ForgotMyPassword.as_view(),
        name='forgot-password')
)