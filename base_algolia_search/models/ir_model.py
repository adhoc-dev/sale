# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from lxml import etree
from algoliasearch.search_client import SearchClient
from odoo.tools.safe_eval import safe_eval
import logging

_logger = logging.getLogger(__name__)


# algolia search is only used on some operators
ALLOWED_OPS = set(['ilike', 'like'])


@tools.ormcache(skiparg=0)
def _get_add_algolia_search(self):
    "Add Smart Search on search views"
    return self.env['ir.model'].search([('model', '=', str(self._name))]).add_algolia_search


@tools.ormcache(skiparg=0)
def _get_use_algolia_name_search(self):
    return self.env['ir.model'].search([('model', '=', str(self._name))]).use_algolia_name_search


class Base(models.AbstractModel):

    # TODO perhaps better to create only the field when enabled on the model
    _inherit = 'base'

    algolia_search = fields.Char(
        compute="_compute_algolia_search",
        search="_search_algolia_search",
    )

    def _compute_algolia_search(self):
        self.update({'algolia_search': False})

    @api.model
    def _search_algolia_search(self, operator, name):
        """
        Por ahora este método no llama a
        self.name_search(name, operator=operator) ya que este no es tan
        performante si se llama a ilimitados registros que es lo que el
        name search debe devolver. Por eso se reimplementa acá nuevamente.
        Además name_search tiene una lógica por la cual trata de devolver
        primero los que mejor coinciden, en este caso eso no es necesario
        Igualmente seguro se puede mejorar y unificar bastante código
        """
        if name and operator in ALLOWED_OPS:
            rec_ids = self.env['ir.model'].search([('model', '=', str(self._name))])._agolia_search(name)
            return [('id', 'in', rec_ids)]
        return []


