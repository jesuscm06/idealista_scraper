import requests
import urllib3

# Deshabilitar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Proxy URL según la documentación de BrightData
proxy_url = "http://brd-customer-hl_cd81b832-zone-residential-country-es:h2hoeouh5du8@brd.superproxy.io:22225"

# URL a probar
test_url = "https://www.idealista.com/en/venta-viviendas/campo-huesca/"

# Configuración del proxy
proxies = {
    "http": proxy_url,
    "https": proxy_url,
}

# Agregar encabezados adicionales
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

# Crear una sesión para manejar cookies
session = requests.Session()

# Realizar la solicitud
try:
    response = session.get(test_url, proxies=proxies, headers=headers, verify=False)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Content: {response.text[:500]}")  # Mostrar solo los primeros 500 caracteres del contenido
    
    # Guardar el contenido de la respuesta en un archivo
    with open('response.html', 'w') as file:
        file.write(response.text)
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
