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
                            groupby=None, search_in='content', **kw):
        """ this is only to group tickets by stage on portal view by default
        """

        if not groupby:
            groupby = 'stage'

        if not sortby:
            sortby = 'stage'
        
        if not filterby:
            filterby = 'open'

        res = super().my_helpdesk_tickets(page=page, date_begin=date_begin, date_end=date_end,
                            sortby=sortby, filterby=filterby, search=search,
                            groupby=groupby, search_in=search_in, **kw)

        res.qcontext.get("searchbar_sortings", {}).update({'stage': {'label': _('Priority'), 'order': 'stage_id desc, %s' % request.env['helpdesk.ticket']._order}})


        return res
