from contextlib import asynccontextmanager
import websockets
import json
import base64
import os
import shutil
from curl_cffi.requests import Session
from pydub import AudioSegment
from io import BytesIO
from easygoogletranslate import EasyGoogleTranslate as esgt

# ______         ______ _______ _______ ______ 
# |   __ \ __ __ |      |   _   |_     _|__    |
# |    __/|  |  ||   ---|       |_|   |_|    __|
# |___|   |___  ||______|___|___|_______|______|
#         |_____|                                 

                                                           
# BUILD BY @Falco_TK    (https://github.com/FalcoTK)
# CODE  BY @kramcat     (https://github.com/kramcat)
# CODE  BY @background  (https://github.com/backaround)

# PLEASE IF YOU HAVE SOMTING WRONG DM ME IN DISCORD ASAP! (discord: tokaifalco_)                                                  
# ==================================================

__all__ = ['PyCAI2', 'PyAsyncCAI2']


class PyCAI2EX(Exception):
    pass

class ServerError(PyCAI2EX):
    pass

class LabelError(PyCAI2EX):
    pass

class AuthError(PyCAI2EX):
    pass

class PostTypeError(PyCAI2EX):
    pass

class PyAsyncCAI2:
    def __init__(
        self, token: str = None, plus: bool = False
    ):
        self.token = token
        self.plus = plus
        if plus: sub = 'plus'
        else: sub = 'beta'

        self.session = Session(
            headers={
                'User-Agent': 'okhttp/5.0.0-SNAPSHOT'
            }
        )

        setattr(self.session, 'url', f'https://{sub}.character.ai/')
        setattr(self.session, 'token', token)
        
        self.chat = self.chat(token, self.session)
        self.chat2 = self.chat2(token, None, self.session)

    async def request(
        url: str, session: Session,
        *, token: str = None, method: str = 'GET',
        data: dict = None, split: bool = False,
        split2: bool = False, neo: bool = False
    ):

        if neo:
            link = f'https://neo.character.ai/{url}'
        else:
            link = f'{session.url}{url}'

        if token == None:
            key = session.token
        else:
            key = token

        headers = {
            'Authorization': f'Token {key}',
        }

        if method == 'GET':
            response = session.get(
                link, headers=headers
            )

        elif method == 'POST':
            response = session.post(
                link, headers=headers, json=data
            )

        elif method == 'PUT':
            response = session.put(
                link, headers=headers, json=data
            )


        if split:
            data = json.loads(response.text.split('\n')[-2])
        elif split2:
            lines = response.text.strip().split('\n')
            data = [json.loads(line) for line in lines if line.strip()] # List
        else:
            data = response.json()

        if str(data).startswith("{'command': 'neo_error'"):
            raise ServerError(data['comment'])
        elif str(data).startswith("{'detail': 'Auth"):
            raise AuthError('Invalid token')
        elif str(data).startswith("{'status': 'Error"):
            raise ServerError(data['status'])
        elif str(data).startswith("{'error'"):
            raise ServerError(data['error'])
        else:
            return data

    async def ping(self):
        return self.session.get(
            'https://neo.character.ai/ping/'
        ).json()

    @asynccontextmanager
    async def connect(self, token: str = None):
        try:
            if token == None: key = self.token
            else: key = token

            setattr(self.session, 'token', key)

            try:
                self.ws = await websockets.connect(
                    'wss://neo.character.ai/ws/',
                     extra_headers = {
                        'Cookie': f'HTTP_AUTHORIZATION="Token {key}"',
                    }  
                )
            except websockets.exceptions.InvalidStatusCode:
                raise AuthError('Invalid token')
            
            yield PyAsyncCAI2.chat2(key, self.ws, self.session)
        finally:
            await self.ws.close()  

    class chat:
        def __init__(
            self, token: str, session: Session
        ):
            self.token = token
            self.session = session

        async def voice(
            self, char: str, room_id: str, 
            text: str, voice_pth:str, *, token: str = None,
            **kwargs
        ):
            response = await PyAsyncCAI2.request(
                'chat/streaming/', self.session,
                token=token, method='POST', split2='True',
                data={
                    "character_external_id": char,
                    "enable_tti": None,
                    "filter_candidates": None,
                    "give_room_introductions": True,
                    "history_external_id": room_id,
                    "image_description": "",
                    "image_description_type": "",
                    "image_origin_type": "",
                    "image_rel_path": "",
                    "initial_timeout": None,
                    "insert_beginning": None,
                    "is_proactive": False,
                    "mock_response": False,
                    "model_properties_version_keys": "",
                    "model_server_address": None,
                    "model_server_address_exp_chars": None,
                    "num_candidates": 1,
                    "override_prefix": None,
                    "override_rank": None,
                    "parent_msg_uuid": None,
                    "prefix_limit": None,
                    "prefix_token_limit": None,
                    "rank_candidates": None,
                    "ranking_method": "random",
                    "retry_last_user_msg_uuid": None,
                    "rooms_prefix_method": "",
                    "seen_msg_uuids": [],
                    "staging": False,
                    "stream_every_n_steps": 16,
                    "stream_params": None,
                    "text": text,
                    "tgt": None,
                    "traffic_source": None,
                    "unsanitized_characters": None,
                    "voice_enabled": True,
                    **kwargs
                }
            )

            merged_audio = AudioSegment.silent(duration=0)
            for i, json_parsed in enumerate(response):
                replies = json_parsed.get("replies", [])

                for reply in replies:
                    text = reply.get("text", "")

                encode = json_parsed.get("speech", "")
                if encode:
                    decode = base64.b64decode(encode)
                    audio = AudioSegment.from_file(BytesIO(decode))
                    merged_audio += audio
                else:
                    print(f"Skipping .json #{i}") # Intentionally skips due to how c.ai api works

            # Exporting the merged audio to voice.mp3
            merged_audio.export("voice.mp3", format="mp3")
            voice_path = os.path.abspath('voice.mp3')
            shutil.move(voice_path, os.path.join(voice_pth, os.path.basename(voice_path)))
            
            return text 

        async def next_message(
            self, history_id: str, parent_msg_uuid: str,
            tgt: str, *, token: str = None, **kwargs
        ):
            response = await PyAsyncCAI2.request(
                'chat/streaming/', self.session,
                token=token, method='POST', split=True,
                data={
                    'history_external_id': history_id,
                    'parent_msg_uuid': parent_msg_uuid,
                    'tgt': tgt,
                    **kwargs
                }
            )

        async def get_histories(
            self, char: str, *, number: int = 50,
            token: str = None
        ):
            return await PyAsyncCAI2.request(
                'chat/character/histories_v2/', self.session,
                token=token, method='POST',
                data={'external_id': char, 'number': number},
            )

        async def send_message(
            self, char: str, text: str,
            *, token: str = None, **kwargs
        ):
            r = await PyAsyncCAI2.request('chat/history/continue/', self.session,token=token, method='POST',data={'character_external_id': char})
            external = r['external_id']
            participants = r['participants']
            if not participants[0]['is_human']:
                tgt = participants[0]['user']['username']
            else:
                tgt = participants[1]['user']['username']
            
            r = await PyAsyncCAI2.request(
                'chat/streaming/', self.session,
                token=token, method='POST', split=True,
                data={
                    'history_external_id': external,
                    'tgt': tgt,
                    'text': text,
                    **kwargs
                }
            )
            print(r)
            response = r['replies'][0]['text']
            return response
        

        async def delete_message(
            self, history_id: str, uuids_to_delete: list,
            *, token: str = None, **kwargs
        ):
            return await PyAsyncCAI2.request(
                'chat/history/msgs/delete/', self.session,
                token=token, method='POST',
                data={
                    'history_id': history_id,
                    'uuids_to_delete': uuids_to_delete,
                    **kwargs
                }
            )

        async def new_chat(
            self, char: str, *, token: str = None
        ):
            return await PyAsyncCAI2.request(
                'chat/history/create/', self.session,
                token=token, method='POST',
                data={
                    'character_external_id': char
                }
            )

    class chat2:
        """Managing a chat2 with a character

        chat.next_message('CHAR', 'CHAT_ID', 'PARENT_ID')
        chat.send_message('CHAR', 'CHAT_ID', 'TEXT', {AUTHOR})
        chat.next_message('CHAR', 'MESSAGE')
        chat.new_chat('CHAR', 'CHAT_ID', 'CREATOR_ID')
        chat.get_histories('CHAR')
        chat.get_chat('CHAR')
        chat.get_history('CHAT_ID')
        chat.rate(RATE, 'CHAT_ID', 'TURN_ID', 'CANDIDATE_ID')
        chat.delete_message('CHAT_ID', 'TURN_ID')

        """
        def __init__(
            self, token: str,
            ws: websockets.WebSocketClientProtocol,
            session: Session
        ):
            self.token = token
            self.session = session
            self.ws = ws


        async def transl(text:str, target:str, source:str):
            translator = esgt(
            source_language=source,
            target_language=target)

            resoult = translator.translate(text)

            return resoult

        async def next_message(
            self, char: str, parent_msg_uuid: str,token:str = None
        ):
            setup = await PyAsyncCAI2.request(f'chats/recent/{char}', self.session,token=token,method='GET',neo=True)
            chat_id = setup['chats'][0]['chat_id']
            await self.ws.send(json.dumps({
                'command': 'generate_turn_candidate',
                'payload': {
                    'character_id': char,
                    'turn_key': {
                        'turn_id': parent_msg_uuid,
                        'chat_id': chat_id
                    }
                }
            }))

            while True:
                response = json.loads(await self.ws.recv())
                try: response['turn']
                except: raise ServerError(response['comment'])
                
                if not response['turn']['author']['author_id'].isdigit():
                    try: is_final = response['turn']['candidates'][0]['is_final']
                    except: pass
                    else: return response

        async def create_img(
            self, char: str, chat_id: str, text: str,
            author_name:str, Return_img: bool = True, Return_all: bool = False, *, turn_id: str = None, candidate_id: str = None, token:str = None
        ):
            json_out = await PyAsyncCAI2.request(f'chats/recent/{char}', self.session,token=token,method='GET',neo=True)
            chat_id = json_out['chats'][0]['chat_id']
            creator_id = json_out['chats'][0]['creator_id']
              
            
            
            if turn_id != None and candidate_id != None:
                message['update_primary_candidate'] = {
                    'candidate_id': candidate_id,
                    'turn_key': {
                        'turn_id': turn_id,
                        'chat_id': chat_id
                    }
                }

            message = {
                'command': 'create_and_generate_turn',
                'payload': {
                    'character_id': char,
                    'turn': {
                        'turn_key': {'chat_id': chat_id},
                        "author": {
                                "author_id": creator_id,
                                "is_human": True,
                                "name   ": author_name},
                        'candidates': [{'raw_content': text}]
                    }
                }
            }

            await self.ws.send(json.dumps(message))
            
            while True:
                response = json.loads(await self.ws.recv())
                try: response['turn']
                except: raise ServerError(response['comment'])
                
                if not response['turn']['author']['author_id'].isdigit():
                    try: is_final = response['turn']['candidates'][0]['is_final']
                    except: pass
                    else:
                        if Return_all:
                            r_in = response['turn']['candidates'][0]['raw_content']
                            img_in = response['turn']['candidates'][0]['tti_image_rel_path']  # Perhatikan perubahan indeks ke 0 di sini
                            results = f"{r_in}\n{img_in}"
                            return results
                        if Return_img:
                            r = response['turn']['candidates'][0]['tti_image_rel_path']
                            return r
                        



        async def send_message(
            self, char: str,
            text: str, author_name:str,
            *, turn_id: str = None,token:str = None,
            candidate_id: str = None, Return_name: bool = False
        ):  

            json_out = await PyAsyncCAI2.request(f'chats/recent/{char}', self.session,token=token,method='GET',neo=True)
            chat_id = json_out['chats'][0]['chat_id']
            creator_id = json_out['chats'][0]['creator_id']
              
            message = {
                'command': 'create_and_generate_turn',
                'payload': {
                    'character_id': char,
                    'turn': {
                        'turn_key': {'chat_id': chat_id},
                         "author": {
                                "author_id": creator_id,
                                "is_human": True,
                                "name   ": author_name},
                        'candidates': [{'raw_content': text}]
                    }
                }
            }

            if turn_id != None and candidate_id != None:
                message['update_primary_candidate'] = {
                    'candidate_id': candidate_id,
                    'turn_key': {
                        'turn_id': turn_id,
                        'chat_id': chat_id
                    }
                }
        
            await self.ws.send(json.dumps(message))

            while True:
                response = json.loads(await self.ws.recv())
                try: response['turn']
                except: raise ServerError(response['comment'])
                
                if not response['turn']['author']['author_id'].isdigit():
                    try: is_final = response['turn']['candidates'][0]['is_final']
                    except: pass
                    else:
                        if Return_name:
                            r_in = response['turn']['candidates'][0]['raw_content']
                            n_in = response['turn']['author']["name"]
                            r = f"({n_in}) {r_in}"
                            return r
                        else:
                            r = response['turn']['candidates'][0]['raw_content']
                            return r
        

        async def new_chat(
            self, char: str, *, with_greeting: bool = True, token:str =None
        ):
            json_out = await PyAsyncCAI2.request(f'chats/recent/{char}', self.session,token=token,method='GET',neo=True)
            chat_id = json_out['chats'][0]['chat_id']
            creator_id = json_out['chats'][0]['creator_id']

            message = {
                'command': 'create_chat',
                'payload': {
                    'chat': {
                        'chat_id': chat_id,
                        'creator_id': creator_id,
                        'visibility': 'VISIBILITY_PRIVATE',
                        'character_id': char,
                        'type': 'TYPE_ONE_ON_ONE'
                    },
                    'with_greeting': with_greeting
                }
            }
            await self.ws.send(json.dumps(message))

            response = json.loads(await self.ws.recv())
            print(response)

            try: response['chat']
            except KeyError:
                raise ServerError(response['comment'])
            else:
                answer = json.loads(await self.ws.recv())
                return response, answer
        

        async def get_histories(
            self, char: str = None, *,
            preview: int = 2, token: str = None
        ):
            return await PyAsyncCAI2.request(
                f'chats/?character_ids={char}'
                f'&num_preview_turns={preview}',
                self.session, token=token, neo=True
            )


        async def get_history(self, char: str, *, token: str = None):
            json_out = await PyAsyncCAI2.request(f'chats/recent/{char}', self.session, token=token, method='GET', neo=True)
            chat_id = json_out['chats'][0]['chat_id']
            r = await PyAsyncCAI2.request(f'turns/{chat_id}/', self.session, token=token, neo=True)
            turn_out = [{"turn_id": turn['turn_key']['turn_id'], "raw_content": turn['candidates'][0]['raw_content']} for turn in r['turns']]
            output = [f'["{turn["turn_id"]}", "{turn["raw_content"]}"]' for turn in turn_out]
            
            return output
                    

        async def delete_message(
            self, char: str, turn_ids: list,
            *, token: str = None, **kwargs
        ):
            json_out = await PyAsyncCAI2.request(f'chats/recent/{char}', self.session, token=token, method='GET', neo=True)
            chat_id = json_out['chats'][0]['chat_id']
            payload = {
                'command':'remove_turns',
                'payload': {
                    'chat_id': chat_id,
                    'turn_ids': turn_ids
                }
            }
            await self.ws.send(json.dumps(payload))
            return json.loads(await self.ws.recv())
        

        async def get_avatar(self, char:str,*, token:str = None):
            json_out = await PyAsyncCAI2.request(f'chats/recent/{char}', self.session, token=token, method='GET', neo=True)
            avatar_url = json_out["chats"][0]["character_avatar_uri"]
            full_link = f"https://characterai.io/i/80/static/avatars/{avatar_url}"
            return full_link
            


