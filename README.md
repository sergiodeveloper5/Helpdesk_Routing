Módulo de Enrutamiento de Tickets de Helpdesk
🚀 Enruta automáticamente los tickets de helpdesk basándose en dominios de email y notifica a los líderes de equipo con enlaces internos.

📌 Características
✔ Asignación Automática de Equipos

Tickets de @wavext.io → Equipo Interno

Todos los demás dominios → Equipo Externo

✔ Mapeo de Dominios Configurable

Establece dominios personalizados para tickets internos a través de Configuración

✔ Notificaciones a Líderes de Equipo

Email + notificaciones en la aplicación con enlaces directos al ticket

✔ Mejoras en el Panel de Control

Nuevos filtros (tickets Internos/Externos)

Visibilidad del dominio de email en las vistas

🛠 Instalación
Clona o añade el módulo a tu carpeta de addons de Odoo:

bash
git clone [tu-url-repo] /opt/odoo17/odoo-custom-addons/Helpdesk_Routing
Instala el módulo:

Ve a Aplicaciones → Actualizar Lista de Aplicaciones

Busca "Helpdesk Ticket Routing" → Haz clic en Instalar

⚙ Configuración
Configura Equipos y Dominios

Ve a Configuración → Helpdesk → Enrutamiento de Tickets

Configura:

Dominios de Email Internos (ej., wavext.io)

Equipos Internos/Externos

Habilita Notificaciones

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

