import logging

logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    The objective of this hook is to speed up the installation
    of the module on an existing Odoo instance.

    Without this script, big databases can take a long time to install this
    module.
    """
    cr.execute("""SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_partial_reconcile' AND
    column_name='exchange_diff_adjustment_required'""")
    if not cr.fetchone():
        logger.info('Creating field exchange_diff_adjustment_required')
        cr.execute(
            """
            ALTER TABLE account_partial_reconcile
            ADD COLUMN exchange_diff_adjustment_required boolean
            """)
