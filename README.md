<div align="center">

<h3 align="center">Agente de Ventas B2B con IA para WhatsApp</h3>

<div align="center">
Un bot conversacional inteligente que gestiona inventario y pedidos de forma automática, integrado con WhatsApp.
</div>
🤸 Guía de Inicio Rápido

<a name="introducción">🤖 Introducción</a>
Este proyecto es un agente de ventas B2B diseñado para operar a través de WhatsApp. Utiliza la inteligencia artificial de Google Gemini para mantener conversaciones naturales con los clientes, entender sus necesidades y gestionar transacciones de venta. El agente se conecta a una base de datos en Supabase para consultar inventarios, incluyendo una base de datos vectorial para responder preguntas contextuales, y registrar nuevos pedidos. La comunicación con WhatsApp se gestiona a través de la API de Twilio.

<a name="tech-stack">⚙️ Stack Tecnológico</a>
Backend: Python, Flask

Base de Datos: Supabase (PostgreSQL con pgvector)

IA Conversacional: Google Gemini

Mensajería: Twilio API para WhatsApp

Creación de Embeddings: Sentence-Transformers

<a name="features">🔋 Características</a>
👉 Conversación Inteligente: Gracias a Google Gemini, el agente puede entender el lenguaje natural, manteniendo conversaciones fluidas y respondiendo a preguntas complejas.

👉 Búsqueda Semántica de Productos: Utiliza una base de datos vectorial en Supabase para encontrar productos basados en descripciones contextuales (ej: "¿qué ropa tienes para el verano?").

👉 Gestión de Inventario en Tiempo Real: Consulta el stock de productos directamente desde la base de datos para proporcionar información precisa y actualizada.

👉 Procesamiento de Pedidos Automatizado: Los clientes pueden realizar pedidos directamente desde WhatsApp. El agente valida el stock, calcula precios por volumen y registra la orden en la base de datos.

👉 Integración con WhatsApp: Se conecta de forma segura a la API de WhatsApp a través de Twilio, permitiendo una comunicación directa con los clientes en su plataforma de mensajería preferida.

👉 Escalable y Flexible: Construido con herramientas robustas que permiten añadir nuevas funcionalidades y "herramientas" para la IA fácilmente.

<a name="quick-start">🤸 Guía de Inicio Rápido</a>
Sigue estos pasos para configurar y ejecutar el proyecto en tu máquina local.

Prerrequisitos

Asegúrate de tener lo siguiente instalado:

Git

Python

pip

Clonar el Repositorio

git clone [URL_DE_TU_REPOSITORIO]
cd [NOMBRE_DE_LA_CARPETA]

Crear un Entorno Virtual (Recomendado)

python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

Instalación de Dependencias

Instala todas las librerías necesarias con pip:

pip install Flask python-dotenv supabase twilio google-generativeai sentence-transformers

Configurar Variables de Entorno

Crea un archivo llamado .env en la raíz de tu proyecto y añade el siguiente contenido, reemplazando los valores entre corchetes con tus credenciales reales:

SUPABASE_URL="https://[ID_PROYECTO].supabase.co"
SUPABASE_KEY="[TU_SUPABASE_ANON_KEY]"

TWILIO_ACCOUNT_SID="[TU_TWILIO_ACCOUNT_SID]"
TWILIO_AUTH_TOKEN="[TU_TWILIO_AUTH_TOKEN]"
TWILIO_PHONE_NUMBER="whatsapp:+14155238886"

GEMINI_API_KEY="[TU_GEMINI_API_KEY]"

Ejecutar el Proyecto

python main.py

El servidor se iniciará en http://127.0.0.1:5000. Para conectar el agente con WhatsApp, necesitarás exponer este servidor a internet usando una herramienta como ngrok.
