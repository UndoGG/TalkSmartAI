import os
import uuid
import zipfile

import yaml

from database.users import UserManagement
import enums
from database.conversations import ConversationManagement
from pydantic_models.users import User


class Dumper:
    def __init__(self):
        pass

    async def dump_user(self, user: User):
        dump = {}
        conversations = await ConversationManagement.get(id=user.id, by=enums.GetByEnum.USER_ID,
                                                         include_closed=True)
        for conv in conversations:
            if dump.get(f'{conv.created_at:%Y-%m-%d}') is None:
                dump[f'{conv.created_at:%Y-%m-%d}'] = []

            dump[f'{conv.created_at:%Y-%m-%d}'].append({'author': conv.role.value,
                                                        'text': conv.text,
                                                        'time': f"{conv.created_at:%H:%M:%S}",
                                                        'closed': 'Yes' if conv.closed else 'No'})

        return dump

    async def dump_all(self) -> tuple:
        """
        returns path to zip dump-file and dump-folder path tuple
        """
        dumps = {}

        for user in await UserManagement.get_all():
            dump = await self.dump_user(user)
            if len(dump) > 0:
                dumps[f'{user.telegram_name} ({user.telegram_id})'] = dump

        dump_id = str(uuid.uuid1())
        dump_folder_path = os.path.join('temp', f'dump-{dump_id}')
        zip_path = os.path.join('temp', dump_id + '.zip')

        for tg_id, dump in dumps.items():
            for date in dump:
                dump = dumps[tg_id][date]
                path = os.path.join(dump_folder_path, str(tg_id))
                try:
                    os.makedirs(path)
                except Exception:
                    pass
                path = os.path.join(path, date  + '.yml')
                with open(path, mode='w+') as yaml_file:
                    yaml.dump(dump, yaml_file, encoding='utf-8', sort_keys=False)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dump_folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dump_folder_path)
                    zipf.write(file_path, arcname=arcname)

        return zip_path, dump_folder_path
