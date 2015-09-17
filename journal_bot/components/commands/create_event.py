"""
Command that will allow for the creation of arbitrary events in the database.
"""
from rhobot.components.rdf_publish import RDFSourceStanza
from rhobot.components.commands.base_command import BaseCommand
from rhobot.components.storage import StoragePayload
from rhobot.namespace import GRAPH, WGS_84, SCHEMA, EVENT, TIMELINE, RHO
from rdflib.namespace import DCTERMS, DC, FOAF
import logging

logger = logging.getLogger(__name__)

class CreateEventCommand(BaseCommand):

    name = 'create_event'
    description = 'Create Event'
    dependencies = BaseCommand.default_dependencies.union({'rho_bot_rdf_publish', 'rho_bot_storage_client',
                                                           'rho_bot_get_or_lookup', 'rho_bot_scheduler',
                                                           'rho_bot_representation_manager', })

    def post_init(self):
        super(CreateEventCommand, self).post_init()

        self._scheduler = self.xmpp['rho_bot_scheduler']
        self._rdf_publish = self.xmpp['rho_bot_rdf_publish']
        self._storage_client = self.xmpp['rho_bot_storage_client']
        self._get_or_lookup = self.xmpp['rho_bot_get_or_lookup']
        self._representation_manager = self.xmpp['rho_bot_representation_manager']

    def command_start(self, request, initial_session):
        """
        Provide the configuration details back to the requester and end the command.
        :param request:
        :param initial_session:
        :return:
        """
        form = self._forms.make_form()

        form.add_field(var='title', label='Title', ftype='text-single')
        form.add_field(var='description', label='Description', ftype='text-multi')
        form.add_field(var='event_start', label='Start Time', ftype='text-single')
        form.add_field(var='event_stop', label='Stop Time', ftype='text-single')

        initial_session['payload'] = form
        initial_session['next'] = self.store_results
        initial_session['has_next'] = False

        def handle_results_from_search(results):
            options = []

            results.results.sort(cmp=lambda x, y: cmp(x.get_column(str(GRAPH.degree))[0],
                                                      y.get_column(str(GRAPH.degree))[0]),
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

        return self._rdf_publish.send_out_search(payload, timeout=2.0).then(handle_results_from_search)

    def store_results(self, payload, session):
        """
        Store the results into the database.
        :param payload:
        :param session:
        :return:
        """

        logger.info('Payload: %s' % payload)
        logger.info('Session: %s' % session)

        storage_session = dict()

        if 'locations' in payload.get_values():
            storage_payload = StoragePayload()
            storage_payload.about = payload.get_values()['locations']
            storage_payload.add_type(WGS_84.SpatialThing)

            promise = self._get_or_lookup(storage_payload).then(
                self._scheduler.generate_promise_handler(self._update_session, storage_session, 'location'))
        else:
            promise = self._scheduler.defer(lambda: storage_session)

        promise = promise.then(self._get_owner)
        promise = promise.then(self._scheduler.generate_promise_handler(self._create_interval, payload))
        promise = promise.then(self._scheduler.generate_promise_handler(self._create_event, payload))

        promise = promise.then(lambda s: session)

        session['payload'] = None
        session['next'] = None
        session['has_next'] = False

        return promise

    def _update_session(self, result, session, key):
        """
        Update the storage session with the key and value.
        :param result: value to store.
        :param session: session to store values in.
        :param key: key to store value under.
        :return: session.
        """
        session[key] = result

        return session

    def _get_owner(self, session):
        """
        Fetch the owner of the system from the framework.
        :param session:
        :return:
        """
        def _translate_search_to_about(result):
            if result.results:
                return result.results[0].about

            raise RuntimeError('Owner could not be found')

        search_payload = StoragePayload()
        search_payload.add_type(RHO.Owner, FOAF.Person)

        promise = self._rdf_publish.send_out_request(search_payload)
        promise = promise.then(_translate_search_to_about)
        promise = promise.then(self._scheduler.generate_promise_handler(self._update_session, session, 'owner'))

        return promise

    def _create_interval(self, session, form_payload):
        """
        Convert the form payload into a storage payload for creating a new interval.
        :param session:
        :param form_payload:
        :return:
        """
        def _translate_search_to_about(result):
            if result.results:
                return result.results[0].about

            raise RuntimeError('Interval was not created.')

        # Handle the creation of the interval.
        create_interval_payload = StoragePayload()
        create_interval_payload.add_type(TIMELINE.Interval)

        if 'event_start' in form_payload.get_values():
            create_interval_payload.add_property(TIMELINE.start, form_payload.get_values()['event_start'])

        if 'event_stop' in form_payload.get_values():
            create_interval_payload.add_property(TIMELINE.end, form_payload.get_values()['event_stop'])

        creator = self._representation_manager.representation_uri
        if creator:
            create_interval_payload.add_property(DCTERMS.creator, creator)

        promise = self._storage_client.create_node(create_interval_payload)
        promise = promise.then(_translate_search_to_about)
        promise = promise.then(self._scheduler.generate_promise_handler(self._update_session, session, 'interval'))

        return promise

    def _create_event(self, session, form_payload):
        """
        Conver the form payload into a storage payload for creating a new event.
        :param session:
        :param form_payload:
        :return:
        """
        create_event_payload = StoragePayload()
        create_event_payload.add_type(EVENT.Event)

        create_event_payload.add_reference(key=EVENT.agent, value=session['owner'])
        create_event_payload.add_reference(key=DCTERMS.creator, value=self._representation_manager.representation_uri)

        if 'title' in form_payload.get_values():
            create_event_payload.add_property(key=DC.title, value=form_payload.get_values()['title'])

        if 'description' in form_payload.get_values():
            create_event_payload.add_property(key=DC.description, value=form_payload.get_values()['description'])

        if session['location']:
            create_event_payload.add_reference(key=EVENT.place, value=session['location'])

        if session['interval']:
            create_event_payload.add_reference(key=EVENT.time, value=session['interval'])

        promise = self._storage_client.create_node(create_event_payload)

        return promise


create_event = CreateEventCommand
