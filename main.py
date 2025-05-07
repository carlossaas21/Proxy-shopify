from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import requests
import os
import logging

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

@app.route('/proxy/customers', methods=['GET', 'OPTIONS'])
@cross_origin()  # Adiciona suporte a CORS na rota
def get_shopify_customers():
    logger.info("Recebida requisição para /proxy/customers")
    logger.info(f"Parâmetros: shop_domain={request.args.get('shop_domain')}, access_token={request.args.get('access_token')}")

    # Obter parâmetros da query string
    shop_domain = request.args.get('shop_domain')
    access_token = request.args.get('access_token')

    # Validar parâmetros
    if not shop_domain or not access_token:
        logger.error("Parâmetros shop_domain e access_token são obrigatórios")
        response = jsonify({
            'error': 'Parâmetros shop_domain e access_token são obrigatórios'
        })
        response.status_code = 400
        response.headers.add('Access-Control-Allow-Origin', 'https://ecomlyze-62237.bubbleapps.io')
        return response

    # Construir a URL da API do Shopify
    api_url = f'https://{shop_domain}/admin/api/2023-04/customers.json'
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }

    try:
        logger.info(f"Fazendo requisição para Shopify: {api_url}")
        # Fazer a requisição para a API do Shopify
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()  # Levanta um erro para códigos de status 4xx/5xx

        logger.info("Requisição ao Shopify bem-sucedida")
        # Retornar os dados dos clientes
        resp = jsonify(response.json())
        resp.status_code = 200
        resp.headers.add('Access-Control-Allow-Origin', 'https://ecomlyze-62237.bubbleapps.io')
        return resp

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Erro HTTP ao acessar a API do Shopify: {str(http_err)}")
        response = jsonify({
            'error': f'Erro HTTP ao acessar a API do Shopify: {str(http_err)}',
            'details': response.text if 'response' in locals() else 'Sem detalhes'
        })
        response.status_code = response.status_code if 'response' in locals() else 500
        response.headers.add('Access-Control-Allow-Origin', 'https://ecomlyze-62237.bubbleapps.io')
        return response

    except requests.exceptions.RequestException as err:
        logger.error(f"Erro ao acessar a API do Shopify: {str(err)}")
        response = jsonify({
            'error': f'Erro ao acessar a API do Shopify: {str(err)}'
        })
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', 'https://ecomlyze-62237.bubbleapps.io')
        return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
