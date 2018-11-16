##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.helpdesk.controllers.portal import CustomerPortal
from odoo.http import request, route
from odoo import _


class CustomerPortal(CustomerPortal):

    @route()
    def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None,
                            sortby=None, filterby=None, search=None,
                            search_in='content', **kw):
        response = super(CustomerPortal, self).my_helpdesk_tickets(
            page=page, date_begin=date_begin, date_end=date_end,
            sortby=sortby, filterby=filterby, search=search,
            search_in=search_in, **kw)

        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = ['|', ('user_id', '=', user.id), ('partner_id', 'child_of', user.partner_id.commercial_partner_id.id)]

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('Open'),
                     'domain': [('stage_id.is_close', '=', False)]},
        }
        # default filter
        if not filterby:
            filterby = 'open'
        domain += searchbar_filters[filterby]['domain']

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        tickets_count = request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={
                'date_begin': date_begin, 'date_end': date_end,
                'sortby': sortby, 'filterby': filterby, 'search_in': search_in,
                'search': search},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )
        tickets = request.env['helpdesk.ticket'].sudo().search(
            domain, order=order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_tickets_history'] = tickets.ids[:100]

        response.qcontext.update({
            'tickets': tickets,
            'pager': pager,
            'searchbar_filters': OrderedDict(
                sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return response
