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

#. This module add a boolean field to the Subscription template that let us copy or not its desctiprion in the recurring invoice notes.
#. We add constraint so that subscription End date must be equal or greater than Start date.
#. Add Dates required boolean field on Subscription Template model, if setted, then the Start date and End date will be required
#. Improove prepare invoice to use _set_additional_fields method
#. Add Period field on Subscription Template model that let us know how many times will be repeated the subscription taking into account the recurrence, if setted, compute automatically the End date of the subscription everytime the start date or the subscription tempalte is change.
#. If you have a sale order that have both, subscription products and products
   that generate projects or tasks, then the created subscriptions will re use
   the analytic account that was created for the project/tasks.
#. Add sequence on sale subscriptions lines that let us to order the
   subscription lines.
#. Update prices in subscriptions: update price in subscription lines from the
   values in the related products.

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
