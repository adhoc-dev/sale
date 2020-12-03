# Copyright 2020 Tecnativa - Alexandre Díaz
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import time

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL


class SolutionController(http.Controller):

    @http.route(['/get_solution'], type='json', auth="public", website=True)
    def get_solution(self):
        solution = http.request.env["helpdesk.solution"].search([], limit=1)
        import ipdb; ipdb.set_trace()
        solution_dict = {
            'name': solution.name,
            'ticket_description': solution.ticket_description
            }
        solution_js =[]
        solution_js.append(solution_dict)
        return solution_js

# class ProductCarouselWebsiteSale(WebsiteSale):
#     @http.route(
#         ["/website/get_solutions"],
#         type="json",
#         auth="public",
#         website=True,
#         csrf=False,
#         cache=30,
#     )
#     def render_product_carousel(
#         self, domain=False, **kwargs
#     ):
# '<div class="card bg-white"> <a href="#" role="tab" data-toggle="collapse" aria-expanded="true" class="card-header">'+ data[i].name+ '</a><div class="collapse show" role="tabpanel"><div class="card-body"> <p class="card-text">'+ data[i].ticket_description + '</p></div></div></div>';
#         import ipdb; ipdb.set_trace()
#         # Snippet options only allow a maximium of 24 records
#         # Used this way to follow Odoo implementation
#         request.context = dict(
#             request.context,
#             partner=request.env.user.partner_id)
#         records = request.env["product.template"].search(domain or [], limit=1)

#         records_grouped = []
#         record_list = []
#         for index, record in enumerate(records, 1):
#             record_list.append(record)
#         if any(record_list):
#             records_grouped.append(record_list)
#         solution = request.env["helpdesk.solution"].search(domain or [], limit=limit)


#         template = "website_helpdesk_solutions.test"
#         return request.website.viewref(template).render(
#             {
#                 "objects": records_grouped,
#                 "num_slides": len(records_grouped),
#                 "uniqueId": "pc-%d" % int(time.time() * 1000),
#             }
#         )
