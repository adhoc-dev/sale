.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================
Accounting Reports UX
=====================

Este modulo agrega un boton en la vista form de los reportes financieros para generar el menu de acceso al reporte si no lo tiene establecido.

Es importante que antes de que se creen la conciliaciones ya esté bien definida la cotización para los días involucrados salvo que los pagos sean a futuro porque en tal caso se marca que van a requerir ajuste para revisar llegada la fecha.

Una posible mejora sería agregar un cron que se encargue de recalcular todos los días al ir teniendo nuevas cotizaciones.

Por ultimo, actualmente no estaría sugiriendo cuando se requiera hacer las NC y esto es una limitación conocida por como se debe hacer el calculo.

Installation
============

To install this module, you need to:

#. Only need to install the module

Configuration
=============

To configure this module, you need to:

#. Nothing to configure

Usage
=====

To use this module, you need to:

#. Go to ...

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
