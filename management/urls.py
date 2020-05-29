from django.urls import path, re_path
from django.contrib.auth import views as auth_views

from management import views

app_name = 'management'

urlpatterns = [
    path('', views.index, name='index'),
    path('meeting/<int:pk>/add_voters', views.add_voters, name='add_voters'),
    path('meeting/<int:pk>/add_election', views.add_election, name='add_election'),
    path('meeting/<int:pk>', views.session_detail, name='session'),
    path('election/<int:pk>/add_application', views.election_upload_application, name='add_application'),
    path('election/<int:pk>/edit/<int:application_id>', views.election_upload_application, name='edit_application'),
    path('election/<int:pk>', views.election_detail, name='election'),
    path('election/<int:pk>/voters_list', views.voters_list, name='voters_list'),
    path('election/<int:pk>/invalidate_voter', views.invalidate_voter, name='invalidate_voter'),

    # account management stuff
    path('login', auth_views.LoginView.as_view(
        template_name='management/login.html'
    ), name='login'),
    path('logout', auth_views.LogoutView.as_view(
        next_page='management:login',
    ), name='logout')
]
