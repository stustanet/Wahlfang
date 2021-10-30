import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from management.models import ElectionManager
from vote.models import Voter


class VoteAPIConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group = await database_sync_to_async(self.get_session_key)()  # pylint: disable=W0201
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def send_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update',
            'table': event['table'],
            'instance_id': event['instance_id']
        }))

    def get_session_key(self):
        # if 'uuid' in self.scope['url_route']['kwargs']:
        #     uuid = self.scope['url_route']['kwargs']['uuid']
        #     session = Session.objects.get(spectator_token=uuid)
        # else:
        if isinstance(self.scope['user'], Voter):
            session = self.scope['user'].session
            return f'api-vote-session-{session.pk}'
        else:
            raise RuntimeError('error, trying to connect to voter websocket with an election manager')


class ManagementAPIConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group = await database_sync_to_async(self.get_manager_key)()  # pylint: disable=W0201
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def send_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update',
            'table': event['table'],
            'instance_id': event['instance_id']
        }))

    def get_manager_key(self):
        if isinstance(self.scope['user'], ElectionManager):
            manager_key = self.scope['user'].id
            return f'api-election-manager-{manager_key}'
        else:
            raise RuntimeError('error, trying to connect to voter websocket with an election manager')
