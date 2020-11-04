import csv
import json
import logging
import os
from argparse import Namespace
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Dict

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from latex.build import PdfLatexBuilder
from ratelimit.decorators import ratelimit

from management.authentication import management_login_required
from management.forms import StartElectionForm, AddElectionForm, AddSessionForm, AddVotersForm, ApplicationUploadForm, \
    StopElectionForm, ChangeElectionPublicStateForm, AddTokensForm, CSVUploaderForm
from vote.models import Election, Application, Voter

logger = logging.getLogger('management.view')


class LoginView(auth_views.LoginView):
    # login view settings
    # https://docs.djangoproject.com/en/3.0/topics/auth/default/#django.contrib.auth.views.LoginView
    template_name = 'management/login.html'

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY, rate='10/h', method='POST'))
    def post(self, request, *args, **kwargs):
        ratelimited = getattr(request, 'limited', False)
        if ratelimited:
            return render(request, template_name='vote/ratelimited.html', status=429)
        return super().post(request, *args, **kwargs)


@management_login_required
def index(request):
    manager = request.user

    if request.GET.get("action") == "add_session":
        form = AddSessionForm(request=request, user=request.user, data=request.POST or None)
        if request.POST and form.is_valid():

            if request.POST.get("submit_type") != "test":
                ses = form.save()
                return redirect('management:session', ses.id)
            else:
                messages.add_message(request, messages.INFO, 'Test email sent.')

                test_session = Namespace(**{
                    "title": form.data['title'],
                    "invite_text": form.data['invite_text'],
                    "start_date": datetime.fromisoformat(form.data['start_date']) if form.data[
                        'start_date'] else datetime.now(),
                    'meeting_link': form.data['meeting_link'],
                })

                test_voter = Namespace(**{
                    "name": "Testname",
                    "email": form.data['email'],
                    "session": test_session,
                })
                test_voter.email_user = partial(Voter.email_user, test_voter)

                Voter.send_invitation(test_voter, "mock-up-access-token", manager.stusta_email)

        variables = {
            "{name}": "Voter's name if set",
            "{title}": "Session's title",
            "{access_code}": "Access code/token for the voter to login",
            "{login_url}": "URL which instantly logs user in",
            "{base_url}": "Basically vote.stusta.de",
            "{start_time}": "Start time if datetime is set",
            "{start_date}": "Start date if datetime is set",
            "{start_time_en}": "Start time in english format e.g. 02:23 PM",
            "{start_date_en}": "Start date in english format e.g. 12/12/2020",
            "{meeting_link}": "Meeting link if set"
        }
        return render(request, template_name='management/add_session.html', context={'form': form, 'vars': variables})

    context = {
        'sessions': manager.sessions.order_by('-pk')
    }
    return render(request, template_name='management/index.html', context=context)


@management_login_required
def session_detail(request, pk=None):
    manager = request.user
    session = manager.sessions.get(id=pk)
    context = {
        'session': session,
        'elections': session.elections.order_by('pk'),
        'voters': session.participants.all()
    }
    return render(request, template_name='management/session.html', context=context)


@management_login_required
def add_election(request, pk=None):
    # todo add chron job script that sends emails
    # todo apply changes to session
    manager = request.user
    session = manager.sessions.get(id=pk)
    context = {
        'session': session,
        'vars': {
            "{name}": "Voter's name if set",
            "{title}": "Session's title",
            "{url}": "URL to the election",
            "{end_time}": "End time if datetime is set",
            "{end_date}": "End date if datetime is set",
            "{end_time_en}": "End time in english format e.g. 02:23 PM",
            "{end_date_en}": "End date in english format e.g. 12/12/2020",
        }
    }

    form = AddElectionForm(session=session, request=request, user=manager, data=request.POST if request.POST else None)
    context['form'] = form
    if request.POST and form.is_valid():
        if request.POST.get("submit_type") == "test":
            messages.add_message(request, messages.INFO, 'Test email sent.')

            test_voter = Namespace(**{
                "name": "Testname",
                "email": form.cleaned_data['email'],
            })
            test_voter.email_user = partial(Voter.email_user, test_voter)
            test_election = Namespace(**{
                "title": form.cleaned_data['title'],
                "remind_text": form.cleaned_data['remind_text'],
                "pk": 1,
                "end_date": form.cleaned_data['end_date'],
            })

            Voter.send_reminder(test_voter, manager.stusta_email, test_election)
        else:
            form.save()
            return redirect('management:session', pk=session.pk)

    return render(request, template_name='management/add_election.html', context=context)


