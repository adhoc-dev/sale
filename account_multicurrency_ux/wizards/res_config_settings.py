from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    exchange_diff_adjustment_tolerance = fields.Float(
        related='company_id.exchange_diff_adjustment_tolerance',
        readonly=False,
    )
    exchange_rate_tolerance = fields.Float(
        related='company_id.exchange_rate_tolerance',
        readonly=False,
    )