# =================================================================================================================
# ______         ______ _______ _______ ______ 
# |   __ \ __ __ |      |   _   |_     _|__    |
# |    __/|  |  ||   ---|       |_|   |_|    __|
# |___|   |___  ||______|___|___|_______|______|
#         |_____|                                 

                                                           
# BUILD BY @Falco_TK (https://github.com/FalcoTK)
# CODE  BY @kramcat  (https://github.com/kramcat)

# PyCAI V1: https://github.com/kramcat/CharacterAI (docs: https://pycai.gitbook.io/welcome/)
# PyCAI V2: (docs: )

# PLEASE IF YOU HAVE SOMTING WRONG DM ME IN DISCORD ASAP! (discord: tokaifalco_)                                                  
# ==================================================


class PyCAI2:
    def __init__(
        self, token: str = None, plus: bool = False
    ):
        self.token = token
        self.plus = plus
        if plus: sub = 'plus'
        else: sub = 'beta'

        self.session = Session(
            headers={
                'User-Agent': 'okhttp/5.0.0-SNAPSHOT'
            }
        )

        setattr(self.session, 'url', f'https://{sub}.character.ai/')
        setattr(self.session, 'token', token)
        
        self.chat = self.chat(token, self.session)
        self.chat2 = self.chat2(token, None, self.session)

    def request(
        url: str, session: Session,
        *, token: str = None, method: str = 'GET',
        data: dict = None, split: bool = False,
        split2: bool = False, neo: bool = False, 
    ):
        

        if neo:
            link = f'https://neo.character.ai/{url}'
        else:
            link = f'{session.url}{url}'

        if token == None:
            key = session.token
        else:
            key = token

        headers = {
            'Authorization': f'Token {key}',
        }

        if method == 'GET':
            response = session.get(
                link, headers=headers
            )

        elif method == 'POST':
            response = session.post(
                link, headers=headers, json=data
            )

        elif method == 'PUT':
            response = session.put(
                link, headers=headers, json=data
            )

        if split:
            data = json.loads(response.text.split('\n')[-2])
        elif split2:
            lines = response.text.strip().split('\n')
            data = [json.loads(line) for line in lines if line.strip()] # List
        else:
            data = response.json()

        if str(data).startswith("{'command': 'neo_error'"):
            raise ServerError(data['comment'])
        elif str(data).startswith("{'detail': 'Auth"):
            raise AuthError('Invalid token')
        elif str(data).startswith("{'status': 'Error"):
            raise ServerError(data['status'])
        elif str(data).startswith("{'error'"):
            raise ServerError(data['error'])
        else:
            return data

    def ping(self):
        return self.session.get(
            'https://neo.character.ai/ping/'
        ).json()

            


    class chat:
        def __init__(
            self, token: str, session: Session
        ):
            self.token = token
            self.session = session

        def voice(
            self, characterId: str, room_id: str, 
            text: str,voice_pth:str, *, token: str = None,
            **kwargs
        ):
            response = PyCAI2.request(
                'chat/streaming/', self.session,
                token=token, method='POST', split2='True',
                data={
                    "character_external_id": characterId,
                    "enable_tti": None,
                    "filter_candidates": None,
                    "give_room_introductions": True,
                    "history_external_id": room_id,
                    "image_description": "",
                    "image_description_type": "",
                    "image_origin_type": "",
                    "image_rel_path": "",
                    "initial_timeout": None,
                    "insert_beginning": None,
                    "is_proactive": False,
                    "mock_response": False,
                    "model_properties_version_keys": "",
                    "model_server_address": None,
                    "model_server_address_exp_chars": None,
                    "num_candidates": 1,
                    "override_prefix": None,
                    "override_rank": None,
                    "parent_msg_uuid": None,
                    "prefix_limit": None,
                    "prefix_token_limit": None,
                    "rank_candidates": None,
                    "ranking_method": "random",
                    "retry_last_user_msg_uuid": None,
                    "rooms_prefix_method": "",
                    "seen_msg_uuids": [],
                    "staging": False,
                    "stream_every_n_steps": 16,
                    "stream_params": None,
                    "text": text,
                    "tgt": None,
                    "traffic_source": None,
                    "unsanitized_characters": None,
                    "voice_enabled": True,
                    **kwargs
                }
            )

            merged_audio = AudioSegment.silent(duration=0)

            for i, json_parsed in enumerate(response):
                replies = json_parsed.get("replies", [])

                for reply in replies:
                    text = reply.get("text", "")

                encode = json_parsed.get("speech", "")
                if encode:
                    decode = base64.b64decode(encode)
                    audio = AudioSegment.from_file(BytesIO(decode))
                    merged_audio += audio
                else:
                    print(f"Skipping .json #{i}") # Intentionally skips due to how c.ai api works

            # Exporting the merged audio to voice.mp3
            merged_audio.export("voice.mp3", format="mp3")
            voice_path = os.path.abspath('voice.mp3')
            shutil.move(voice_path, os.path.join(voice_pth, os.path.basename(voice_path)))
            
            return text 

        def next_message(
            self, history_id: str, parent_msg_uuid: str,
            tgt: str, *, token: str = None, **kwargs
        ):
            response = PyCAI2.request(
                'chat/streaming/', self.session,
                token=token, method='POST', split=True,
                data={
                    'history_external_id': history_id,
                    'parent_msg_uuid': parent_msg_uuid,
                    'tgt': tgt,
                    **kwargs
                }
            )

        def get_histories(
            self, char: str, *, number: int = 50,
            token: str = None
        ):
            return PyCAI2.request(
                'chat/character/histories_v2/', self.session,
                token=token, method='POST',
                data={'external_id': char, 'number': number},
            )

        def get_history(
            self, history_id: str = None,
            *, token: str = None
        ):
            return PyCAI2.request(
                'chat/history/msgs/user/?'
                f'history_external_id={history_id}',
                self.session, token=token
            )

        def get_chat(
            self, char: str = None, *,
            token: str = None
        ):
            return PyCAI2.request(
                'chat/history/continue/', self.session,
                token=token, method='POST',
                data={
                    'character_external_id': char
                }
            )

        def send_message(
            self, char: str, text: str,
            *, token: str = None, **kwargs
        ):
            
            r = PyCAI2.request('chat/history/continue/', self.session,token=token, method='POST',data={'character_external_id': char})
            external = r['external_id']
            participants = r['participants']
            if not participants[0]['is_human']:
                tgt = participants[0]['user']['username']
            else:
                tgt = participants[1]['user']['username']
            
            r = PyCAI2.request(
                'chat/streaming/', self.session,
                token=token, method='POST', split=True,
                data={
                    'history_external_id': external,
                    'tgt': tgt,
                    'text': text,
                    **kwargs
                }
            )
            response = r['replies'][0]['text']
            return response

        def delete_message(
            self, history_id: str, uuids_to_delete: list,
            *, token: str = None, **kwargs
        ):
            return PyCAI2.request(
                'chat/history/msgs/delete/', self.session,
                token=token, method='POST',
                data={
                    'history_id': history_id,
                    'uuids_to_delete': uuids_to_delete,
                    **kwargs
                }
            )

        def new_chat(
            self, char: str, *, token: str = None
        ):
            return PyCAI2.request(
                'chat/history/create/', self.session,
                token=token, method='POST',
                data={
                    'character_external_id': char
                }
            )

   
