from odoo import api, models, fields


class AlgoliaField(models.Model):
    _name = 'algolia.field'
    _description = 'Algolia Attribute'
    _order = 'priority asc'

    priority = fields.Integer(
        help='Priority used for search relevance (lower priority is higher relevance.\n'
        'Only relevant if attribute is set as searchable')
    field_id = fields.Many2one('ir.model.fields', required=True)
    searchable = fields.Boolean(default=True)
    model_id = fields.Many2one('ir.model', required=True, ondelte='cascade')
    unordered = fields.Boolean(
        help="By default, all searchable attributes are ordered. This means that matches at the beginning of an "
        "attribute are considered more important than in the middle or the end. If you specifically set them as "
        "unordered, the position of the match within the attribute doesn’t count.")

    @api.onchange('searchable', 'field_id')
    def onchange_searchable(self):
        self.priority = self.searchable and 10 or False
        self.unordered = (self.searchable and self.field_id.name == 'name') and True or False
