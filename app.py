from flask import Flask, request, Response
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import pandas as pd
import json

app = Flask(__name__)

@app.route('/get_indented_xml', methods=['GET'])
def get_indented_xml():
    # Get the XML URL from the query parameter
    xml_url = request.args.get('xml_url')

    if not xml_url:
        return "XML URL is missing in the query parameter", 400

    try:
        # Fetch the XML content from the provided URL
        response = requests.get(xml_url)

        if response.status_code != 200:
            return f"Failed to fetch XML from URL: {xml_url}", 500

        # Parse the XML content using ElementTree
        root = ET.fromstring(response.content)
        root = get_value_unit(root)

        # Create an indented XML string using minidom
        xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

        # Encode the XML string as UTF-8
        encoded_xml = xml_string.encode('utf-8')

        return Response(encoded_xml, content_type='application/xml; charset=utf-8')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

def valor_unidade(id):
    url = f'https://prezunic.myvtex.com/api/catalog_system/pub/products/variations/{id}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.content
        data = json.loads(result)
        skus = data['skus']
        for sku in skus:
            id = str(data['productId'])
            best_price_formatted = sku['bestPriceFormated']
            unit_multiplier = sku['unitMultiplier']
            if(unit_multiplier == 1.0):
              continue
            best_price = float(best_price_formatted.replace('R$', '').replace(',', '.'))
            sku['bestPriceFormated'] = f'R$ {round(best_price * unit_multiplier)}'

        return sku['bestPriceFormated']

    except (requests.exceptions.RequestException, ValueError, KeyError):
        return -1

def get_value_unit(root):
    item_data = []

    for item in root.findall('.//item'):
        item_id_product = item.find('id_product').text.strip()
        item_product_type = item.find('g:product_type', namespaces={'g': 'http://base.google.com/ns/1.0'}).text.strip()
        item_data.append({'id_product': item_id_product, 'product_type': item_product_type})

    df = pd.DataFrame(item_data)
    df['product_type'] = df['product_type'].str.split('> ', n=1).str[0]

    filtered_df = df.loc[df['product_type'].str.contains('Hortifrute|Carnes e Aves')]
    filtered_df['unit_value'] = filtered_df['id_product'].apply(valor_unidade)

    for element in root.findall('.//item'):
        product_id = element.find('id_product').text.strip()
        matching_row = filtered_df.loc[filtered_df['id_product'] == product_id]
        if matching_row.empty:
            continue  
        unit_value = matching_row['unit_value'].values[0]
        if unit_value == -1:
            continue
        element.find('g:product_type', namespaces={'g': 'http://base.google.com/ns/1.0'}).text = str(unit_value)
    return(root)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
