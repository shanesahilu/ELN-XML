# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by ReportLab or other libraries
# libffi-dev is for cffi (a potential sub-dependency)
# build-essential provides tools for compiling if any pip packages need it
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend application code,
# including app.py, pdf_processor.py, and the 'schemas' directory
COPY . .

# The 'schemas' directory will be copied by "COPY . ." if it exists in your backend folder.
# No need to explicitly mkdir for 'uploads' or 'generated_pdfs' as they are not used on disk.
# If your 'schemas' directory needs specific permissions (though usually not for read-only access by the app),
# you could add a chown for it, but often it's not necessary on Render.

# Expose the port Gunicorn will run on.
# Render provides the $PORT environment variable, which Gunicorn will use.
# This EXPOSE line is good practice for documentation.
EXPOSE 10000

# Command to run the application using Gunicorn.
# Gunicorn binds to all network interfaces (0.0.0.0)
# and uses the port specified by Render's $PORT environment variable.
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]