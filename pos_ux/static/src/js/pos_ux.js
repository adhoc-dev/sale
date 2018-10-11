odoo.define('pos_ux.PosScreens', function (require) {
"use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    console.log("1111 !!!!!!");

    screens.PaymentScreenWidget.include({
        order_is_valid: function (force_validation) {
            console.log("222 !!!!!");
            var self = this;
            var order = this.pos.get_order();

            console.log(order.journal_id.name);
            console.log(order.partner_id.name);

            if (order.journal_id.pos_outstanding_payment){
                // and not order.partner_id
                this.gui.show_popup('error', {
                    'title': _t('Missing Customer for Current Account'),
                    'body': _t('You need to select the customer before you can invoice this order if you use Current Account payment.'),
                });
                return false;
            }
            this._super.apply(this, arguments);
        },
    });
});
