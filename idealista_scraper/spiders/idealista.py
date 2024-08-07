import scrapy
import json
import re
from fake_useragent import UserAgent
from scrapy.exporters import CsvItemExporter
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()
proxy_url = os.getenv('PROXY_URL')

class MySpider(scrapy.Spider):
    name = 'my_spider'
    rotate_user_agent = True
    
    ua = UserAgent()
    headers = {
        'authority': 'www.idealista.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        "Dnt": "1",
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no cache',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Not?A_Brand";v="8.0.0.0", "Chromium";v="108.0.5359.126", "Google Chrome";v="108.0.5359.126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user_agent': ua.random
    }
    
    custom_settings = {
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'DOWNLOAD_DELAY': 0.1,
        'COOKIES_ENABLED': False
    }
    
    def __init__(self, start_urls, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.start_urls = start_urls
        self.file = open('results.csv', 'wb')
        self.exporter = CsvItemExporter(self.file)
        self.exporter.start_exporting()
        # Crear un archivo temporal al iniciar el scraping
        with open('scraping_status.txt', 'w') as f:
            f.write('Scraping en progreso')
    
    def start_requests_failure(self, failure):
        yield scrapy.Request(
            url=failure.request.url,
            headers=self.headers,
            callback=self.parse,
            errback=self.start_requests_failure,
            meta={'proxy': proxy_url},
            dont_filter=True
        )

    def start_requests(self):
        if hasattr(self, 'start_urls'):
            urls = self.start_urls.split(',')  # Asumiendo que puede haber más de una URL, separadas por comas
            for url in urls:
                yield scrapy.Request(
                    url=url,
                    headers=self.headers,
                    callback=self.parse,
                    errback=self.start_requests_failure,
                    dont_filter=True
                )

    def handle_failure(self, failure):
        yield scrapy.Request(
            url=failure.request.url,
            headers=self.headers,
            callback=self.parse_listing,
            errback=self.handle_failure,
            meta={'proxy': proxy_url},
            dont_filter=True
        )
   
    def handle_failure_PAGE(self, failure):
        yield scrapy.Request(
            url=failure.request.url,
            headers=self.headers,
            callback=self.parse,
            errback=self.handle_failure_PAGE,
            meta={'proxy': proxy_url},
            dont_filter=True
        )

    def parse(self, response):
        card_urls = []

        cards_hightop = response.css('div[class="item   item_contains_branding item_hightop item-multimedia-container"]')
        cards_casual = response.css('div[class="item-info-container "]')
        cards_branding = response.css('div[class="item extended-item item-multimedia-container"]')
        cards_highlight = response.css('div[class="item     item_contains_branding item_featured item_highlight-phrase item_hightop item-multimedia-container"]')
        cards_highlight2 = response.css('div[class="item-info-container "]')  
                                                                                   
        for card in cards_casual:
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())
        for card in cards_hightop:
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())
        for card in cards_branding:
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())
        for card in cards_highlight:
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())
        for card in cards_highlight2:
            href = card.css('div.item-info-container > a::attr(href)').extract_first()
            if href and '/inmueble/' in href:
                card_urls.append(href)
        
        card_urls = [url for url in card_urls if url is not None and url != ""]

        for card_url in card_urls:
            yield scrapy.Request(
                url='https://www.idealista.com' + card_url,
                headers=self.headers,
                callback=self.parse_listing,
                errback=self.handle_failure,
                meta={'proxy': proxy_url},
                dont_filter=True
            )        
        
        next_page = response.css('.icon-arrow-right-after::attr(href)').get()
        
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(
                next_page,  
                headers=self.headers,
                meta={'proxy': proxy_url},
                errback=self.handle_failure_PAGE,
                callback=self.parse
            )
    
    def parse_listing(self, response):

        print("URL visitada:", response.url)
        if response is None:
            print('\r\n' + 'SIN RESPUESTA' + '\r\n')
        else: 
            features = {
                'id': response.url.split('/')[-2],
                'url': response.url,
                'title': response.css('span[class="main-info__title-main"]::text').get().strip().split(" ")[0],
                'price €': float(response.css('span[class="info-data-price"] *::text').get().replace(',', '').split(" ")[0]),
                '€/m²': float(response.css('p.squaredmeterprice span:contains("€/m²")::text').extract_first().replace(',', '').split(" ")[0]),
                'price_before': '',
                'pricedown_%': '',
                'rooms': '',
                'm² building': '',
                'm² land': '',
                'baths': '',
                'floor': '',
                'elevator': '',
                'status': '',
                'heater': '',
                'closet': '',
                'storage': '',
                'year': '',
                'oriented': '',
                'last_updated': '',
                'full_description': list(filter(None, [
                    text.get().strip().replace("* ", '') for text in
                    response.css('div[class="adCommentsLanguage expandable is-expandable"] *::text')
                ])),
                'pool': '',
                'garden': '',
                'cool air': '',
                'green areas': '',
                'longitude': '',
                'latitude': ''
            }

            rooms_text = response.css('div.info-features span:contains("bed.")::text').extract_first()
            if rooms_text:
                features['rooms'] = float(rooms_text.strip().split(" ")[0])

            sqm_text = response.css('div.info-features span:contains("m²")::text').extract_first()
            if sqm_text:
                sqm_text_cleaned = sqm_text.replace(',', '').strip()
                features['m² building'] = float(sqm_text_cleaned.split(" ")[0])

            try:
                land_text = response.css('div.details-property_features li:contains("Land plot of")::text').get()
                land_size = re.search(r'\d+(,\d+)?', land_text).group(0)
                land_size = float(land_size.replace(',', ''))
                features['m² land'] = land_size
            except:
                features['m² land'] = None
                pass

            baños_text = response.css('div.details-property_features li::text').re_first(r'(\d+)\s*(bathroom|bathrooms)')
            try:
                features['baths'] = float(baños_text)
            except:
                features['baths'] = None
                pass

            try:
                features['floor'] = response.css('div.info-features span:contains("floor") span::text').extract_first()
            except:
                features['floor'] = None
                pass

            try:
                features['elevator'] = response.css('div.info-features span:contains("Elevator") span::text').extract_first()
            except:
                features['elevator'] = None
                pass

            try:
                features['status'] = response.css('div.details-property_features li:contains("Status")::text').extract_first()
            except:
                features['status'] = None
                pass

            try:
                features['heater'] = response.css('div.details-property_features li:contains("Heating")::text').extract_first()
            except:
                features['heater'] = None
                pass

            try:
                features['closet'] = response.css('div.details-property_features li:contains("Built-in wardrobes")::text').extract_first()
            except:
                features['closet'] = None
                pass

            try:
                features['storage'] = response.css('div.details-property_features li:contains("Storage room")::text').extract_first()
            except:
                features['storage'] = None
                pass

            try:
                year_text = response.css('div.details-property_features li:contains("Year built")::text').extract_first()
                features['year'] = float(year_text.split(" ")[0])
            except:
                features['year'] = None
                pass

            try:
                features['oriented'] = response.css('div.details-property_features li:contains("Orientation")::text').extract_first()
            except:
                features['oriented'] = None
                pass

            try:
                features['last_updated'] = response.css('div.details-property_features li:contains("Last updated")::text').extract_first()
            except:
                features['last_updated'] = None
                pass

            try:
                features['pool'] = response.css('div.details-property_features li:contains("Swimming pool")::text').extract_first()
            except:
                features['pool'] = None
                pass

            try:
                features['garden'] = response.css('div.details-property_features li:contains("Garden")::text').extract_first()
            except:
                features['garden'] = None
                pass

            try:
                features['cool air'] = response.css('div.details-property_features li:contains("Air conditioning")::text').extract_first()
            except:
                features['cool air'] = None
                pass

            try:
                features['green areas'] = response.css('div.details-property_features li:contains("Green areas")::text').extract_first()
            except:
                features['green areas'] = None
                pass

            try:
                script = response.css('script:contains("window._initialProps")::text').get()
                match = re.search(r'(?<=geoPoint":{"lat":)(.*?)(?=,"lng")', script)
                lat = float(match.group(0))
                features['latitude'] = lat
            except:
                features['latitude'] = None
                pass

            try:
                script = response.css('script:contains("window._initialProps")::text').get()
                match = re.search(r'(?<=,"lng":)(.*?)(?=})', script)
                lng = float(match.group(0))
                features['longitude'] = lng
            except:
                features['longitude'] = None
                pass

            try:
                price_before = response.css('div.info-features span:contains("Price drop")::text').extract_first()
                features['price_before'] = float(price_before.strip().split(" ")[0])
            except:
                features['price_before'] = None
                pass

            try:
                pricedown_text = response.css('div.info-features span:contains("%")::text').extract_first()
                features['pricedown_%'] = float(pricedown_text.strip().split("%")[0])
            except:
                features['pricedown_%'] = None
                pass

            self.exporter.export_item(features)

    def close(self, reason):
        self.exporter.finish_exporting()
        self.file.close()
        # Eliminar el archivo de estado al finalizar
        if os.path.exists('scraping_status.txt'):
            os.remove('scraping_status.txt')
