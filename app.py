from flask import Flask, request, render_template, send_file, jsonify
import subprocess
import os
import signal

app = Flask(__name__)
process = None  # Variable global para manejar el proceso de scraping

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_scrape():
    url = request.json.get("url")
    if url:
        global process
        try:
            # Eliminar el archivo de resultados existente si existe
            if os.path.exists('results.csv'):
                os.remove('results.csv')
            
            command = [
                'scrapy', 'crawl', 'my_spider',
                '-a', f'start_urls={url}',
                '-o', 'results.csv',
                '-t', 'csv'
            ]
            # Crear el archivo de estado
            with open('scraping_status.txt', 'w') as f:
                f.write('scraping')
            # Ejecuta el scraper en segundo plano para no bloquear la interfaz de usuario
            process = subprocess.Popen(command)
            return jsonify({"message": "Scraping iniciado, por favor espere...", "status": "scraping"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "URL no proporcionada"}), 400

@app.route("/status", methods=["GET"])
def status():
    if os.path.exists('scraping_status.txt'):
        with open('scraping_status.txt', 'r') as f:
            status = f.read()
        return jsonify({"status": status})
    return jsonify({"status": "no_scraping"})

@app.route("/stop", methods=["GET"])
def stop_scrape():
    global process
    if process:
        try:
            process.send_signal(signal.SIGINT)  # Enviar señal para terminar el proceso de Scrapy
            process.wait()  # Esperar a que el proceso termine
            process = None
        finally:
            # Actualizar el archivo de estado
            with open('scraping_status.txt', 'w') as f:
                f.write('finished')
        return jsonify({"message": "Scraping detenido. Puede descargar el archivo.", "status": "finished"})
    return jsonify({"error": "No hay un proceso de scraping en ejecución"}), 404

@app.route("/download")
def download():
    if os.path.exists("results.csv"):
        return send_file("results.csv", as_attachment=True)
    else:
        return "No hay resultados disponibles para descargar", 404

if __name__ == "__main__":
    app.run(debug=True)
