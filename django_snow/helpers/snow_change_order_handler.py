import logging

import pysnow
from django.conf import settings
from django.utils import timezone
from requests.exceptions import HTTPError

from django_snow.helpers.exceptions import ChangeOrderException
from django_snow.models import ChangeOrder


logger = logging.getLogger('django_snow')


class ChangeOrderHandler:
    """
    SNow Change Order Handler.
    """

    group_guid_dict = {}

    # Service Now table REST endpoints
    CHANGE_ORDER_TABLE_PATH = '/table/change_request'
    USER_GROUP_TABLE_PATH = '/table/sys_user_group'

    def __init__(self):
        self._client = None
        self.snow_instance = settings.SNOW_INSTANCE
        self.snow_api_user = settings.SNOW_API_USER
        self.snow_api_pass = settings.SNOW_API_PASS
        self.snow_assignment_group = getattr(settings, 'SNOW_ASSIGNMENT_GROUP', None)
        self.snow_default_cr_type = getattr(settings, 'SNOW_DEFAULT_CHANGE_TYPE', 'standard')

    def create_change_order(self, title, description, assignment_group=None, payload=None):
        """
        Create a change order with the given payload.
        """
        client = self._get_client()
        change_orders = client.resource(api_path=self.CHANGE_ORDER_TABLE_PATH)
        payload = payload or {}
        payload['short_description'] = title
        payload['description'] = description

        if 'type' not in payload:
            payload['type'] = self.snow_default_cr_type
        if 'assignment_group' not in payload:
            payload['assignment_group'] = self.get_snow_group_guid(assignment_group or self.snow_assignment_group)

        try:
            result = change_orders.create(payload=payload)
        except HTTPError as e:
            logger.error('Could not create change order due to %s', e.response.text)
            raise ChangeOrderException('Could not create change order due to %s.' % e.response.text)

        # This piece of code is for legacy SNow instances. (probably Geneva and before it)
        if 'error' in result:
            logger.error('Could not create change order due to %s', result['error'])
            raise ChangeOrderException('Could not create change order due to %s' % result['error'])

        change_order = ChangeOrder.objects.create(
            sys_id=result['sys_id'],
            number=result['number'],
            title=result['short_description'],
            description=result['description'],
            assignment_group_guid=result['assignment_group']['value'],
            state=result['state']
        )

        return change_order

    def close_change_order(self, change_order):
        """Mark the change order as completed."""

        payload = {'state': ChangeOrder.TICKET_STATE_COMPLETE}
        change_order.closed_time = timezone.now()
        self.update_change_order(change_order, payload)

    def close_change_order_with_error(self, change_order, payload):
        """Mark the change order as completed with error.

        The possible keys for the payload are:
            * `title`
            * `description`

        :param change_order: The change order to be closed
        :type change_order: :class:`django_snow.models.ChangeOrder`
        :param payload: A dict of data to be updated while closing change order
        :type payload: dict
        """
        payload['state'] = ChangeOrder.TICKET_STATE_COMPLETE_WITH_ERRORS
        change_order.closed_time = timezone.now()
        self.update_change_order(change_order, payload)

    def update_change_order(self, change_order, payload):
        """Update the change order with the data from the kwargs.

        The possible keys for the payload are:
            * `title`
            * `description`
            * `state`

        :param change_order: The change order to be updated
        :type change_order: :class:`django_snow.models.ChangeOrder`
        :param payload: A dict of data to be updated while updating the change order
        :type payload: dict
        """
        client = self._get_client()

        # Get the record and update it
        change_orders = client.resource(api_path=self.CHANGE_ORDER_TABLE_PATH)

        try:
            result = change_orders.update(query={'sys_id': change_order.sys_id.hex}, payload=payload)
        except HTTPError as e:
            logger.error('Could not update change order due to %s', e.response.text)
            raise ChangeOrderException('Could not update change order due to %s' % e.response.text)

        # This piece of code is for legacy SNow instances. (probably Geneva and before it)
        if 'error' in result:
            logger.error('Could not update change order due to %s', result['error'])
            raise ChangeOrderException('Could not update change order due to %s' % result['error'])

        change_order.state = result['state']
        change_order.title = result['short_description']
        change_order.description = result['description']
        change_order.assignment_group_guid = result['assignment_group']['value']
        change_order.save()

        return result

    def _get_client(self):
        if self._client is None:
            self._client = pysnow.Client(
                instance=self.snow_instance, user=self.snow_api_user, password=self.snow_api_pass
            )
        return self._client

    def get_snow_group_guid(self, group_name):
        """
        Get the SNow Group's GUID from the Group Name
        """

        if group_name not in self.group_guid_dict:
            client = self._get_client()
            user_groups = client.resource(api_path=self.USER_GROUP_TABLE_PATH)
            response = user_groups.get(query={'name': group_name})
            result = response.one()
            self.group_guid_dict[group_name] = result['sys_id']

        return self.group_guid_dict[group_name]

    def clear_group_guid_cache(self):
        """
        Clear the SNow Group Name - GUID cache.
        """
        self.group_guid_dict.clear()
