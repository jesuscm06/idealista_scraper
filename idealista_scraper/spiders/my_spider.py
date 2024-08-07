import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
from scrapy.exporters import JsonItemExporter
import json
import datetime
import six
import urllib.request
import random
import requests
from fake_useragent import UserAgent
import re


class Scraper(scrapy.Spider):
    

    name = 'Scraper'
    rotate_user_agent = True
    
    ua = UserAgent()
    headers={
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
        'user_agent': '"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36"'
    }       
    headers = {'user_agent': ua.random}
    #custom settings
    custom_settings={
        'CONCURRENT_REQUESTS_PER_DOMAIN':10,
        'DOWNLOAD_DELAY':0.1,
        'COOKIES_ENABLED' : False
    }
    
    #postcodes list
    postcodes=[]

    failed_url = None

    def __init__(self, start_urls, *args, **kwargs):
        super(Scraper, self).__init__(*args, **kwargs)
        self.start_urls = start_urls
               
     

    def start_requests_failure(self, failure):
       
        # vuelve a hacer el request con la nueva IP del proxy  
        yield scrapy.Request(
                            url=failure.request.url,
                            headers=self.headers,
                            callback=self.parse,
                            errback=self.start_requests_failure,
                            meta={'proxy': 'http://brd-customer-hl_cd81b832-zone-zone1:gzrvo1m3481c@zproxy.lum-superproxy.io:22225'},
                            dont_filter = True)

    def start_requests(self):

        for url in self.start_urls:
            yield scrapy.Request(url=url,
                            headers=self.headers,
                            callback=self.parse,
                            errback=self.start_requests_failure,
                            # meta={'proxy': 'http://brd-customer-hl_cd81b832-zone-zone1:gzrvo1m3481c@zproxy.lum-superproxy.io:22225'},
                            dont_filter = True)

    def handle_failure(self, failure):

        # vuelve a hacer el request con la nueva IP del proxy  
        yield scrapy.Request(
                            url=failure.request.url,
                            headers=self.headers,
                            callback=self.parse_listing,
                            errback=self.handle_failure,
                            meta={'proxy': 'http://brd-customer-hl_cd81b832-zone-zone1:xaztey3u2pi9@zproxy.lum-superproxy.io:22225'},
                            dont_filter=True)
   
    def handle_failure_PAGE(self, failure):

        yield scrapy.Request(
                            url=failure.request.url,
                            headers=self.headers,
                            callback=self.parse,
                            errback=self.handle_failure_PAGE,
                            meta={'proxy': 'http://brd-customer-hl_cd81b832-zone-zone1-country-es:gzrvo1m3481c@zproxy.lum-superproxy.io:22225'},
                            dont_filter=True
                            )       

    def parse(self, response):

        # print('\r\n' + "URL: " + response.request.url + '\r\n' + '\r\n')
        

        # Cards URLS
        card_urls=[]
        

        # extracting hightop cards
        cards_hightop = response.css('div[class="item   item_contains_branding item_hightop item-multimedia-container"]')
        cards_casual = response.css('div[class="item-info-container "]')
        cards_branding = response.css('div[class="item extended-item item-multimedia-container"]')

        cards_highlight = response.css('div[class="item     item_contains_branding item_featured item_highlight-phrase item_hightop item-multimedia-container"]')
        cards_highlight2 = response.css('div[class="item-info-container "]')  
                                                                                   
        # extracting casual cards URLs
        for card in cards_casual:
        
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())
            
        # extracting hightop cards URLs
        for card in cards_hightop:
        
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())

        # extracting brading cards URLs
        for card in cards_branding:
        
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())
        # extracting higlighted cards URLs
        for card in cards_highlight:
        
            card_urls.append(card.css('a[class="item-link"]::attr(href)').get())
        
        # extracting higlighted cards URLs
        for card in cards_highlight2:
            href = card.css('div.item-info-container > a::attr(href)').extract_first()
            if href and '/inmueble/' in href:
                
                # Aquí es donde puedes agregar el enlace a tu lista card_urls
                card_urls.append(href)
        
        # Filtrar la lista card_urls para eliminar None y cadenas vacías
        card_urls = [url for url in card_urls if url is not None and url != ""]
        
        # loop over property card URLs
        proxy='http://brd-customer-hl_cd81b832-zone-zone1-country-es:xaztey3u2pi9@zproxy.lum-superproxy.io:22225'

        for card_url in card_urls:
            # crawl property listing

            yield scrapy.Request(

                url='https://www.idealista.com' + card_url,
                headers=self.headers,
                callback=self.parse_listing,
                errback=self.handle_failure,
                meta={'proxy': proxy},
                dont_filter = True
                             
            )        
        
        # That for extracting from Main Page without go into asset details
        '''
        # data extraction   
        for quote in response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "item", " " ))] | //*[contains(concat( " ", @class, " " ), concat( " ", "item_fade", " " ))] | //*[contains(concat( " ", @class, " " ), concat(" ", "item-multimedia-container", " " ))]').getall():
            info_items = scrapy.Selector(text=quote).xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "item-detail", " " ))]').getall()
        
            for item in info_items:
                if scrapy.Selector(text=item).css('small::text').get() == 'm²':
                    surface = scrapy.Selector(text=item).css('span::text').get()
            
            yield {
                'id': scrapy.Selector(text=quote).xpath('//article/@data-adid').get(),
                'title': scrapy.Selector(text=quote).css('.item-link::text').get(),
                'price': scrapy.Selector(text=quote).css('.h2-simulated::text').get(),
                'surface': scrapy.Selector(text=quote).css('span::text').get()
            }
        '''
        # next page    
        next_page = response.css('.icon-arrow-right-after::attr(href)').get()
        
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page,  
                                headers=self.headers,
                                meta={'proxy': 'http://brd-customer-hl_cd81b832-zone-zone1-country-es:xaztey3u2pi9@zproxy.lum-superproxy.io:22225'},
                                errback=self.handle_failure_PAGE ,
                                callback=self.parse)
    
               
    # crawling URLs of assets
    def parse_listing(self, response):

        
        if response is None:
            print('\r\n' + 'SIN RESPUESTA' + '\r\n')

        else: 
            # extraction logic
            features={
                'id': response.url.split('/')[-2],
                'url':response.url,
                'title': response.css('span[class="main-info__title-main"]::text').get().strip().split(" ")[0],
                #'address': response.css('span[class="main-info__title-minor"]::text').get(),
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
                'status' : '' , 
                'heater': '',
                'closet': '',
                'storage': '',
                'year': '',
                'oriented': '',
                
                
                #'details': '',
                
                #'price-detail': list(filter(None, [
                #                    text.get().strip()
                #                    for text in 
                #                    response.css('section[class="price-features__container"] *::text')])),
                
                'last_updated':     '',            
                #'floor_area': '',
                'full_description': list(filter(None, [
                                    text.get().strip().replace("* ",'')
                                    for text in
                                   response.css('div[class="adCommentsLanguage expandable is-expandable"] *::text')
                ])),
                #'agent_name': list(filter(None, [
                #                   text.get().strip()
                #                   for text in 
                #                   response.css('div[class="professional-name"]').css('span::text')])),
                # 'agent_link': 'https://www.idealista.com' + str(response.css('a[class="about-advertiser-name"]::attr(href)').get()),
                #'agent_phone': response.css('span[class="phone-btn-number"]::text').get(),
                #'particulas_phone': response.css('span[class="hidden-contact-phones_text"]::text').get(),

                #'image_urls':[],
                #'key_features': [
                #                    text.strip()
                #                   for text in
                #                   Selector(text=response.css('div[class="details-property_features"]').get()).css('li::text').getall()],
                #'building-fabric': '',
                'pool': '',
                'garden': '',
                'cool air': '',
                'green areas': '',
                #'location': [
                #                  text.get().strip().replace("´",'')
                #                   for text in 
                #                   response.css('div[id="headerMap"]').css('li::text')
                #],
                'longitude': '',
                'latitude': ''
            }
            # Extraer el número de habitaciones
            rooms_text = response.css('div.info-features span:contains("bed.")::text').extract_first()
            if rooms_text:
                features['rooms'] = float(rooms_text.strip().split(" ")[0])
                # print("Número de habitaciones:", features['rooms'])
            else:
                raise ValueError("No se encontró información de habitaciones.")
            # m²
            # Extraer los metros cuadrados
            
            try:
                # Extraer los metros cuadrados
                sqm_text = response.css('div.info-features span:contains("m²")::text').extract_first()
                if sqm_text:
                    # Eliminar puntos y convertir a float
                    sqm_text_cleaned = sqm_text.replace(',', '').strip()
                    features['m² building'] = float(sqm_text_cleaned.split(" ")[0])
                    # print("Metros cuadrados:", features['m² building'])
                else:
                    raise ValueError("No se encontró información de metros cuadrados.")
            except:
                    features['m² building'] = None
                

            # land m2
            try:
                land_text = response.css('div.details-property_features li:contains("Land plot of")::text').get()
                land_size = re.search(r'\d+(,\d+)?', land_text).group(0)
                land_size = float(land_size.replace(',',''))
                features['m² land'] = land_size
            except:
                features['m² land'] = None
                pass
            # baths
            baños_text = response.css('div.details-property_features li::text').re_first(r'(\d+)\s*(bathroom|bathrooms)')
            try:
                features['baths'] = baños_text
                features['baths'] = float(features['baths'])
            except:
                features['baths'] = None
                pass

             # Floor
            try:
                features['floor'] = response.css('div.info-features span:contains("floor") span::text').extract_first()
            except:
                features['floor'] = None
                pass
            # elevator
            try:
                features['elevator'] = response.css('div.details-property_features li:contains("lift")::text').extract_first()
            except:
                features['elevator'] = None
                pass
            # status
            try:
                features['status'] = response.css('div.details-property_features li:contains("condition"),li:contains("hand"),li:contains("renovating")::text').extract_first().replace("</li>", "").replace("<li>", "")
            except:
                features['status'] = None
                pass
            # heater
            try:
                features['heater'] = response.css('div.details-property_features li:contains("heating"),li:contains("heating")::text').extract_first().replace("</li>", "").replace("<li>", "")
            except:
                features['heater'] = None
                pass
            # Closet
            try:
                features['closet'] = response.css('div.details-property_features li:contains("wardrobes")::text').extract_first().replace("</li>", "").replace("<li>", "")
            except:
                features['closet'] = None
                pass
            # Storage
            try:
                features['storage'] = response.css('div.details-property_features li:contains("Storeroom")::text').extract_first().replace("</li>", "").replace("<li>", "")
            except:
                features['storage'] = None
                pass
            # oriented
            try:
                features['oriented'] = response.css('div.details-property_features li:contains("Orientation")::text').extract_first().replace("</li>", "").replace("<li>", "")
            except:
                features['oriented'] = None
                pass
            # Year
            try:
                year = response.css('div.details-property_features li:contains("Built")::text').extract_first()
                if year:
                    features['year'] = re.search(r'\d+', year).group(0)
                else:
                    features['year'] = None
            except:
                pass

            # pricedown
            try:
                features['price_before'] = float(response.css('span[class="pricedown_price"] *::text').get().replace(',', '').strip().split(" ")[0])
            except:
                features['price_before'] = None
                pass
            
            try:
                features['pricedown_%'] = float(response.css('span[class="pricedown_icon icon-pricedown"] *::text').get().strip().replace("%", ""))/100
            except:
                features['pricedown_%']= None
                pass
            '''        
            # Details
            try:
                features['details'] = list(filter(None, [
                                    text.strip()
                                    for text in
                                    response.css('div[class="info-features"]').css('span::text').getall()])),
            except:
                pass
            
            # extract building fabric
            try:
                features['building-fabric']=[
                    text.strip()
                    for text in
                    Selector(text=response.css('div[class="details-property_features"]').getall()[1]).css('li::text').getall()]
            except:
                pass
            '''
            # extract last updated
            try:
                features['last_updated']=[
                        ''.join(list(filter(None,[
                            text.get().strip()
                            for text in 
                            response.css('div[id="stats"] *::text')
                            ]))[1:-1])]
                
            except:
                pass
            
            # extract equipment
            try:
                features['pool'] = response.css('div.details-property_features li:contains("pool")::text').extract_first().replace("</li>", "").replace("<li>", "").strip()
            except:
                features['pool'] = None
                pass
            try:
                features['garden'] = response.css('div.details-property_features li:contains("Garden")::text').extract_first().replace("</li>", "").replace("<li>", "").strip()
            except:
                features['garden'] = None
                pass
            try:
                features['cool air'] = response.css('div.details-property_features li:contains("Air conditioning")::text').extract_first().replace("</li>", "").replace("<li>", "").strip()
            except:
                features['cool air']= None
                pass
            
            try:
                features['green areas'] = response.css('div.details-property_features li:contains("Green areas")::text').extract_first().replace("</li>", "").replace("<li>", "").strip()
            except:
                features['green areas']= None
                pass
            '''    
            # extract floor area
            try:
                features['floor_area'] = ''.join(list(filter(None, [
                                            text.get().strip()
                                            for text in
                                            Selector(text=response.css('div[class="info-features"]').css('span').getall()[0]).css(' *::text')
                    ])))
            except:
                pass
            '''
            # extract script containing json data
            try:
                script = ''.join([
                    text.get() 
                    for text in 
                    response.css('script::text')
                    if 'var config =' in text.get()
                ])
            except:
                pass
            '''
            # extract image URLs
            try:
                features['image_urls'] = [
                    image.split(',')[0]
                    for image in
                    script.split('imageDataService:"')
                ][1:]
            except:
                pass
            '''
            # extract coordinates
            try:
                features['latitude'] = float(script.split("latitude: '")[1].split("'")[0].split(" ")[0])     
                
            except:
                pass
            
            try:
                features['longitude'] = float(script.split("longitude: '")[1].split("'")[0].split(" ")[0])
            except:
                pass
            
            yield features

    def close(self, reason):
        with open('output.json', 'w') as f:
            exporter = JsonItemExporter(f)
            exporter.start_exporting()
            for item in self.items:
                exporter.export_item(item)
            exporter.finish_exporting()