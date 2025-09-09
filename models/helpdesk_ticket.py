# models/helpdesk_ticket.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import logging

_logger = logging.getLogger(__name__)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    is_internal_ticket = fields.Boolean(
        string="Ticket Interno",
        compute="_compute_is_internal_ticket",
        store=True,
        help="Indica si este ticket es de un usuario interno"
    )

    email_domain = fields.Char(
        string="Dominio de Email",
        compute="_compute_email_domain",
        store=True,
        help="Dominio extraído del email del contacto",
        index=True
    )

    routing_processed = fields.Boolean(
        string="Enrutamiento Procesado",
        default=False,
        help="Campo técnico para rastrear si el enrutamiento ha sido procesado"
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
        tickets = super().create(vals_list)
        for ticket in tickets:
            if not ticket.routing_processed:
                ticket._auto_assign_team()
                ticket._notify_team_leader()
                ticket.routing_processed = True
        return tickets

    def _auto_assign_team(self):
        """Asignar automáticamente equipo basado en dominio de email"""
        self.ensure_one()

        # Solo auto-asignar si no hay equipo ya establecido
        if not self.team_id:
            team_to_assign = None

            if self.is_internal_ticket:
                # Intentar obtener equipo de configuración primero, luego usar datos por defecto
                internal_team_id = self.env['ir.config_parameter'].sudo().get_param(
                    'Helpdesk_Routing.internal_team_id'
                )
                if internal_team_id:
                    team_to_assign = self.env['helpdesk.ticket.team'].browse(int(internal_team_id))
                else:
                    team_to_assign = self.env.ref('Helpdesk_Routing.internal_helpdesk_team', raise_if_not_found=False)
            else:
                # Intentar obtener equipo de configuración primero, luego usar datos por defecto
                external_team_id = self.env['ir.config_parameter'].sudo().get_param(
                    'Helpdesk_Routing.external_team_id'
                )
                if external_team_id:
                    team_to_assign = self.env['helpdesk.ticket.team'].browse(int(external_team_id))
                else:
                    team_to_assign = self.env.ref('Helpdesk_Routing.external_helpdesk_team', raise_if_not_found=False)

            if team_to_assign and team_to_assign.exists():
                self.team_id = team_to_assign.id
                ticket_type = "interno" if self.is_internal_ticket else "externo"
                _logger.info(f"Ticket {self.name} asignado a equipo {ticket_type}: {team_to_assign.name}")

    def _notify_team_leader(self):
        """Enviar notificación al líder del equipo usando plantilla de email"""
        self.ensure_one()

        # Verificar si las notificaciones están habilitadas
        notifications_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'Helpdesk_Routing.enable_notifications', 'True'
        ).lower() == 'true'

        if not notifications_enabled:
            return

        if not self.team_id or not self.team_id.user_id:
            _logger.warning(f"No se encontró líder de equipo para el ticket {self.name}")
            return

        team_leader = self.team_id.user_id

        # Enviar notificación por email usando plantilla
        try:
            mail_template = self.env.ref('Helpdesk_Routing.ticket_assignment_email_template', raise_if_not_found=False)
            if mail_template:
                # Usar with_context para asegurar el envío correcto del email
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
                _logger.info(f"Notificación por email enviada a {team_leader.email} para el ticket {self.name}")
            else:
                _logger.warning(f"Plantilla de email 'Helpdesk_Routing.ticket_assignment_email_template' no encontrada")
        except Exception as e:
            _logger.error(f"No se pudo enviar notificación por email para el ticket {self.name}: {e}")

        # Enviar notificación en la aplicación (mensaje en chatter) - versión simplificada
        try:
            ticket_type = "Interno" if self.is_internal_ticket else "Externo"
            simple_body = f"""
            <p>Nuevo ticket {ticket_type.lower()} asignado a tu equipo.</p>
            <p><strong>Ticket:</strong> {self.name}<br/>
            <strong>Cliente:</strong> {self.partner_id.name if self.partner_id else 'Invitado'}<br/>
            <strong>Email:</strong> {self.partner_email or (self.partner_id.email if self.partner_id else 'Sin email')}</p>
            """

            self.message_post(
                body=simple_body,
                subject=f"Nuevo Ticket {ticket_type} Asignado",
                partner_ids=[team_leader.partner_id.id],
                message_type='notification',
                subtype_xmlid='mail.mt_note'  # Usar mt_note en lugar de mt_comment
            )
            _logger.info(f"Notificación en la aplicación enviada al líder de equipo {team_leader.name} para el ticket {self.name}")
        except Exception as e:
            _logger.warning(f"No se pudo enviar notificación en la aplicación para el ticket {self.name}: {e}")

    def write(self, vals):
        result = super().write(vals)

        # Si partner_email o partner_id se actualiza, reprocesar enrutamiento si es necesario
        if ('partner_email' in vals or 'partner_id' in vals) and not vals.get('routing_processed'):
            for ticket in self:
                if not ticket.team_id:  # Solo reasignar si no hay equipo establecido
                    ticket._auto_assign_team()
                    ticket._notify_team_leader()
                    ticket.routing_processed = True

        return result
