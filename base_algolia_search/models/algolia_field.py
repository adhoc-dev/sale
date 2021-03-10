from odoo import api, models, fields


class AlgoliaField(models.Model):
    _name = 'algolia.field'
    _description = 'Algolia Attribute'
    _order = 'priority asc'

    priority = fields.Integer(
        help='Priority used for search relevance (lower priority is higher relevance.\n'
        'Only relevant if attribute is set as searchable')
    field_id = fields.Many2one('ir.model.fields', required=True, ondelete='cascade')
    relation_model = fields.Char(related='field_id.relation', readonly=True)
    sub_field_id = fields.Many2one('ir.model.fields', string='Sub Campo')
    searchable = fields.Boolean(default=True)
    model_id = fields.Many2one('ir.model', required=True, ondelte='cascade')
    unordered = fields.Boolean(
        help="By default, all searchable attributes are ordered. This means that matches at the beginning of an "
        "attribute are considered more important than in the middle or the end. If you specifically set them as "
        "unordered, the position of the match within the attribute doesn’t count.")

    def _get_algolia_field_name(self):
        self.ensure_one()
        if self.field_id.ttype in ['many2one', 'many2many', 'one2many']:
            field_name = '%s/%s' % (
                self.field_id.name, (self.sub_field_id.name == 'id' and '.id' or self.sub_field_id.name))
        else:
            field_name = self.field_id.name
        return field_name

    @api.onchange('sub_field_id')
    def onchange_sub_field_id(self):
        if self.sub_field_id.name == 'id':
            self.searchable = False

    @api.onchange('searchable', 'field_id')
    def onchange_searchable(self):
        self.priority = self.searchable and 10 or False
        self.unordered = (self.searchable and self.field_id.name == 'name') and True or False

    @api.onchange('field_id')
    def onchange_relational_field_id(self):
        if self.field_id.relation:
            self.sub_field_id = self.sub_field_id.search(
                [('model_id.model', '=', self.field_id.relation), ('name', '=', 'display_name')], limit=1)
        else:
            self.sub_field_id = False

    _sql_constraints = [
        ('algolia_field_uniqe', 'unique(field_id, model_id)', 'Algolia field must be unique per model!'),
    ]
