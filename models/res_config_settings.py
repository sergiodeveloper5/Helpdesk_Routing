# models/res_config_settings.py
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    internal_domains = fields.Char(
        string="Dominios de Email Internos",
        config_parameter='helpdesk_routing.internal_domains',
        default='wavext.io',
        help="Lista separada por comas de dominios de email internos"
    )
    
    internal_team_id = fields.Many2one(
        'helpdesk.ticket.team',
        string="Equipo Interno",
        config_parameter='helpdesk_routing.internal_team_id',
        help="Equipo para tickets internos"
    )
    
    external_team_id = fields.Many2one(
        'helpdesk.ticket.team',
        string="Equipo Externo", 
        config_parameter='helpdesk_routing.external_team_id',
        help="Equipo para tickets externos"
    )
