Módulo de Enrutamiento de Tickets de Mesa de Ayuda
🚀 Enruta automáticamente tickets de mesa de ayuda basado en dominios de email y notifica a líderes de equipo con enlaces internos.

📌 Características
✔ Asignación Automática de Equipos

Tickets de @wavext.io → Equipo Interno

Todos los otros dominios → Equipo Externo

✔ Mapeo de Dominios Configurable

Establecer dominios personalizados para tickets internos vía Configuración

✔ Notificaciones a Líderes de Equipo

Email + notificaciones en la aplicación con enlaces directos al ticket

✔ Mejoras en el Panel de Control

Nuevos filtros (tickets Internos/Externos)

Visibilidad del dominio de email en las vistas

🛠 Instalación
Clona o agrega el módulo a tu carpeta de addons de Odoo:

bash
git clone [tu-repo-url] /opt/odoo18/odoo-custom-addons/Helpdesk_Routing
Instala el módulo:

Ve a Aplicaciones → Actualizar Lista de Aplicaciones

Busca "Enrutamiento de Mesa de Ayuda" → Haz clic en Instalar

⚙ Configuración
Configurar Equipos y Dominios

Ve a Configuración → Mesa de Ayuda → Enrutamiento de Tickets

Configura:

Dominios de Email Internos (ej., wavext.io)

Equipos Internos/Externos

Habilitar Notificaciones

Asegúrate de asignar un usuario interno verificado en los equipos

📂 Estructura de Archivos
text
Helpdesk_Routing/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── helpdesk_ticket.py          # Lógica principal de enrutamiento
│   └── res_config_settings.py      # Opciones de configuración
├── security/
│   └── ir.model.access.csv         # Permisos
├── data/
│   └── helpdesk_data.xml           # Equipos por defecto + plantilla de email
└── views/
    ├── helpdesk_ticket_views.xml    # Mejoras de interfaz
    └── res_config_settings_views.xml  # Panel de configuración
🔧 Dependencias
Odoo 18.0+

módulo helpdesk_mgmt

🚨 Solución de Problemas
"¿El módulo no aparece?"

Verifica __manifest__.py para dependencias correctas.

Reinicia Odoo y actualiza el módulo.

"¿Las notificaciones no se envían?"

Verifica las plantillas de email (data/helpdesk_data.xml).

Revisa Configuración → Técnico → Email → Registros.

"¿La asignación de equipo falla?"

Asegúrate de que team_id existe en el modelo helpdesk.ticket.

