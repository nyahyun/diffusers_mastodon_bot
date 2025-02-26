import typing
from mastodon import Mastodon

from diffusers_mastodon_bot.bot_context import BotContext
from typing import *


class BotRequestContext:
    def __init__(self,
                 status: Dict[str, Any],
                 mastodon: Mastodon,
                 bot_ctx: BotContext
                 ):
        self.status = status
        self.mastodon: Mastodon = mastodon
        self.bot_ctx = bot_ctx

        self.reply_visibility = status['visibility']
        if self.reply_visibility == 'public' or self.reply_visibility == 'direct':
            self.reply_visibility = 'unlisted'
        self.reply_visibility = 'unlisted'

        # [{'name': 'testasdf', 'url': 'https://don.naru.cafe/tags/testasdf'}]
        self.tag_name_list = set(map(lambda tag: tag['name'], status['tags']))

        self.payload: Dict[typing.Type, Dict[str, Any]] = {}

    def contains_tag_name(self, tag_name):
        return tag_name in self.tag_name_list

    def mentions_bot(self):
        # mention dicts
        mentions = self.status['mentions']
        return self.bot_ctx.bot_acct_url in map(lambda x: x['url'], mentions)

    def not_from_self(self):
        account = self.status['account']
        return account['url'] != self.bot_ctx.bot_acct_url

    def reply_to(self, status: Dict[str, Any], body: str, **kwargs):
        if 'visibility' not in kwargs.keys():
            kwargs['visibility'] = self.reply_visibility

        return self.mastodon.status_reply(status, body, **kwargs)

    def set_payload(self, klass: typing.Type, key: str, value: Any):
        if klass not in self.payload.keys():
            self.payload[klass] = {}

        self.payload[klass][key] = value

    def get_payload(self, klass: typing.Type, key: str) -> Optional[Any]:
        if klass not in self.payload.keys():
            return None

        if key not in self.payload[klass]:
            return None

        return self.payload[klass][key]
