from lxml import html
import requests
import unicodecsv as csv
import argparse
import json
import roundrobin
from itertools import cycle
import offerCalc as oc
import re

interest_rate = 4.0


def clean(text):
    if text:
        return ' '.join(' '.join(text).split())
    return None


def get_headers():
    # Creating headers.
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'accept-encoding': 'gzip, deflate, sdch, br',
               'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
               'cache-control': 'max-age=0',
               'upgrade-insecure-requests': '1',
               'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'}
    proxies = get_proxies()
    proxy_pool = cycle(proxies)

    # Rotate proxy
    for i in range(1, 11):
        # Get a proxy from the pool
        proxy = next(proxy_pool)
        try:
            headers['http'] = proxy
            headers['https'] = proxy
        except:
            # Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work.
            # We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url
            print("Skipping. Error adding proxy")
    return headers


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = html.fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0],
                              i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def create_url(search_str, page):
    # Creating Zillow URL
    url = "https://www.zillow.com/homes/for_sale/{0}_rb/{1}_p/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy".format(
        search_str, page)
    # print(url)
    return url


def save_to_file(response):
    # saving response to `response.html`

    with open("response.html", 'w', encoding='utf-8') as fp:
        fp.write(response.text)


def write_data_to_csv(data):
    # saving scraped data to csv.

    with open("properties-%s.csv" % (search_str), 'wb') as csvfile:
        fieldnames = ['title', 'home_type', 'home_status', 'year_built', 'address', 'city', 'state', 'postal_code',
                      'facts and features', 'price', 'offer', 'monthly_p_i', 'total_expense', 'rent_zestimate',
                      'days_on_zillow', 'price_reduction', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def get_response(url):

    # Get response from zillow.com.
    for i in range(5):
        response = requests.get(
            url, headers=get_headers())

        if response.status_code != 200:
            # saving response to file for debugging purpose.
            print("error - status code:", response.status_code)
            save_to_file(response)
            continue
        else:
            save_to_file(response)
            return response
    return None


def get_data_from_json(raw_json_data):
    # getting data from json (type 2 of their A/B testing page)
    cleaned_data = None
    properties_list = []
    if clean(raw_json_data) is not None:
        cleaned_data = clean(raw_json_data).replace(
            '<!--', "").replace("-->", "")

        try:
            json_data = json.loads(cleaned_data)
            search_results = json_data.get(
                'searchResults').get('listResults', [])

            for property in search_results:
                address = property.get('addressWithZip')
                property_info = property.get('hdpData', {}).get('homeInfo')
                city = property_info.get('city')
                state = property_info.get('state')
                postal_code = property_info.get('zipcode')
                price = property.get('price')
                bedrooms = property.get('beds')
                bathrooms = property.get('baths')
                area = property.get('area')
                info = f'{bedrooms} bds, {bathrooms} ba ,{area} sqft'
                broker = property.get('brokerName')
                property_url = property.get('detailUrl')
                title = property.get('statusText')
                rent_zestimate = property_info.get('rentZestimate')
                days_on_zillow = property_info.get('daysOnZillow')
                price_reduction = property_info.get('priceReduction')
                year_built = property_info.get('yearBuilt')
                home_type = property_info.get('homeType')
                home_status = property_info.get('homeStatus')

                float_price = 0
                monthly_p_i = 0
                offer = 0
                total_expense = 0

                if price is not None and price != '':
                    float_price = float(re.sub('[^0-9]', '', price[1:]))
                    property_tax = float_price * 0.02
                    monthly_p_i = oc.mortgage_calc(float_price, interest_rate)
                    if rent_zestimate is not None and rent_zestimate != '':
                        float_rent = float(rent_zestimate)
                        offer = oc.offer(home_type, float_price,
                                         interest_rate, float_rent, property_tax)
                        monthly_p_i = oc.mortgage_calc(offer, interest_rate)
                        total_expense = oc.total_expense(
                            home_type, offer, interest_rate, float_rent, property_tax)

                data = {'address': address,
                        'city': city,
                        'state': state,
                        'postal_code': postal_code,
                        'price': float_price,
                        'offer': offer,
                        'monthly_p_i': monthly_p_i,
                        'facts and features': info,
                        'url': property_url,
                        'title': title,
                        'rent_zestimate': rent_zestimate,
                        'days_on_zillow': days_on_zillow,
                        'price_reduction': price_reduction,
                        'year_built': year_built,
                        'home_type': home_type,
                        'home_status': home_status,
                        'total_expense': total_expense}
                if title not in ['New construction', 'Pre-foreclosure / Auction', 'Auction', 'Lot / Land for sale']:
                    properties_list.append(data)
        except ValueError as e:
            print(e)
            return None

    return properties_list


def parse(search_str, page):
    url = create_url(search_str, page)
    response = get_response(url)

    if not response:
        print("Failed to fetch the page, please check `response.html` to see the response received from zillow.com.")
        return None

    parser = html.fromstring(response.text)
    search_results = parser.xpath("//div[@id='search-results']//article")

    if not search_results:
        # print("parsing from json data")
        # identified as type 2 page
        raw_json_data = parser.xpath(
            '//script[@data-zrr-shared-data-key="mobileSearchPageStore"]//text()')
        return get_data_from_json(raw_json_data)

    # print("parsing from html page")
    properties_list = []
    for properties in search_results:
        raw_address = properties.xpath(
            ".//span[@itemprop='address']//span[@itemprop='streetAddress']//text()")
        raw_city = properties.xpath(
            ".//span[@itemprop='address']//span[@itemprop='addressLocality']//text()")
        raw_state = properties.xpath(
            ".//span[@itemprop='address']//span[@itemprop='addressRegion']//text()")
        raw_postal_code = properties.xpath(
            ".//span[@itemprop='address']//span[@itemprop='postalCode']//text()")
        raw_price = properties.xpath(
            ".//span[@class='zsg-photo-card-price']//text()")
        raw_info = properties.xpath(
            ".//span[@class='zsg-photo-card-info']//text()")
        raw_broker_name = properties.xpath(
            ".//span[@class='zsg-photo-card-broker-name']//text()")
        url = properties.xpath(".//a[contains(@class,'overlay-link')]/@href")
        raw_title = properties.xpath(".//h4//text()")

        address = clean(raw_address)
        city = clean(raw_city)
        state = clean(raw_state)
        postal_code = clean(raw_postal_code)
        price = clean(raw_price)
        info = clean(raw_info).replace(u"\xb7", ',')
        broker = clean(raw_broker_name)
        title = clean(raw_title)
        property_url = "https://www.zillow.com" + url[0] if url else None
        is_forsale = properties.xpath('.//span[@class="zsg-icon-for-sale"]')

        properties = {'address': address,
                      'city': city,
                      'state': state,
                      'postal_code': postal_code,
                      'price': price,
                      'facts and features': info,
                      'real estate provider': broker,
                      'url': property_url,
                      'title': title,
                      'rent_zestimate': ''}
        if is_forsale:
            properties_list.append(properties)
    return properties_list


def get_page_cnt(search_str):

    url = create_url(search_str, 1)
    response = get_response(url)
    parser = html.fromstring(response.text)
    pagenation = parser.xpath("//div[@class='search-pagination']//text()")
    return pagenation[len(pagenation) - 2]


if __name__ == "__main__":
    # Reading arguments
    scraped_data = []
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    argparser.add_argument('city', help='')
    argparser.add_argument('state', help='')

    args = argparser.parse_args()
    city = args.city
    state = args.state
    search_str = city + "-" + state

    # Get page count
    pageCnt = int(get_page_cnt(search_str))

    print("Fetching data for %s" % (search_str))

    for page in range(1, pageCnt):
        scraped_temp_data = parse(search_str, page)
        if scraped_temp_data:
            scraped_data = scraped_data + scraped_temp_data
    print("Writing data to output file")
    write_data_to_csv(scraped_data)
