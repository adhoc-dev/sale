# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'
#Start change: Esta nueva función se encarga de retornar al front-end el valor del block additional quantities. #End
    def getPickingTypeOperation(self):
        self.ensure_one()
        return self.picking_type_id.block_additional_quantity

