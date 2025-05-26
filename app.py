from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import pdf_processor 
import io

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SCHEMA_FOLDER = os.path.join(BASE_DIR, 'schemas')

ASSETS_FOLDER = os.path.join(BASE_DIR, 'assets')
LOGO_FILE_PATH = os.path.join(ASSETS_FOLDER, 'logo.webp')

pdf_processor.set_pdf_logo_path(LOGO_FILE_PATH)

if not os.path.exists(LOGO_FILE_PATH):
    app.logger.warning(f"LOGO NOT FOUND: Expected at '{LOGO_FILE_PATH}'. PDFs will not have a logo.")
else:
    app.logger.info(f"Logo found at '{LOGO_FILE_PATH}'. Will be used in PDFs.")

SCHEMA_FILES_CONFIG = {
        "media_feed_schema": os.path.join(SCHEMA_FOLDER, "Media Feed Reagent Solution.xml"),
        "fed_batch_schema": os.path.join(SCHEMA_FOLDER, "FedBatch Conditions-DataCollection-CBD-UBD.xml"),
        "pa_feedback_output_schema": os.path.join(SCHEMA_FOLDER, "PA Feedback-Output.xml"),
        "pa_feedback_input_schema": os.path.join(SCHEMA_FOLDER, "PA Feedback-Input.xml"),
        "dbc_schema": os.path.join(SCHEMA_FOLDER, "DBC.xml"),
        "dbd_buffer_prep_schema": os.path.join(SCHEMA_FOLDER, "DBD Buffer Prep.xml"),
        "eluate_frac_pool_prep2_schema": os.path.join(SCHEMA_FOLDER, "Eluate Frac Pool Prep2.xml"),
        "ft_and_ht_schema": os.path.join(SCHEMA_FOLDER, "FT and HT.xml"),
        "output_schema_definition": os.path.join(SCHEMA_FOLDER, "Output.xml"),
        "tff_process_schema": os.path.join(SCHEMA_FOLDER, "TFF Process.xml"),

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
        for name, path_val in SCHEMA_FILES_CONFIG.items(): 
            if not os.path.exists(path_val):
                missing_schemas.append(path_val)
        if missing_schemas:
            app.logger.critical(f"CRITICAL: The following schema files are missing: {', '.join(missing_schemas)}. Application might not function correctly.")

    local_dev_port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=local_dev_port, debug=True)