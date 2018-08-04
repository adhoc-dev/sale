from openupgradelib import openupgrade


table_renames = [
    ('project_issue_solution', 'helpdesk_solution'),
    ('project_solution_tag', 'helpdesk_solution_tag'),
    ('project_issue_solution_project_solution_tag_rel', 'helpdesk_solution_helpdesk_solution_tag_rel'),
]

model_renames = [
    ('project.solution.tag', 'helpdesk.solution.tag'),
    ('helpdesk.solution', 'project.issue.solution'),
]

column_renames = {
    'project_issue_solution': [
        ('issue_description', 'ticket_description'),
    ],
    'project_issue_solution_project_solution_tag_rel': [
        ('project_issue_solution_id', 'helpdesk_solution_id'),
        ('project_solution_tag_id', 'helpdesk_solution_tag_id'),
    ],
    'helpdesk_ticket': [
        ('issue_description', 'ticket_description'),
        ('project_issue_solution_id', 'helpdesk_solution_id'),
    ],
}

field_renames = [
    ('project.solution.tag', 'project_issue_solution',
        'issue_description', 'ticket_description'),
    ('project.issue', 'project_issue', 'issue_description',
        'ticket_description'),
    ('project.issue', 'project_issue', 'project_issue_solution_id',
        'helpdesk_solution_id'),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr
    openupgrade.rename_columns(cr, column_renames)
    openupgrade.rename_fields(env, field_renames)
    openupgrade.rename_tables(cr, table_renames)
    openupgrade.rename_models(cr, model_renames)
    # parte de la migracion la estamos haciendo en post-upgrades de nube
