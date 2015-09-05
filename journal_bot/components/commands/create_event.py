"""
Command that will allow for the creation of arbitrary events in the database.
"""
from rhobot.components.rdf_publish import RDFSourceStanza
from rhobot.components.commands.base_command import BaseCommand
from rhobot.components.storage import StoragePayload
import logging
from rdflib.namespace import Namespace

SCHEMA = Namespace('http://schema.org/')
WGS_84 = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')

logger = logging.getLogger(__name__)

class CreateEventCommand(BaseCommand):

    def initialize_command(self):
        super(CreateEventCommand, self).initialize_command()

        logger.info('Initialize Command')
        self._initialize_command(identifier='create_event', name='Create Event',
                                 additional_dependencies={'rho_bot_rdf_publish', 'rho_bot_storage_client', })

    def command_start(self, request, initial_session):
        """
        Provide the configuration details back to the requester and end the command.
        :param request:
        :param initial_session:
        :return:
        """
        form = self.xmpp['xep_0004'].make_form()

        form.add_field(var='title', label='Title', ftype='text-single')
        form.add_field(var='description', label='Description', ftype='text-multi')
        form.add_field(var='event_start', label='Start Time', ftype='text-single')
        form.add_field(var='event_stop', label='Stop Time', ftype='text-single')

        initial_session['payload'] = form
        initial_session['next'] = self.store_results
        initial_session['has_next'] = False

        def handle_results_from_search(results):
            options = []

            results.results.sort(cmp=lambda x, y: cmp(x.get_column('http://degree')[0],
                                                      y.get_column('http://degree')[0]),
                                 reverse=True)

            for result in results.results:
                options.append({'value': result.about, 'label': result.get_column(str(SCHEMA.name))[0]})

            options = options[:10]

            location_field = form.add_field(var='locations', label='Location', ftype='list-single', options=options)

            if hasattr(results, 'sources'):
                for source in results.sources:
                    source_stanza = RDFSourceStanza()
                    source_stanza['name'] = source[0]
                    source_stanza['command'] = source[1]

                    location_field.append(source_stanza)

            return initial_session

        payload = StoragePayload()
        payload.add_type(WGS_84.SpatialThing)

        return self.xmpp['rho_bot_rdf_publish'].send_out_search(payload, timeout=2.0).then(handle_results_from_search)

    def store_results(self, payload, session):

        logger.info('Payload: %s' % payload)
        logger.info('Session: %s' % session)

        return session


create_event = CreateEventCommand
