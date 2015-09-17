from journal_bot.components.commands.create_event import create_event

from sleekxmpp.plugins.base import register_plugin


def load_commands():
    register_plugin(create_event)
