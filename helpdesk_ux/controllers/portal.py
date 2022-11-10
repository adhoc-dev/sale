# flake8: noqa
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.helpdesk.controllers.portal import CustomerPortal as HelpdeskCustomerPortal
from odoo.http import request, route
from odoo import _


class CustomerPortal(HelpdeskCustomerPortal):

    @route()
    def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None,
                            sortby=None, filterby=None, search=None,
                            groupby=None, search_in='content', **kw):
        """ this is only to group tickets by stage on portal view by default
        """

        if not groupby:
            groupby = 'stage'
        if not sortby:
            sortby = 'stage'
        if not filterby:
            filterby = 'open'

        if sortby == 'stage':
            ctx = request.env.context.copy()
            ctx.update({'order_by_priority':True})
            request.env.context = ctx
        values = self._prepare_my_tickets_values(page, date_begin, date_end, sortby, filterby, search, groupby, search_in)
        values.get("searchbar_sortings", {}).update({'stage': {'label': _('Priority'), 'order': 'stage_id desc, %s' % request.env['helpdesk.ticket']._order}})
        return request.render("helpdesk.portal_helpdesk_ticket", values)
