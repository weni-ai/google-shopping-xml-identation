from flask import Flask, request, Response
import requests
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

        # Parse the XML content
        parsed_xml = minidom.parseString(response.text)

        # Generate indented XML as a string
        indented_xml = parsed_xml.toprettyxml(indent="  ")

        return Response(indented_xml, content_type='application/xml')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
