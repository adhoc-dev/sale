.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=============================
Account Online Sync Argentina
=============================


Installation
============

To install this module, you need to:

#. Only install the module

Configuration
=============

To configure this module, you need to:

#. Nothing todo

Usage
=====

To use this module, you need to:

#. Configure from your bank journal form view to use automatic syncronization for the bank statements.
#. From the Accouting dashboard serach the journal and click on the button Syncronization Online
#. Log in to your bank adding the credentials you use for login in the bank

After all this if found multiple account banks Odoo will ask you to define which bank account want to sync and to which journal and from which date you want to import the bank statements.

After that an automatic action will be run daily to update you Odoo bank statements, you can force it by clicking the Sync Now button in bank card on the Accouting Dashboard.

For development purpose, you can change this line in order to make it easier the test::

   -            <form action="/account_online_sync_ar/paybook_success" id="paybook_success" method="post" class="invisible">
   +            <form action="/account_online_sync_ar/paybook_success" id="paybook_success" method="post" t-att-class="'invisible' if not request.env.user.has_group('saas_client.group_saas_support') else ''">

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: http://runbot.adhoc.com.ar/

Credits
=======

Images
------

* |company| |icon|

Contributors
------------

Maintainer
----------

|company_logo|

This module is maintained by the |company|.

To contribute to this module, please visit https://www.adhoc.com.ar.
