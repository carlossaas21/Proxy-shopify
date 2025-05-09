from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging
import certifi
from typing import Dict, Any, List, Optional

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

def format_customer_data(customer: Dict[str, Any]) -> Dict[str, str]:
    """
    Formata os dados do cliente com as informações solicitadas.
    
    Args:
        customer (Dict[str, Any]): Dicionário com os dados do cliente do Shopify
        
    Returns:
        Dict[str, str]: Dicionário formatado com os campos:
            - Nome (str): Nome do cliente ("Sem informação" se não existir)
            - sobrenome (str): Sobrenome do cliente ("Sem informação" se não existir)
            - phone (str): Número de telefone ("Sem informação" se não existir)
    """
    # Função auxiliar para tratar valores vazios ou None
    def format_value(value: Any) -> str:
        if value is None or value == "" or value == "None":
            return "Sem informação"
        return str(value).strip()

    customer_data: Dict[str, str] = {
        'Nome': format_value(customer.get('first_name')),
        'sobrenome': format_value(customer.get('last_name')),
        'phone': format_value(customer.get('phone'))
    }
        
    return customer_data

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
        formatted_customers = [format_customer_data(customer) for customer in customers_data]

        logger.info("Requisição ao Shopify bem-sucedida")
        return jsonify(formatted_customers), 200

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
