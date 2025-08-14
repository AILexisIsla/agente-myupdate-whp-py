import os
import json
from flask import Flask, request
from dotenv import load_dotenv
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

# --- INICIALIZACIÓN Y CONFIGURACIÓN ---
load_dotenv()
app = Flask(__name__)

# Clientes de servicios
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
twilio_client = TwilioClient(twilio_sid, twilio_token)

gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

# Modelo para crear embeddings para la búsqueda vectorial
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- HERRAMIENTAS QUE LA IA PUEDE UTILIZAR ---

def search_product_information(query: str) -> str:
    """
    Busca información relevante en la base de datos vectorial para responder
    preguntas generales o contextuales sobre los productos.
    """
    try:
        query_embedding = embedding_model.encode(query).tolist()
        params = {
            'query_embedding': query_embedding,
            'match_threshold': 0.3,
            'match_count': 5
        }
        response = supabase.rpc('match_documents', params).execute()
        documents = response.data
        
        if not documents:
            return "No se encontró información relevante para esa consulta."

        # Formatea la respuesta como un string simple
        info_string = "Se encontró la siguiente información relevante:\n"
        for doc in documents:
            info_string += f"- {doc.get('content', 'Contenido no disponible')}\n"
        return info_string
    except Exception as e:
        return f"Error al buscar información: {str(e)}"

def get_product_inventory(tipo_prenda: str = None, talla: str = None, color: str = None) -> str:
    """
    Consulta el inventario de productos específicos en la base de datos.
    Útil para preguntas directas como '¿tienes pantalones talla L?'.
    """
    try:
        query = supabase.table('DB').select('ID, TIPO_PRENDA, TALLA, COLOR, CANTIDAD_DISPONIBLE').ilike('DISPONIBLE', 'sí')
        if tipo_prenda:
            query = query.ilike('TIPO_PRENDA', f'%{tipo_prenda}%')
        if talla:
            query = query.eq('TALLA', talla)
        if color:
            query = query.ilike('COLOR', f'%{color}%')
        
        response = query.limit(10).execute()
        products = response.data
        
        if not products:
            return "No se encontraron productos con esos criterios."

        # Formatea la respuesta como un string simple
        inventory_string = "Resultados del inventario:\n"
        for p in products:
            inventory_string += f"- ID: {p.get('ID')}, Prenda: {p.get('TIPO_PRENDA')}, Talla: {p.get('TALLA')}, Color: {p.get('COLOR')}, Stock: {p.get('CANTIDAD_DISPONIBLE')}\n"
        return inventory_string
    except Exception as e:
        return f"Error al obtener el inventario: {str(e)}"

def place_b2b_order(product_id: int, quantity: int) -> str:
    """
    Registra un pedido de compra para un producto y cantidad específicos.
    """
    try:
        product_res = supabase.table('DB').select('*').eq('ID', product_id).single().execute()
        product = product_res.data
        if not product:
            return json.dumps({"status": "error", "message": "Producto no encontrado."})
        if product['CANTIDAD_DISPONIBLE'] < quantity:
            return json.dumps({"status": "error", "message": f"Stock insuficiente. Disponibles: {product['CANTIDAD_DISPONIBLE']}."})

        price_per_unit = get_price_for_quantity(product, quantity)
        if price_per_unit is None:
            return json.dumps({"status": "error", "message": "La cantidad mínima de compra es de 50 unidades."})
        
        total_price = price_per_unit * quantity

        # Insertar el pedido en la base de datos
        order_data = {
            "customer_phone": "whatsapp_user",
            "product_id": product_id,
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "total_price": total_price
        }
        supabase.table('b2b_orders').insert(order_data).execute()

        # Actualizar stock
        new_stock = product['CANTIDAD_DISPONIBLE'] - quantity
        supabase.table('DB').update({'CANTIDAD_DISPONIBLE': new_stock}).eq('ID', product_id).execute()

        confirmation_details = {
            "status": "success",
            "message": f"¡Pedido confirmado! Se ha registrado un pedido para {quantity} unidades del producto ID {product_id}."
        }
        return json.dumps(confirmation_details)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def get_price_for_quantity(product, quantity):
    """Función auxiliar para determinar el precio por unidad."""
    if quantity < 50: return None
    if quantity >= 200 and product.get("PRECIO_200_U"): return product["PRECIO_200_U"]
    if quantity >= 100 and product.get("PRECIO_100_U"): return product["PRECIO_100_U"]
    if quantity >= 50 and product.get("PRECIO_50_U"): return product["PRECIO_50_U"]
    return None

# --- LÓGICA DEL AGENTE CON IA (GEMINI) ---

tools = [get_product_inventory, place_b2b_order, search_product_information]
model = genai.GenerativeModel(model_name='gemini-1.5-flash', tools=tools)
chat_sessions = {}

def run_agent_conversation(from_number, message_body):
    """Orquesta la conversación entre el usuario y la IA."""
    if from_number not in chat_sessions:
        chat_sessions[from_number] = model.start_chat()
    chat = chat_sessions[from_number]

    response = chat.send_message(message_body)
    
    # Bucle para manejar llamadas a funciones hasta obtener una respuesta de texto.
    while response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        function_name = function_call.name
        args = {key: value for key, value in function_call.args.items()}
        
        print(f"IA quiere llamar a la función: {function_name} con argumentos: {args}")
        function_to_call = globals()[function_name]
        function_response_str = function_to_call(**args)
        
        # CORRECCIÓN: Se devuelve a la IA la respuesta de la función como un string simple,
        # envuelto en un diccionario para evitar errores de formato.
        response = chat.send_message(
            [{"function_response": {"name": function_name, "response": {"content": function_response_str}}}]
        )

    final_reply = response.text
    send_whatsapp_message(from_number, final_reply)

# --- WEBHOOK Y COMUNICACIÓN ---

def send_whatsapp_message(to_number, message_body):
    """Función para enviar un mensaje de WhatsApp usando Twilio."""
    try:
        twilio_client.messages.create(
            from_=twilio_phone_number,
            body=message_body,
            to=f'whatsapp:{to_number}'
        )
        print(f"Respuesta enviada a {to_number}")
    except Exception as e:
        print(f"Error al enviar mensaje de WhatsApp: {e}")

@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Webhook para recibir mensajes de WhatsApp de Twilio."""
    incoming_message = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '').replace('whatsapp:', '')
    
    print(f"Mensaje recibido de {from_number}: {incoming_message}")
    if from_number and incoming_message:
        run_agent_conversation(from_number, incoming_message)
    return "OK", 200

# --- EJECUCIÓN DE LA APLICACIÓN ---
if __name__ == '__main__':
    app.run(port=5000, debug=True)