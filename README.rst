django-snow
=================

.. image:: https://img.shields.io/pypi/v/django-snow.svg
   :target: https://pypi.python.org/pypi/django-snow
   :alt: Latest Version

.. image:: https://travis-ci.org/godaddy/django-snow.svg?branch=master
   :target: https://travis-ci.org/godaddy/django-snow
   :alt: Test/build status

.. image:: https://codecov.io/gh/godaddy/django-snow/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/godaddy/django-snow
   :alt: Code coverage

**django-snow** is a django app to manage ServiceNow tickets from within a django project.

Installation
============

::

    pip install django-snow

Configuration
=============
**django-snow** requires the following settings to be set in your Django settings:

* ``SNOW_INSTANCE`` - The ServiceNow instance where the tickets should be created
* ``SNOW_API_USER`` - The ServiceNow API User
* ``SNOW_API_PASS`` - The ServiceNow API User's Password
* ``SNOW_ASSIGNMENT_GROUP`` (Optional) - The group to which the tickets should be assigned.
  If this is not provided, each call to create the tickets should be provided with an `assignment_group` argument.
  See the API documentation for more details
* ``SNOW_DEFAULT_CHANGE_TYPE`` (Optional) - Default Change Order Type. If not provided,
  `standard` will considered as the default type.

Usage
=====

Creation
--------
``ChangeOrderHandler.create_change_order`` has the following parameters and return value:

**Parameters**

* ``title`` - The title of the change order
* ``description`` - The description of the change order
* ``assignment_group`` - The group to which the change order is to be assigned.
  This is **optional** if ``SNOW_ASSIGNMENT_GROUP`` django settings is available, else, it is **mandatory**
* ``payload`` (Optional) - The payload for creating the Change Order.

**Returns**

``ChangeOrder`` model - The model created from the created Change Order.

**Example**

.. code-block:: python

    from django_snow.helpers import ChangeOrderHandler

    def change_data(self):
        co_handler = ChangeOrderHandler()
        change_order = co_handler.create_change_order('Title', 'Description', 'assignment_group')


Updating
--------
``ChangeOrderHandler.update_change_order`` method signature:

**Parameters**

* ``change_order`` - The ``ChangeOrder`` Model
* ``payload`` - The payload to pass to the ServiceNow REST API.

**Example**

.. code-block:: python

    from django_snow.models import ChangeOrder
    from django_snow.helpers import ChangeOrderHandler

    def change_data(self):
        change_order = ChangeOrder.objects.filter(...)
        co_handler = ChangeOrderHandler()

        payload = {
                    'description': 'updated description',
                    'state': ChangeOrder.TICKET_STATE_IN_PROGRESS
                  }

        co_handler.update_change_order(change_order, payload)


Closing
-------
``ChangeOrderHandler.close_change_order`` has the following signature:

**Parameters**

* ``change_order`` - The ``ChangeOrder`` Model representing the Change Order to be closed.

**Example**

.. code-block:: python

    from django_snow.models import ChangeOrder
    from django_snow.helpers import ChangeOrderHandler

    def change_data(self):
        change_order = ChangeOrder.objects.filter(...)
        co_handler = ChangeOrderHandler()

        co_handler.close_change_order(change_order)

Closing with error
------------------
``ChangeOrderHandler.close_change_order_with_error`` method signature:

**Parameters**

* ``change_order`` - The ``ChangeOrder`` Model representing the Change Order to be closed with error
* ``payload`` - The payload to pass to the ServiceNow REST API.

**Example**

.. code-block:: python

    from django_snow.models import ChangeOrder
    from django_snow.helpers import ChangeOrderHandler

    def change_data(self):
        change_order = ChangeOrder.objects.filter(...)
        co_handler = ChangeOrderHandler()

        payload = {
                    'description': 'updated description',
                    'title': 'foo'
                  }

        co_handler.close_change_order_with_error(change_order, payload)

Models
======

ChangeOrder
-------------
The ``ChangeOrder`` model has the following attributes:

* ``sys_id`` - The sys_id of the Change Order.
* ``number`` - Change Order Number.
* ``title`` - The title of the Change Order a.k.a short_description.
* ``description`` - Description for the change order
* ``assignment_group_guid`` - The GUID of the group to which the Change Order is assigned to
* ``state`` - The State of the Change Order. Can be any one of the following ``ChangeOrder``'s constants:

  * ``TICKET_STATE_OPEN`` - '1'
  * ``TICKET_STATE_IN_PROGRESS`` - '2'
  * ``TICKET_STATE_COMPLETE`` - '3'
  * ``TICKET_STATE_COMPLETE_WITH_ERRORS`` - '4'


Supported Ticket Types
======================
* Change Orders
