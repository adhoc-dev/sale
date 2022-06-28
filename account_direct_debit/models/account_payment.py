from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.payment'

    direct_debit_mandate_id = fields.Many2one(
        'account.direct_debit.mandate', compute='_compute_direct_debit_mandate', store=True, readonly=False,
        states={'draft': [('readonly', False)]}, ondelete='restrict')
    commercial_partner_id = fields.Many2one(related='partner_id.commercial_partner_id')
    direct_debit_format = fields.Selection(related='journal_id.direct_debit_format')

    @api.depends('partner_id', 'journal_id', 'payment_method_id')
    def _compute_direct_debit_mandate(self):
        """ Remove selected mandate if not usable for current journal, payment mode and partner """
        self.filtered(
            lambda x: x.direct_debit_mandate_id and (
                x.payment_method_id.code != 'dd' or
                x.direct_debit_mandate_id.direct_debit_format != x.direct_debit_format or
                x.direct_debit_mandate_id.journal_id != x.journal_id)).direct_debit_mandate_id = False

    def cancel_and_remove_from_batch(self):
        """ Metodo para ser utilizado en los batches para los pagos que son rechazados.
        Pasa el pago a borrador y lo cancela (que es lo que se haría por interfaz) además desvincula el payment del
        batch y postea un mensaje en el payment indicando esto. Lo desvinculamos porque si no el batch queda con:
        * amount: sumando este payment
        * si por alguna razón se quiere re-generar el archivo entonces hay que cambiar muchos lugares donde odoo
        usa self.payment_ids sin filtrar por el estado de los payments
        De alguna manera, la logica es que si un payment esta en el batch, no importa si lo cancelas desde otro lad,
        se va a usar en ese batch. Salvo que uses este botón para cancelarlo y desvincular del batch."""
        payment_group = self._fields.get('payment_group_id')
        for rec in self:
            if payment_group and rec.payment_group_id:
                rec.payment_group_id.action_draft()
                rec.payment_group_id.cancel()
                rec.payment_group_id.message_post(body=_('Payment cancelled from batch %s') % (rec.batch_payment_id.display_name))
            else:
                rec.action_draft()
                rec.cancel()
                rec.message_post(body=_('Payment cancelled from batch %s') % (rec.batch_payment_id.display_name))
        self.write({'batch_payment_id': False})
