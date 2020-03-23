from django.urls import path
import accounts.views  
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', accounts.views.HomeView.as_view()),
    path('home', accounts.views.HomeView.as_view()),
    path('data-lab', accounts.views.LabView.as_view()),
    path('docs', accounts.views.DocsView.as_view()),
    path('forum', accounts.views.ForumView.as_view()),
    path('rates',accounts.views.RatesView.as_view()),
    path('ts_groups', accounts.views.TSGView.as_view()),
    path('raceSex', accounts.views.RaceSexView.as_view()),
    path('ses', accounts.views.SesView.as_view()),
    path('geo', accounts.views.GeoView.as_view()),
    path('geo1', accounts.views.GeoMenuView.as_view()),
    path('clustering', accounts.views.ClusteringView.as_view()),
    path('login', LoginView.as_view(template_name='accounts/login.html')), 
    path('logout', LogoutView.as_view(template_name='accounts/home.html')),
    path('register', accounts.views.RegisterView.as_view()),
    path('countytime', accounts.views.CountyTimeView.as_view()),
    path('temporalclustering', accounts.views.TempClusteringView.as_view()),
    path('secondarydata', accounts.views.SecondaryDataView.as_view()),
    path('geo_mapbox', accounts.views.MapboxView.as_view()),
]

