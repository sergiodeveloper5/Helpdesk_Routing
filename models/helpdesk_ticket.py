# models/helpdesk_ticket.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import logging

_logger = logging.getLogger(__name__)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    is_internal_ticket = fields.Boolean(
        string="Internal Ticket",
        compute="_compute_is_internal_ticket",
        store=True,
        help="Indicates if this ticket is from an internal user"
    )

    email_domain = fields.Char(
        string="Email Domain",
        compute="_compute_email_domain",
        store=True,
        help="Domain extracted from partner email",
        index=True
    )

    routing_processed = fields.Boolean(
        string="Routing Processed",
        default=False,
        help="Technical field to track if routing has been processed"
    )

    @api.depends('partner_email', 'partner_id.email')
    def _compute_email_domain(self):
        for ticket in self:
            email = ticket.partner_email or (ticket.partner_id and ticket.partner_id.email)
            if email:
                domain = email.split('@')[-1].lower()
                ticket.email_domain = domain
            else:
                ticket.email_domain = False

    @api.depends('email_domain')
    def _compute_is_internal_ticket(self):
        internal_domains = self.env['ir.config_parameter'].sudo().get_param(
            'Helpdesk_Routing.internal_domains', 'wavext.io'
        ).split(',')
        internal_domains = [domain.strip().lower() for domain in internal_domains]

        for ticket in self:
            ticket.is_internal_ticket = ticket.email_domain in internal_domains

    @api.model_create_multi
    def create(self, vals_list):
        # Procesar la lógica de enrutamiento ANTES de crear los tickets
        for vals in vals_list:
            # Marcar como procesado para evitar procesamiento múltiple
            if not vals.get('routing_processed', False):
                vals['routing_processed'] = True
                # Pre-procesar el enrutamiento basado en email
                self._preprocess_routing(vals)
        
        # Crear los tickets con la lógica ya aplicada
        tickets = super().create(vals_list)
        
        # Post-procesamiento solo para notificaciones
        for ticket in tickets:
            if ticket.routing_processed and not ticket.env.context.get('skip_routing_notification'):
                ticket._notify_team_leader()
        
        return tickets

    def _preprocess_routing(self, vals):
        """Pre-process routing logic before ticket creation"""
        # Extraer email del partner o del campo directo
        email = vals.get('partner_email')
        if not email and vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            email = partner.email
        
        if email:
            # Calcular dominio de email
            domain = email.split('@')[-1].lower()
            vals['email_domain'] = domain
            
            # Determinar si es ticket interno
            internal_domains = self.env['ir.config_parameter'].sudo().get_param(
                'Helpdesk_Routing.internal_domains', 'wavext.io'
            ).split(',')
            internal_domains = [d.strip().lower() for d in internal_domains]
            vals['is_internal_ticket'] = domain in internal_domains
            
            # Auto-asignar equipo si no está ya asignado
            if not vals.get('team_id'):
                team_to_assign = None
                
                if vals.get('is_internal_ticket'):
                    # Equipo interno
                    internal_team_id = self.env['ir.config_parameter'].sudo().get_param(
                        'Helpdesk_Routing.internal_team_id'
                    )
                    if internal_team_id:
                        team_to_assign = self.env['helpdesk.ticket.team'].browse(int(internal_team_id))
                    else:
                        team_to_assign = self.env.ref('Helpdesk_Routing.internal_helpdesk_team', raise_if_not_found=False)
                else:
                    # Equipo externo
                    external_team_id = self.env['ir.config_parameter'].sudo().get_param(
                        'Helpdesk_Routing.external_team_id'
                    )
                    if external_team_id:
                        team_to_assign = self.env['helpdesk.ticket.team'].browse(int(external_team_id))
                    else:
                        team_to_assign = self.env.ref('Helpdesk_Routing.external_helpdesk_team', raise_if_not_found=False)
                
                if team_to_assign and team_to_assign.exists():
                    vals['team_id'] = team_to_assign.id
                    ticket_type = "internal" if vals.get('is_internal_ticket') else "external"
                    _logger.info(f"Pre-assigned ticket to {ticket_type} team: {team_to_assign.name}")

    def _auto_assign_team(self):
        """Automatically assign team based on email domain"""
        self.ensure_one()

        # Only auto-assign if no team is already set
        if not self.team_id:
            team_to_assign = None

            if self.is_internal_ticket:
                # Try to get team from config first, then fallback to data
                internal_team_id = self.env['ir.config_parameter'].sudo().get_param(
                    'Helpdesk_Routing.internal_team_id'
                )
                if internal_team_id:
                    team_to_assign = self.env['helpdesk.ticket.team'].browse(int(internal_team_id))
                else:
                    team_to_assign = self.env.ref('Helpdesk_Routing.internal_helpdesk_team', raise_if_not_found=False)
            else:
                # Try to get team from config first, then fallback to data
                external_team_id = self.env['ir.config_parameter'].sudo().get_param(
                    'Helpdesk_Routing.external_team_id'
                )
                if external_team_id:
                    team_to_assign = self.env['helpdesk.ticket.team'].browse(int(external_team_id))
                else:
                    team_to_assign = self.env.ref('Helpdesk_Routing.external_helpdesk_team', raise_if_not_found=False)

            if team_to_assign and team_to_assign.exists():
                self.team_id = team_to_assign.id
                ticket_type = "internal" if self.is_internal_ticket else "external"
                _logger.info(f"Assigned ticket {self.name} to {ticket_type} team: {team_to_assign.name}")

    def _notify_team_leader(self):
        """Send notification to team leader using email template"""
        self.ensure_one()

        # Verificar si las notificaciones están habilitadas
        notifications_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'Helpdesk_Routing.enable_notifications', 'True'
        ).lower() == 'true'

        if not notifications_enabled:
            return

        # Verificar si ya se envió notificación para evitar duplicados
        if self.env.context.get('notification_sent') or self.env.context.get('skip_routing_notification'):
            _logger.debug(f"Skipping notification for ticket {self.name} - already sent or skipped")
            return

        if not self.team_id or not self.team_id.user_id:
            _logger.warning(f"No team leader found for ticket {self.name}")
            return

        team_leader = self.team_id.user_id

        # Send email notification using template
        try:
            mail_template = self.env.ref('Helpdesk_Routing.ticket_assignment_email_template', raise_if_not_found=False)
            if mail_template:
                # Use with_context to ensure proper email sending
                mail_template.with_context(
                    lang=team_leader.lang or self.env.user.lang
                ).send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        'email_to': team_leader.email,
                        'recipient_ids': [(4, team_leader.partner_id.id)],
                    }
                )
                _logger.info(f"Sent email notification to {team_leader.email} for ticket {self.name}")
            else:
                _logger.warning(f"Email template 'Helpdesk_Routing.ticket_assignment_email_template' not found")
        except Exception as e:
            _logger.error(f"Could not send email notification for ticket {self.name}: {e}")

        # Send in-app notification (chatter message) - use template directly
        try:
            mail_template = self.env.ref('Helpdesk_Routing.ticket_assignment_email_template', raise_if_not_found=False)
            if mail_template:
                # Use the template's send_mail method but post to chatter instead
                mail_values = mail_template.generate_email([self.id])[self.id]
                
                self.message_post(
                    body=mail_values.get('body_html', ''),
                    subject=mail_values.get('subject', ''),
                    partner_ids=[team_leader.partner_id.id],
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                _logger.info(f"Sent template-generated notification to team leader {team_leader.name} for ticket {self.name}")
            else:
                # Fallback to simple notification if template not found
                ticket_type = "Internal" if self.is_internal_ticket else "External"
                simple_body = f"""
                <p>New {ticket_type.lower()} ticket assigned to your team.</p>
                <p><strong>Ticket:</strong> {self.name}<br/>
                <strong>Customer:</strong> {self.partner_id.name if self.partner_id else 'Guest'}<br/>
                <strong>Email:</strong> {self.partner_email or (self.partner_id.email if self.partner_id else 'No email')}</p>
                """

                self.message_post(
                    body=simple_body,
                    subject=f"New {ticket_type} Ticket Assigned",
                    partner_ids=[team_leader.partner_id.id],
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                _logger.warning(f"Used fallback notification for ticket {self.name} - template not found")
        except Exception as e:
            _logger.warning(f"Could not send in-app notification for ticket {self.name}: {e}")
        
        # Marcar notificación como enviada en el contexto para evitar duplicados
        self.env.context = dict(self.env.context, notification_sent=True)

    def write(self, vals):
        result = super().write(vals)

        # Si partner_email o partner_id es actualizado, reprocesar enrutamiento si es necesario
        if ('partner_email' in vals or 'partner_id' in vals) and not vals.get('routing_processed'):
            for ticket in self:
                if not ticket.team_id:  # Solo reasignar si no hay equipo asignado
                    # Usar el contexto para evitar notificaciones duplicadas
                    ticket.with_context(skip_routing_notification=True)._auto_assign_team()
                    ticket._notify_team_leader()
                    ticket.routing_processed = True

        return result
