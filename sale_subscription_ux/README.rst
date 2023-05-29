.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

====================
Sale Subscription UX
====================

#. Adds a boolean option to quit period description on invoice narration. By default the value is true and Odoo will show the period in the invoice.
#. Adds Dates required boolean field on Subscription Template model, if setted, then the Start date and End date will be required
#. Updates line data: update price in subscription lines from the values in the related products
#. Adds menu item for Subscription Lines in the Suscription main menu.
#. Adds in the list view in the Sales Order model,  a column with the MRR. If it's a subscription, it will show a positive number, if not, the amount shown will be 0.
#. Allows to hide the column that cointains the client_order_ref field in the Subscriptions list view.
#. Adds option 'Invoice Method' in subscription templates allowing invoices to be created and stay in draft.
#. Keeps field 'Subscription Plan/Quotation Plan' visible while a subscriptions is confirmed.

Installation
============

To install this module, you need to:

#. Just Install this module

Configuration
=============

To configure this module, you need to:

#. No configuration needed

Usage
=====

#. Update prices from subscription form with button "Update Lines Prices"
#. Update prices from subscription list selecting the ones you want to update and then going in to "Action / Update Lines Prices"
#. Within subscription template has option 'Do not update prices', tick to no update price.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: http://runbot.adhoc.com.ar/

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ingadhoc/enterprise-extensions/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

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
