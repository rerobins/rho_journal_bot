from rhobot.bot import RhoBot
from rhobot import configuration
import optparse

parser = optparse.OptionParser()
parser.add_option('-c', dest="filename", help="Configuration file for the bot", default='journal_bot.rho')
(options, args) = parser.parse_args()

configuration.load_file(options.filename)

bot = RhoBot()
bot.register_plugin('rho_bot_storage_client', module='rhobot.components')
bot.register_plugin('rho_bot_rdf_publish', module='rhobot.components')
bot.register_plugin('create_event', module='journal_bot.components.commands')


# Connect to the XMPP server and start processing XMPP stanzas.
if bot.connect():
    bot.process(block=True)
else:
    print("Unable to connect.")
