from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os

import pdf_processor 
import io 

app = Flask(__name__)
CORS(app) 

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SCHEMA_FOLDER = os.path.join(BASE_DIR, 'schemas') 

SCHEMA_FILES_CONFIG = {
    "media_feed_schema": os.path.join(SCHEMA_FOLDER, "Media Feed Reagent Solution.xml"),
    "fed_batch_schema": os.path.join(SCHEMA_FOLDER, "FedBatch Conditions-DataCollection-CBD-UBD.xml"),
    "vessel_master_schema": os.path.join(SCHEMA_FOLDER, "Vessel-BatchVolume Master.xml"),
    "sample_prep_schema": os.path.join(SCHEMA_FOLDER, "Sample Preparation.xml"),
    "seed_train_schema": os.path.join(SCHEMA_FOLDER, "Seed Train-CBD-UBD.xml")
}

@app.route('/convert', methods=['POST'])
def convert_xml_to_pdf():
    if 'xmlFile' not in request.files:
        app.logger.error("No XML file part in request.")
        return jsonify({"error": "No XML file part"}), 400

    file = request.files['xmlFile']
    if file.filename == '':
        app.logger.error("No selected XML file.")
        return jsonify({"error": "No selected XML file"}), 400

    if file and file.filename.endswith('.xml'):
        try:
            xml_content_bytes = file.read() 
            xml_content_string = xml_content_bytes.decode('utf-8') 
            app.logger.info(f"Received XML file: {file.filename}, size: {len(xml_content_bytes)} bytes")

            pdf_bytes = pdf_processor.process_xml_to_pdf(xml_content_string, SCHEMA_FILES_CONFIG)

            if pdf_bytes:
                app.logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes.")

                pdf_buffer = io.BytesIO(pdf_bytes)
                pdf_buffer.seek(0) 

                response = send_file(
                    pdf_buffer,
                    as_attachment=True,
                    download_name='converted_eln_report.pdf', 
                    mimetype='application/pdf'
                )
                app.logger.info("PDF file sent to client.")
                return response
            else:
                app.logger.error("PDF generation returned None (failed).")
                return jsonify({"error": "Failed to generate PDF from XML. Check server logs for details."}), 500

        except Exception as e:
            app.logger.error(f"An error occurred during conversion: {e}", exc_info=True) 

            return jsonify({"error": f"An internal server error occurred. Please check server logs."}), 500

    else:
        app.logger.warning(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload an XML file."}), 400

if __name__ == '__main__':

    if not os.path.isdir(SCHEMA_FOLDER):
        app.logger.critical(f"CRITICAL: SCHEMA_FOLDER '{SCHEMA_FOLDER}' does not exist. Schemas cannot be loaded.")

    else:
        missing_schemas = []
        for name, path in SCHEMA_FILES_CONFIG.items():
            if not os.path.exists(path):
                missing_schemas.append(path)
        if missing_schemas:
            app.logger.critical(f"CRITICAL: The following schema files are missing: {', '.join(missing_schemas)}. The application might not function correctly.")

    app.run(host='0.0.0.0', port=5000, debug=True) 