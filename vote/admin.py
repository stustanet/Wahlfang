from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import Election
from .models import Application
from .models import Voter


class VoterCreationForm(UserCreationForm):
    class Meta:
        model = Voter
        fields = ('voter_id',)
        field_classes = {}


class VoterChangeForm(UserChangeForm):
    class Meta:
        model = Voter
        fields = ('voter_id',)
        field_classes = {}


class VoterAdmin(UserAdmin):
    add_form = VoterCreationForm
    form = VoterChangeForm
    model = Voter
    fieldsets = (
        (None, {'fields': ('voter_id', 'password', 'election',)}),
        # (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Personal info'), {'fields': ('email',)}),
        (_('Status'), {'fields': ('voted',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('voter_id', 'password1', 'password2', 'election')}
        ),
        (_('Personal info'), {'fields': ('email',)}),
    )
    list_display = ('voter_id', 'election', 'voted',)
    list_filter = ('voted',)
    search_fields = ('voter_id', 'election', 'email',)
    ordering = ('voter_id',)
    filter_horizontal = tuple()


admin.site.register(Election)
admin.site.register(Application)
admin.site.register(Voter, VoterAdmin)
