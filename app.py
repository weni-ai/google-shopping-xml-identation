from flask import Flask, request, Response
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import pandas as pd
import json
import multiprocessing as mp
import numpy as np

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

        item_data = []

        for item in root.findall('.//item'):
          item_id_product = item.find('id_product').text.strip()
          item_product_type = item.find('g:product_type', namespaces={'g': 'http://base.google.com/ns/1.0'}).text.strip()
          item_data.append({'id_product': item_id_product, 'product_type': item_product_type})

        df = pd.DataFrame(item_data)
        df['product_type'] = df['product_type'].str.split('> ', n=1).str[0]
        filtered_df = df.loc[df['product_type'].str.contains('Hortifruti|Carnes e Aves|Frios e Laticínios|Padaria')]
        filtered_df['unit_value'] = np.nan
        filtered_df['weight'] = np.nan

        # Divide o DataFrame em partes iguais para processamento paralelo
        num_cores = mp.cpu_count()
        df_parts = np.array_split(filtered_df, num_cores)

        # Cria um pool de processos com o número de núcleos disponíveis
        pool = mp.Pool(num_cores)

        # Aplica a função de processamento paralelo em cada parte do DataFrame
        processed_parts = pool.map(process_part, df_parts)

        # Combina as partes processadas em um único DataFrame
        processed_df = pd.concat(processed_parts)
        # Encerra o pool de processos
        pool.close()
        pool.join()
        # Atualiza o DataFrame original com os valores processados
        filtered_df['unit_value'] = processed_df['unit_value']
        # Atualiza o DataFrame original com os valores processados
        filtered_df['weight'] = processed_df['weight']


        items = root.findall('.//item', namespaces={'g': 'http://base.google.com/ns/1.0'})
        for item in items:
            product_id = item.find('id_product').text.strip()
            matching_row = filtered_df.loc[filtered_df['id_product'] == product_id]
            if matching_row.empty:
                continue
            unit_value = matching_row['unit_value'].values[0]
            weight = matching_row['weight'].values[0]

            if unit_value == None:
                continue
            price_element = item.find('.//g:price', namespaces={'g': 'http://base.google.com/ns/1.0'})
            original_price = item.find('.//g:original_price', namespaces={'g': 'http://base.google.com/ns/1.0'})
            nome_element = item.find('.//product_name')
            description = item.find('.//description')
            if price_element is not None:
                price_element.text = str(unit_value)
                original_price.text = str(unit_value)
                nome_element.text = (nome_element.text + ' Unidades')
                if weight == None:
                  continue
                weight = str(weight)
                description.text = (description.text + ' Aprox. ' + weight)

                            

        xml_atualizado = ET.tostring(root, encoding='utf-8')

        # Parse string and indent
        dom = minidom.parseString(xml_atualizado)
        xml_string = dom.toprettyxml(indent="  ")

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
            weight = sku['measures']['weight']
            if unit_multiplier == 1.0:
                return None, None  # Retorna None se o unit_multiplier for 1.0
            best_price = float(best_price_formatted.replace('R$', '').replace(',', '.'))
            sku['bestPriceFormated'] = f'R$ {round(best_price * unit_multiplier, 2)}'
            weight = float(weight)
            sku['measures']['weight'] = f'{round(weight * unit_multiplier)}g'
            return sku['bestPriceFormated'], sku['measures']['weight']

    except (requests.exceptions.RequestException, ValueError, KeyError):
        return None, None  # Retorna None em caso de erro

def process_part(df_part):
    df_part[['unit_value', 'weight']] = df_part.apply(lambda row: pd.Series(valor_unidade(row['id_product'])), axis=1)
    return df_part

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)