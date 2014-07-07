rapidsms-multitenancy
=====================

rapidsms-multitenancy allows you to host multiple RapidSMS instances in one cohesive project.


Description
-----------

Why would you want to use rapidsms-multitenancy? It was built for a situation where a large
organization has operations in multiple countries. It's desirable for each country to have its own
RapidSMS instance so that users can easily communicate with that local backend. On the other hand,
it's a pain to install RapidSMS in each location as you'd have to do each installation separately,
keep each installation updated, and have user accounts duplicated over installations.

rapidsms-multitenancy allows you to have one central RapidSMS installation with multiple tenants.
Each tenant is associated with one or more RapidSMS backends with the aim of keeping each tenant
separate. Superusers of the system can view multiple tenants.


Running the Tests
------------------------------------

You can run the tests with via::

    python runtests.py



License
-------

rapidsms-multitenancy is released under the BSD License. See the `LICENSE
<https://github.com/theirc/rapidsms-multitenancy/blob/master/LICENSE>`_ file for
more details.


Contributing
------------

If you think you've found a bug or are interested in contributing to this
project check out `rapidsms-multitenancy on Github
<https://github.com/theirc/rapidsms-multitenancy>`_.

Development sponsored by `The International Rescue Committee
<http://www.rescue.org>`_.