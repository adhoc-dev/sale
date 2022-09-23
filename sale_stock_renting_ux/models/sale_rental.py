from odoo import models, fields


class RentalOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def generate_picking_with_move(self, location_id, location_dest_id):
        def create_picking(stock_move):
            """ Create picking for a move given"""
            vals = stock_move._get_new_picking_values()
            vals['picking_type_id'] = picking_type_id.id
            vals['partner_id'] = self.order_id.partner_shipping_id.id
            picking = self.env['stock.picking'].create(vals)
            picking.date_done = fields.Datetime.now(self)
            picking.origin = self.order_id.name
            group = self.env['procurement.group'].create(self._prepare_procurement_group_vals())
            stock_move.write({
                'picking_id': picking.id,
                'group_id': group.id,
            })
            picking.move_lines._assign_picking_post_process(new=picking)
            return picking, group
        if self.env['ir.config_parameter'].sudo().get_param('sale_stock_renting_ux.rental_create_picking'):
            picking = self.env['stock.picking']
            picking_type_id = self.company_id.rental_picking_type_id
            rental_stock_move_by_location = self.move_ids.filtered(lambda s: s.location_id == location_id and s.location_dest_id == location_dest_id and not s.picking_id)
            pickings = self.order_id.order_line.mapped('move_ids').filtered(lambda s: s.location_id == location_id and s.location_dest_id == location_dest_id).mapped('picking_id')
            if pickings:
                # for the same product in other picking we consider that is partial of a new transfer and create new picking
                if len(pickings) == 1 and (pickings.mapped('move_lines.product_id') & self.product_id):
                    picking, group = create_picking(rental_stock_move_by_location)
                else:
                    # we need the last picking crated to assign
                    picking = pickings.filtered(lambda x: x.location_id == location_id and x.location_dest_id == location_dest_id)[-1]
                    group = picking.group_id
                    rental_stock_move_by_location.write({
                        'picking_id': picking.id,
                        'group_id': group.id,
                    })
            else:
                picking, group = create_picking(rental_stock_move_by_location)
            self.order_id.procurement_group_id = group
            for move_line in rental_stock_move_by_location.mapped('move_line_ids'):
                move_line.picking_id = move_line.move_id.picking_id


    def _move_qty(self, qty, location_id, location_dest_id):
        super()._move_qty(qty, location_id, location_dest_id)
        self.generate_picking_with_move(location_id, location_dest_id)

    def _move_serials(self, lot_ids, location_id, location_dest_id):
        super()._move_serials(lot_ids, location_id, location_dest_id)
        self.generate_picking_with_move(location_id, location_dest_id)
