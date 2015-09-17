from rhobot.bot import RhoBot
from rhobot import configuration
import optparse

from journal_bot.components.commands import load_commands

load_commands()

parser = optparse.OptionParser()
parser.add_option('-c', dest="filename", help="Configuration file for the bot", default='journal_bot.rho')
(options, args) = parser.parse_args()

configuration.load_file(options.filename)

bot = RhoBot()
bot.register_plugin('create_event')


# Connect to the XMPP server and start processing XMPP stanzas.
if bot.connect():
    bot.process(block=True)
else:
    print("Unable to connect.")
