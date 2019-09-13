# flake8: noqa
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from collections import OrderedDict
from operator import itemgetter
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.helpdesk.controllers.portal import CustomerPortal
from odoo.http import request, route
from odoo import _
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem


class CustomerPortal(CustomerPortal):

    @route()
    def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None,
                            sortby=None, filterby=None, search=None,
                            search_in='content', groupby='stage', **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = ['|', ('user_id', '=', user.id), ('partner_id', 'child_of', user.partner_id.commercial_partner_id.id)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
            'stage': {'label': _('Priority'), 'order': 'stage_id desc, %s' % request.env['helpdesk.ticket']._order},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('Open'),
                     'domain': [('stage_id.is_close', '=', False)]},
            'closed': {'label': _(' Resolved'),
                       'domain': [('stage_id.is_close', '=', True)], 'order': 'close_date'},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'stage': {'input': 'stage', 'label': _('Stage')},
        }

        # default sort by value
        if not sortby:
            sortby = 'stage'
        order = searchbar_sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = 'open'
        domain += searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('helpdesk.ticket', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            domain += search_domain

        # pager
        tickets_count = request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            # url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        # group by
        if groupby == 'stage':
            order = "stage_id desc, %s" % order  # force sort on stage first to group by stage in view
        tickets = request.env['helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_tickets_history'] = tickets.ids[:100]

        if groupby == 'stage':
            grouped_tickets = [request.env['helpdesk.ticket'].concat(*g) for k, g in groupbyelem(tickets, itemgetter('stage_id'))]
        else:
            grouped_tickets = [tickets]

        values.update({
            'date': date_begin,
            # el tickets es medio al pedo, solo para un t-if al principio que
            # podria reemplazarse por grouped_tickets
            'tickets': tickets,
            'grouped_tickets': grouped_tickets,
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("helpdesk.portal_helpdesk_ticket", values)
