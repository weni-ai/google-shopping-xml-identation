from flask import Flask, request, Response
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

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

        # Create an indented XML string using minidom
        xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

        # Encode the XML string as UTF-8
        encoded_xml = xml_string.encode('utf-8')

        return Response(encoded_xml, content_type='application/xml; charset=utf-8')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
