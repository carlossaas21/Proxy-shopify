from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

@app.route('/proxy/customers', methods=['GET'])
def get_shopify_customers():
    # Obter parâmetros da query string
    shop_domain = request.args.get('shop_domain')
    access_token = request.args.get('access_token')

    # Validar parâmetros
    if not shop_domain or not access_token:
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
        # Fazer a requisição para a API do Shopify
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()  # Levanta um erro para códigos de status 4xx/5xx

        # Retornar os dados dos clientes
        return jsonify(response.json()), 200

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            'error': f'Erro HTTP ao acessar a API do Shopify: {str(http_err)}',
            'details': response.text if 'response' in locals() else 'Sem detalhes'
        }), response.status_code if 'response' in locals() else 500

    except requests.exceptions.RequestException as err:
        return jsonify({
            'error': f'Erro ao acessar a API do Shopify: {str(err)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