@management_login_required
def add_voters(request, pk):
    manager = request.user
    session = manager.sessions.get(pk=pk)
    context = {
        'session': session,
        'form': AddVotersForm(session=session)
    }
    form = AddVotersForm(session=session, data=request.POST if request.POST else None)
    context['form'] = form
    if request.POST and form.is_valid():
        form.save()
        return redirect('management:session', pk=pk)

    return render(request, template_name='management/add_voters.html', context=context)


@management_login_required
def add_tokens(request, pk):
    manager = request.user
    session = manager.sessions.get(pk=pk)
    context = {
        'session': session,
        'form': AddTokensForm(session=session)
    }
    form = AddTokensForm(session=session, data=request.POST if request.POST else None)
    context['form'] = form
    if request.POST and form.is_valid():
        form.save()
        return redirect('management:session', pk=pk)

    return render(request, template_name='management/add_tokens.html', context=context)


def _unpack(request, pk):
    manager = request.user
    election = Election.objects.get(pk=pk)
    session = election.session
    if not manager.sessions.filter(pk=session.pk).exists():
        raise Http404('Election does not exist/insufficient rights')
    return manager, election, session


@management_login_required
def election_detail(request, pk):
    manager, election, session = _unpack(request, pk)
    context = {
        'election': election,
        'session': session,
        'applications': election.applications.all(),
        'stop_election_form': StopElectionForm(instance=election),
        'start_election_form': StartElectionForm(instance=election),
        'election_upload_application_form': ChangeElectionPublicStateForm(instance=election)
    }

    if request.POST and request.POST.get('action') == 'close' and election.is_open:
        form = StopElectionForm(instance=election, data=request.POST)
        if form.is_valid():
            form.save()
        else:
            context['stop_election_form'] = form

    if request.POST and request.POST.get('action') == 'open':
        form = StartElectionForm(instance=election, data=request.POST)
        if form.is_valid():
            form.save()
            if election.send_emails_on_start:
                for voter in session.participants.all():
                    voter.send_reminder(session.managers.all().first().stusta_email, election)
        else:
            context['start_election_form'] = form

    if request.POST and request.POST.get('action') == 'publish':
        form = ChangeElectionPublicStateForm(instance=election, data=request.POST)
        if form.is_valid():
            form.save()
            context['election_upload_application_form'] = form

    return render(request, template_name='management/election.html', context=context)


