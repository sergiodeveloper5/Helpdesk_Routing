{
    'name': 'Enrutamiento de Mesa de Ayuda',
    'version': '18.0.1.0.0',
    'category': 'Servicios/Mesa de Ayuda',
    'summary': 'Enruta tickets de mesa de ayuda basado en dominio de email y notifica a líderes de equipo',
    'description': """
        Este módulo enruta automáticamente los tickets de mesa de ayuda basado en el dominio de email del solicitante:
        - Emails de wavext.io -> Equipo interno
        - Todos los otros emails -> Equipo externo
        
        Características:
        - Asignación automática de equipo basada en dominio de email
        - Notificación al líder del equipo con enlace interno
        - Mapeo de dominios configurable
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'depends': ['helpdesk_mgmt'],
    'data': [
        'security/ir.model.access.csv',
        'data/helpdesk_data.xml',
        'views/helpdesk_ticket_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
