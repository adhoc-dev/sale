from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


def new_get_search_domain(self, search, category, attrib_values, search_in_description=True):
    """ Monkey patch instead of overwriting method to allow others inheriting
    this method
    """
    domain = request.website.sale_product_domain()
    if search:
        rec_ids = request.env['ir.model'].search([('model', '=', 'product.template')])._agolia_search(search)
        domain += [('id', 'in', rec_ids)]

    if category:
        domain += [('public_categ_ids', 'child_of', int(category))]

    if attrib_values:
        attrib = None
        ids = []
        for value in attrib_values:
            if not attrib:
                attrib = value[0]
                ids.append(value[1])
            elif value[0] == attrib:
                ids.append(value[1])
            else:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]
                attrib = value[0]
                ids = [value[1]]
        if attrib:
            domain += [('attribute_line_ids.value_ids', 'in', ids)]
    return domain


WebsiteSale._get_search_domain = new_get_search_domain
