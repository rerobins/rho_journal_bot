"""
Set up the bot for execution.
"""
from rhobot.application import Application
from journal_bot.components.commands import load_commands


application = Application()

# Register all of the components that are defined in this application.
application.pre_init(load_commands)

@application.post_init
def register_plugins(bot):
    bot.register_plugin('create_event')
