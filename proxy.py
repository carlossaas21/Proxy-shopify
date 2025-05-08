from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging
import certifi

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurar CORS permitindo especificamente o domínio do Bubble
CORS(app, resources={
    r"/proxy/customers": {
        "origins": [
            "https://ecomlyze-62237.bubbleapps.io",
            "http://localhost:3000"  # Para testes locais, se necessário
        ],
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "OPTIONS"]
    }
})

def get_customer_orders(shop_domain, access_token, customer_id):
    """Obtém os pedidos de um cliente específico"""
    api_url = f'https://{shop_domain}/admin/api/2023-04/customers/{customer_id}/orders.json'
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10, verify=certifi.where())
        response.raise_for_status()
        return response.json().get('orders', [])
    except Exception as e:
        logger.error(f"Erro ao buscar pedidos do cliente {customer_id}: {str(e)}")
        return []

def format_customer_data(customer, orders):
    """Formata os dados do cliente com as informações solicitadas"""
    return {
        'first_name': customer.get('first_name', ''),
        'last_name': customer.get('last_name', ''),
        'phone': customer.get('phone', ''),
        'orders': [
            {
                'product_id': item.get('product_id'),
                'product_title': item.get('title', ''),
                'quantity': item.get('quantity', 0)
            }
            for order in orders
            for item in order.get('line_items', [])
        ]
    }

@app.route('/proxy/customers', methods=['GET', 'OPTIONS'])
def get_shopify_customers():
    logger.info("Recebida requisição para /proxy/customers")
    logger.info(f"Parâmetros: shop_domain={request.args.get('shop_domain')}, access_token={request.args.get('access_token')}")

    # Obter parâmetros da query string
    shop_domain = request.args.get('shop_domain')
    access_token = request.args.get('access_token')

    # Validar parâmetros
    if not shop_domain or not access_token:
        logger.error("Parâmetros shop_domain e access_token são obrigatórios")
        return jsonify({
            'error': 'Parâmetros shop_domain e access_token são obrigatórios'
        }), 400

    # Construir a URL da API do Shopify
    api_url = f'https://{shop_domain}/admin/api/2023-04/customers.json'
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }

    try:
        logger.info(f"Fazendo requisição para Shopify: {api_url}")
        response = requests.get(api_url, headers=headers, timeout=10, verify=certifi.where())
        response.raise_for_status()

        # Processar a resposta
        customers_data = response.json().get('customers', [])
        formatted_customers = []

        for customer in customers_data:
            # Buscar pedidos do cliente
            orders = get_customer_orders(shop_domain, access_token, customer['id'])
            # Formatar dados do cliente
            formatted_customer = format_customer_data(customer, orders)
            formatted_customers.append(formatted_customer)

        logger.info("Requisição ao Shopify bem-sucedida")
        return jsonify({'customers': formatted_customers}), 200

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Erro HTTP ao acessar a API do Shopify: {str(http_err)}")
        logger.error(f"Resposta do Shopify: {response.text if 'response' in locals() else 'Sem resposta'}")
        return jsonify({
            'error': f'Erro HTTP ao acessar a API do Shopify: {str(http_err)}',
            'details': response.text if 'response' in locals() else 'Sem detalhes'
        }), response.status_code if 'response' in locals() else 500

    except requests.exceptions.Timeout:
        logger.error("Timeout ao acessar a API do Shopify")
        return jsonify({
            'error': 'Timeout ao acessar a API do Shopify'
        }), 504

    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Erro de conexão ao acessar a API do Shopify: {str(conn_err)}")
        return jsonify({
            'error': f'Erro de conexão ao acessar a API do Shopify: {str(conn_err)}'
        }), 502

    except requests.exceptions.RequestException as err:
        logger.error(f"Erro ao acessar a API do Shopify: {str(err)}")
        return jsonify({
            'error': f'Erro ao acessar a API do Shopify: {str(err)}'
        }), 502

    except Exception as e:
        logger.error(f"Erro inesperado no proxy: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Erro inesperado no proxy: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