@management_login_required
def election_upload_application(request, pk, application_id=None):
    manager, election, meeting = _unpack(request, pk)

    if not election.can_apply:
        messages.add_message(request, messages.ERROR, 'Applications are currently not accepted')
        return redirect('management:election', pk=pk)

    if application_id:
        try:
            instance = election.applications.get(pk=application_id)
        except Application.DoesNotExist:
            raise Http404('Application does not exist')
    else:
        instance = None

    if request.method == 'GET':
        form = ApplicationUploadForm(election, request, instance=instance)
    else:
        form = ApplicationUploadForm(election, request, data=request.POST, files=request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('management:election', election.pk)

    context = {
        'form': form,
        'election': election,
        'application_id': application_id,
        'with_email': False,
        'with_description': False,
    }
    return render(request, template_name='management/application.html', context=context)


@management_login_required
def election_delete_application(request, pk, application_id):
    e = Election.objects.filter(session__in=request.user.sessions.all(), pk=pk)
    if not e.exists():
        raise Http404('Election does not exist')
    e = e.first()
    try:
        a = e.applications.get(pk=application_id)
    except Application.DoesNotExist:
        raise Http404('Application does not exist')
    a.delete()
    return redirect('management:election', pk=pk)


@management_login_required
@csrf_protect
def delete_voter(request, pk):
    v = Voter.objects.filter(session__in=request.user.sessions.all(), pk=pk)
    if not v.exists():
        raise Http404('Voter does not exist')
    v = v.first()
    session = v.session
    v.delete()
    return redirect('management:session', pk=session.pk)


@management_login_required
@csrf_protect
def delete_election(request, pk):
    e = Election.objects.filter(session__in=request.user.sessions.all(), pk=pk)
    if not e.exists():
        raise Http404('Election does not exist')
    e = e.first()
    session = e.session
    e.delete()
    return redirect('management:session', pk=session.pk)


@management_login_required
@csrf_protect
def delete_session(request, pk):
    s = request.user.sessions.filter(pk=pk)
    if not s.exists():
        raise Http404('Session does not exist')
    s = s.first()
    s.delete()
    return redirect('management:index')


@management_login_required
def print_token(request, pk):
    session = request.user.sessions.filter(pk=pk)
    if not session.exists():
        raise Http404('Session does not exist')
    session = session.first()
    participants = session.participants
    tokens = [participant.new_access_token() for participant in participants.all() if participant.is_anonymous]
    if len(tokens) == 0:
        messages.add_message(request, messages.ERROR, 'No tokens have yet been generated.')
        return redirect('management:session', pk=session.pk)

    img = [qrcode.make('https://vote.stustanet.de' + reverse('vote:link_login', kwargs={'access_code': access_code}))
           for access_code in tokens]
    tmp_qr_path = '/tmp/wahlfang/qr_codes/session_{}'.format(session.pk)
    Path(tmp_qr_path).mkdir(parents=True, exist_ok=True)
    paths = []
    for idx, i in enumerate(img):
        path_i = os.path.join(tmp_qr_path, 'qr_{}.png'.format(idx))
        i.save(path_i)
        paths.append(path_i)
    zipped = [{'path': path, 'token': token} for path, token in zip(paths, tokens)]
    context = {
        'session': session,
        'tokens': zipped
    }

    template_name = 'vote/tex/invitation.tex'
    pdf = generate_pdf(template_name, context, tmp_qr_path)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="tokenlist.pdf"'
    response.write(bytes(pdf))
    return response


def generate_pdf(template_name: str, context: Dict, tex_path: str):
    template = get_template(template_name).render(context).encode('utf8')
    pdf = PdfLatexBuilder(pdflatex='pdflatex').build_pdf(template, texinputs=[tex_path, ''])
    return pdf


@management_login_required
def import_csv(request, pk):
    session = request.user.sessions.filter(pk=pk)
    if not session.exists():
        raise Http404('Session does not exist')
    session = session.first()

    if request.method == 'POST':
        form = CSVUploaderForm(session, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect('management:session', session.pk)
    else:
        form = CSVUploaderForm(session)
    return render(request, 'management/import_csv.html', {'form': form, 'session': session})


@management_login_required
def export_csv(request, pk):
    e = Election.objects.filter(session__in=request.user.sessions.all(), pk=pk)
    if not e.exists():
        raise Http404('Election does not exist')
    e = e.first()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="results.csv"'

    writer = csv.writer(response)
    header = ['#', 'applicant', 'email', 'yes', 'no', 'abstention']
    if e.max_votes_yes is not None:
        header.append('elected')
    writer.writerow(header)
    for i in range(len(e.election_summary)):
        a = e.election_summary[i]
        row = [i+1, a.get_display_name(), a.email, a.votes_accept, a.votes_reject, a.votes_abstention]
        if e.max_votes_yes is not None:
            row.append(True if i < e.max_votes_yes else False)
        writer.writerow(row)

    return response


@management_login_required
def export_json(request, pk):
    e = Election.objects.filter(session__in=request.user.sessions.all(), pk=pk)
    if not e.exists():
        raise Http404('Election does not exist')
    e = e.first()

    json_data = []
    for i in range(len(e.election_summary)):
        a = e.election_summary[i]
        appl_data = {
            "applicant": a.get_display_name(),
            "email": a.email,
            "yes": a.votes_accept,
            "no": a.votes_reject,
            "abstention": a.votes_abstention
        }
        if e.max_votes_yes is not None:
            appl_data["elected"] = True if i < e.max_votes_yes else False
        json_data.append(appl_data)

    json_str = json.dumps(json_data)

    response = HttpResponse(json_str, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=result.json'

    return response
