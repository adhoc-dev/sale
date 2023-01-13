.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===========================
Direct Debits for Argentina
===========================

1. Generación de TXT para cobranza de débito directo del BANCO GALICIA; MACRO ; MASTER CRÉDITO ; VISA DÉBITO Y CRÉDITO

2. Generación de contratos de débito directo "Direct Debit Mandates"  

3.  Campo "Direct Debit" en Journal para configurar banco y Campo "Merchant Number" en Journal para configurar  número de comercio


Installation
============

To install this module, you need to:

1. Instalar l10n_ar_account_direct_debit

Configuration
=============

To configure this module, you need to:

1. Configurar Diario de Débito Directo Galicia con método de pago "Direct Debit" eligiendo BANCO GALICIA y "Merchant Number" según Nro de Comercio

Usage
=====

To use this module, you need to:

1. Configurar CBU en contacto

2. Crear contrato de débito directo

3. Generar factura y pago con direct debit mandate

4. Generar Pago por Lote

5. Exportar TXT

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
