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

#. check company consistency between subscription and partner
#. This module add a boolean field to the Subscription template that let us copy or not its desctiprion in the recurring invoice notes.
#. Add Dates required boolean field on Subscription Template model, if setted, then the Start date and End date will be required
#. Add funcionality to use "without discount" in subscription lines.
#. If you have a sale order that have both, subscription products and products
   that generate projects or tasks, then the created subscriptions will re use
   the analytic account that was created for the project/tasks.
#. Add sequence on sale subscriptions lines that let us to order the
   subscription lines.
#. Update prices in subscriptions: update price in subscription lines from the
   values in the related products.
#. Add option for 'Not update prices' when update quantity in sale subscription line.
#. Add Invoice Address field to the subscription, similar to the one in the sale.order in order to be used when creating recurring invoicees (optional by subscription template)
#. Fixes the default behavior that brings payment term to generated invoices from SO even if it's empty, so if SO hasn't got any payment term value, it's brought from the partner's payment term.
#. Add menu item for subscription lines

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
