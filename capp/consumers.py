from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .translation import Translator
import logging
from asgiref.sync import sync_to_async
from .models import Room, Message, UserProfile, TranslationMetric
from channels.exceptions import StopConsumer
from django.utils import timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translator = None
        self.executor = None
        self.room = None
        self.user = None
        self.room_group_name = None
        self.room_id = None

    async def initialize(self):
        """Initialize resources that need an event loop"""
        if self.translator is None:
            from .translation import Translator
            self.translator = Translator()  # Will reuse existing instance
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=3)

    async def connect(self):
        try:
            self.room_id = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_id}'
            self.user = self.scope['user']

            # Initialize resources
            await self.initialize()
            
            # Get room instance
            self.room = await self.get_room()
            if not self.room:
                await self.close()
                return

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            # Send room history in a separate task
            asyncio.create_task(self.send_room_history())
            
            logger.info(f"User {self.user.username} connected to room {self.room_id}")

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if self.room_group_name:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            
            # Clean up resources
            if self.executor:
                self.executor.shutdown(wait=False)
                self.executor = None

            logger.info(f"User {self.user.username if self.user else 'Unknown'} disconnected from room {self.room_id}")

        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")
        
        raise StopConsumer()

    async def send_room_history(self):
        """Send recent chat history to newly connected users"""
        try:
            # Get recent messages
            recent_messages = await self.get_recent_messages()
            
            # Send each message
            for message in recent_messages:
                # Get user's preferred language
                user_language = await self.get_user_language()
                
                # Translate if necessary
                translated = None
                if message.language != user_language:
                    translated = await self.translate_message(
                        message.content,
                        message.language,
                        user_language
                    )

                # Send message
                await self.send(text_data=json.dumps({
                    'type': 'chat_message',
                    'message': message.content,
                    'translated_message': translated if translated else message.content,
                    'username': message.user.username,
                    'source_language': message.language,
                    'target_language': user_language,
                    'timestamp': str(message.date_added)
                }))

        except Exception as e:
            logger.error(f"Error sending room history: {str(e)}")

    @sync_to_async
    def get_recent_messages(self):
        """Get recent messages from the database"""
        return list(Message.objects.filter(room=self.room)
                   .select_related('user')
                   .order_by('-date_added')[:50])

    @sync_to_async
    def get_room(self):
        try:
            return Room.objects.get(id=int(self.room_id))
        except Room.DoesNotExist:
            return None

    async def receive(self, text_data):
        if not self.translator or not self.executor:
            await self.initialize()
            
        try:
            data = json.loads(text_data)
            message = data['message']
            username = data['username']
            source_language = data['source_language']
            
            # Get room members' languages
            room_members_languages = await self.get_room_members_languages()
            
            # Create translations for each unique target language
            translations = {}
            tasks = []
            
            # Create translation tasks
            for target_language in set(room_members_languages.values()):
                if target_language != source_language:
                    translated = await self.translate_message(message, source_language, target_language)
                    translations[target_language] = translated
            
            # Save original message
            await self.save_message(username, message, source_language)
            
            # Broadcast message with translations
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'translations': translations,
                    'username': username,
                    'source_language': source_language,
                    'timestamp': str(timezone.now())
                }
            )
            
        except Exception as e:
            logger.error(f"Receive error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def chat_message(self, event):
        try:
            # Get user's preferred language
            user_language = await self.get_user_language()
            
            # Get appropriate translation for this user
            translated_message = event['translations'].get(
                user_language,
                event['message']  # Default to original if no translation
            )
            
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': event['message'],
                'translated_message': translated_message,
                'username': event['username'],
                'source_language': event['source_language'],
                'target_language': user_language,
                'timestamp': event['timestamp']
            }))
            
        except Exception as e:
            logger.error(f"Chat message error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def translate_message(self, message, source_language, target_language):
        """Translate a single message"""
        try:
            loop = asyncio.get_running_loop()
            translated = await loop.run_in_executor(
                self.executor,
                self.translator.translate_text,
                message,
                source_language,
                target_language
            )
            return translated
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return message

    @sync_to_async
    def save_message(self, username, content, language):
        from django.contrib.auth.models import User
        user = User.objects.get(username=username)
        Message.objects.create(
            room=self.room,
            user=user,
            content=content,
            language=language
        )

    @sync_to_async
    def get_user_language(self):
        if hasattr(self.user, 'userprofile'):
            return self.user.userprofile.preferred_language
        return 'eng_Latn'

    @sync_to_async
    def get_room_members_languages(self):
        """Get language preferences for all users in the room"""
        room_messages = Message.objects.filter(room=self.room)
        users = set(msg.user for msg in room_messages)
        
        languages = {}
        for user in users:
            try:
                profile = UserProfile.objects.get(user=user)
                languages[user.username] = profile.preferred_language
            except UserProfile.DoesNotExist:
                languages[user.username] = 'eng_Latn'
                
        return languages