class IrModel(models.Model):
    _inherit = 'ir.model'

    use_algolia_name_search = fields.Boolean(help="Use Algolia as search engine on m2o fields",)
    add_algolia_search = fields.Boolean(help="Add Algolia Search on search views",)
    algolia_use_given_index = fields.Char()
    algolia_given_index_id_field = fields.Char(help='Field that store the ID on this index')
    algolia_index_name = fields.Char(compute='_compute_algolia_index_name')
    algolia_field_ids = fields.One2many('algolia.field', 'model_id', string='Algolia Attributes')
    algolia_domain = fields.Char(string="Odoo Domain",)
    algolia_last_sync = fields.Datetime(
        readonly="True",
        help="Only records that has been modified (write date) after this date are going to be syncked")

    @api.depends('model')
    def _compute_algolia_index_name(self):
        index_prefix = self.env["ir.config_parameter"].sudo().get_param('base_algolia_search.index_prefix') or ''
        for rec in self:
            rec.algolia_index_name = rec.algolia_use_given_index or '%s%s' % (index_prefix, rec.model)

    @api.model
    def _algolia_get_client(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        appId = get_param('base_algolia_search.algolia_application_ident')
        key = get_param('base_algolia_search.algolia_api_key')
        if not key or not appId:
            raise ValidationError(_('Algolia key or appId notconfigured'))
        return SearchClient.create(appId, key)

    def _agolia_search(self, name, filters=None, limit=None):
        """ Algolia doc:
        * https://www.algolia.com/doc/api-client/methods/search/
        * more parameters here https://www.algolia.com/doc/api-reference/search-api-parameters/
        Algolia por defecto solo devuelve como máximo 1000 resultados, no recomiendan mandar mas por temas de
        perforamnce si se querria obtener mas se podria hacer algo así pero requiere api key full
        # index.set_settings({'paginationLimitedTo': limit})
        """
        self.ensure_one()
        _logger.debug('Using algolia search')
        try:
            client = self._algolia_get_client()
            index = client.init_index(self.algolia_index_name)
            # if no limit use 1000 limit of algolia (recommended for performance)
            # we don't make pagination, we just return
            limit = limit or 1000
            # no necesario, pero lo agregamos para casos de name search donde limite es menor a 1000
            # TODO probar mandarlo abajo directamente
            # we dont want pagination, we use hitsPerPage = to paginationLimitedTo
            # attributesToRetrieve = self.algolia_given_index_id_field and [self.algolia_given_index_id_field] or []
            objects = index.search(name, {'attributesToRetrieve': [], 'hitsPerPage': limit, 'filters': filters})
        except Exception as e:
            raise ValidationError(_('No pudimos conectarnos a Algolia. Esto es lo que recibimos: %s') % e)
        id_field = self.algolia_given_index_id_field or 'objectID'
        rec_ids = [int(rec.get(id_field)) for rec in objects['hits']]
        return rec_ids

    def algolia_index_sync(self):
        alg_client = self._algolia_get_client()
        for rec in self.filtered(lambda x: not x.algolia_use_given_index and x.algolia_field_ids):
            if rec.algolia_domain:
                domain = safe_eval(rec.algolia_domain)
            else:
                domain = []
            if not self._context.get('update_all') and rec.algolia_last_sync:
                domain = [('write_date', '>', rec.algolia_last_sync)] + domain
            index = alg_client.init_index(self.algolia_index_name)
            objects = []
            model_recs = rec.env[rec.model].search(domain)
            odoo_fields = rec.algolia_field_ids.mapped('field_id')
            fields_list = odoo_fields.filtered(lambda x: x.ttype not in ['many2many', 'one2many']).mapped('name')
            fields_2_many = odoo_fields.filtered(lambda x: x.ttype in ['many2many', 'one2many'])
            model_recs_datas = model_recs.export_data(['.id'] + fields_list)['datas']
            for model_rec, data in zip(model_recs, model_recs_datas):
                item = dict(zip(['objectID'] + fields_list, data))
                # odoo exporta los m2m en dos lineas (Exportando xml_id los separa con coma bien)
                for field_2_many in fields_2_many:
                    item[field_2_many.name] = model_rec.mapped('%s.display_name' % field_2_many.name)
                objects.append(item)
            index.save_objects(objects)

            searchable_list = []
            for priority in rec.algolia_field_ids.filtered('searchable').mapped('priority'):
                searchable_list.append(", ".join(rec.algolia_field_ids.filtered(
                    lambda x: x.searchable and x.priority == priority).mapped(
                        lambda x: x.unordered and "unordered(%s)" % x.field_id.name or x.field_id.name)))
            index.set_settings({'searchableAttributes': searchable_list})
            rec.algolia_last_sync = fields.Datetime.now()

    @api.model
    def _cron_algolia_index_sync(self):
        # just with algolia fields we sync so that user is allowed to test sync before enabling search
        algolia_models = self.search([('algolia_field_ids', '!=', False)])
        if algolia_models:
            algolia_models.algolia_index_sync()

    @api.constrains('algolia_field_ids', 'algolia_use_given_index', 'algolia_given_index_id_field')
    def _check_algolia_setup(self):
        for rec in self:
            if rec.algolia_use_given_index and not rec.algolia_given_index_id_field:
                raise ValidationError(_(
                    'If you use an existing index you must provide the algolia attribute that stores de rec IDs'))
            elif rec.algolia_use_given_index and rec.algolia_field_ids:
                raise ValidationError(_(
                    "You can't use an 'Algolia Existing Index' togheter with 'Algolia attributes list', please remove "
                    "one of them"))

    def _register_hook(self):

        def patch_algolia_name_search():
            @api.model
            def name_search(self, name='', args=None, operator='ilike', limit=100):
                if name and _get_use_algolia_name_search(self) and operator in ALLOWED_OPS:
                    limit = limit or 0
                    # only request to argolia when we have at least 3 chars.
                    # TODO make parametrizable.
                    if len(name) < 3:
                        res = []
                    else:
                        rec_ids = self.env['ir.model'].search([('model', '=', str(self._name))])._agolia_search(
                            name, limit=limit)
                        res = self.browse(rec_ids).name_get()
                else:
                    # Perform standard name search
                    res = name_search.origin(self, name=name, args=args, operator=operator, limit=limit)
                return res
            return name_search

        def patch_fields_view_get():
            @api.model
            def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
                res = fields_view_get.origin(
                    self, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
                if view_type == 'search' and _get_add_algolia_search(self):
                    eview = etree.fromstring(res['arch'])
                    placeholders = eview.xpath("//search/field")
                    if placeholders:
                        placeholder = placeholders[0]
                    else:
                        placeholder = eview.xpath("//search")[0]
                    placeholder.addnext(
                        etree.Element('field', {'name': 'algolia_search'}))
                    eview.remove(placeholder)
                    res['arch'] = etree.tostring(eview)
                    res['fields'].update(self.fields_get(['algolia_search']))
                return res
            return fields_view_get

        models.BaseModel._patch_method("fields_view_get", patch_fields_view_get())

        for model in self.sudo().search(self.ids or []):
            Model = self.env.get(model.model)
            if Model is not None:
                Model._patch_method('name_search', patch_algolia_name_search())

        return super(IrModel, self)._register_hook()
