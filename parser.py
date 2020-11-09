import requests
from bs4 import BeautifulSoup
import lxml
from datetime import datetime
import csv
from os import startfile
import re
# from multiprocessing import Pool

'''
Данный парсер учитывает следующие особенности сайта:
1. На основной странице располагаются все ссылки на подкатегории, которые сразу ведут на список товаров c пагинацией
2. Пагинация обозначается последней цифрой в http-строке браузера с приставкой PAGINATION_WORD
3. Пагинация включает в себя ссылку в форме числа на последнюю страницу списка, например (1, 2 ... 20)
'''

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36', 'accept': '*/*'}
URL = 'https://borisov-praktik.by/catalog/'  # URL, с которого будет начинаться парсинг
HOST_URL = 'https://borisov-praktik.by'  # URL, который прикрепляется для относительных ссылок
PAGINATION_WORD = '?PAGEN_1='  # Как обозначается пагинация на данном сайте
FILE_NAME = 'parser_borisov_praktik.csv'  # Наименование файла для записи в файл
# pool_process = 20
catalogs_list = []  # Список со всеми URL на каталоги
pages_list = []  # Список со всеми URL на каталогов с пагинацией, которые ведут на товары
goods_list = []  # Список о всеми URL товаров


def get_html(url):
    r = requests.get(url, headers=HEADERS)
    return r.text


def get_main_content(html):  # Ф-ция отвечает за то, чтобы получить ссылки на товары по каталогам и добавить их в список
    soup = BeautifulSoup(html, 'html.parser')
    print('Получен html-код основной страницы')
    catalogs = soup.find('div', class_='catalog_section_list row items flexbox').find_all('li', class_='sect')
    for catalog in catalogs:
        catalogs_list.append(HOST_URL + catalog.find('a', class_='dark_link').get('href'))
    print(f'Всего каталогов: {len(catalogs_list)}')


def get_pages(last_catalog_html):  # Ф-ция создает все ссылки пагинации на каталог, который она принимает
    html = get_html(last_catalog_html)
    soup = BeautifulSoup(html, 'html.parser')
    try:
        pagination = soup.find('div', class_='module-pagination').find_all('a', class_='dark_link')
        last_pagination = int(pagination[-1].string)
        pages_list.append(last_catalog_html)
        for el in range(2, last_pagination + 1):
            pages_list.append(last_catalog_html + PAGINATION_WORD + str(el))
    except:
        pages_list.append(last_catalog_html)


def get_goods(page_html):
    html = get_html(page_html)
    soup = BeautifulSoup(html, 'html.parser')
    try:
        goods = soup.find('div', class_='catalog_block items block_list').find_all('a', class_='dark_link')
        for good in goods:
            if re.match(HOST_URL, good.get('href')):
                goods_list.append(good.get('href'))
            else:
                goods_list.append(HOST_URL + good.get('href'))
    except:
        print('Ошибка единицы товара. Парсинг продолжается.')


def get_all_pages():  # Ф-ция делает полный список страниц (по всем категориям сайта) на товары
    start = datetime.now()
    print('Собираются ссылки по всей пагинации...')
    for el in catalogs_list:
        get_pages(el)
    # with Pool(pool_process) as p:
    #     p.map(get_goods, pages_list)
    finish = datetime.now()
    print('Пагинация собрана за: ', finish - start)
    print(f'Всего страниц на сайте: {len(pages_list)}')


def get_all_url_goods():  # Ф-ция делает полный список ссылок на товары
    start = datetime.now()
    print('Собираются ссылки на все товары...')
    for el in pages_list:
        get_goods(el)
    # with Pool(pool_process) as p:
    #     p.map(get_goods, pages_list)
    finish = datetime.now()
    print('Ссылки собраны за: ', finish - start)
    print(f'Всего товаров на сайте: {len(goods_list)}')


def get_good_data(html):
    html = get_html(html)
    soup = BeautifulSoup(html, 'lxml')
    try:
        name = soup.find('h1', id='pagetitle').text.strip()
    except:
        name = ' '
    try:
        photo_cont = soup.find('div', class_='slides').find_all('a')
        photos = []
        for el in photo_cont:
            photos.append(HOST_URL + el.get('href'))
        photos = '; '.join(photos)
    except:
        photos = ' '
    try:
        description = soup.find('div', class_='detail_text').text.strip().replace('\t', ' ')
    except:
        description = ' '
    try:
        barcode = ' '
        barcode_cont = soup.find('div', class_='wraps').find('table', class_='props_list nbg').find_all('tr', itemprop='additionalProperty')
        for el in barcode_cont:
            barcode_name = el.find('td', class_='char_name').text.strip()
            barcode_value = el.find('td', class_='char_value').text.strip()
            if barcode_name == 'Штрихкод':
                barcode = barcode_value
    except:
        barcode = ' '
    try:
        vendor_code = ' '
        vendor_code_cont = soup.find('div', class_='wraps').find('table', class_='props_list nbg').find_all('tr', itemprop='additionalProperty')
        for el in vendor_code_cont:
            vendor_code_name = el.find('td', class_='char_name').text.strip()
            vendor_code_value = el.find('td', class_='char_value').text.strip()
            if vendor_code_name == 'Артикул':
                vendor_code = vendor_code_value
    except:
        vendor_code = ' '

    good_data = {
        'vendor_code': vendor_code,
        'barcode': barcode,
        'name': name,
        'description': description,
        'photos': photos,
    }
    print(good_data)
    return good_data


def get_all_goods_with_csv():
    with open(FILE_NAME, 'w', newline='') as f:  # newline нужно чтобы не было лишних переносов строк в ксв файле
        writer = csv.writer(f, delimiter=';')  # delimiter нужен чтобы ксв разделял данные по колонкам
        writer.writerow(['Артикул', 'Штрихкод', 'Наименование', 'Описание', 'Фотографии'])
        for element in goods_list:
            n = get_good_data(element)
            writer.writerow([n['vendor_code'], n['barcode'], n['name'], n['description'], n['photos']])


def parse():
    start = datetime.now()
    html = get_html(URL)
    get_main_content(html)
    get_all_pages()
    get_all_url_goods()
    get_all_goods_with_csv()
    startfile(FILE_NAME)  # Запускает файл через модуль os
    finish = datetime.now()
    print('Парсинг завершен за: ', finish - start)


if __name__ == '__main__':
    parse()



# test_list = ['https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120437/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187275/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187277/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187320/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187021/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127096/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127072/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187678/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187011/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187018/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187009/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187307/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187737/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80851/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187016/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120528/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187309/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187746/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187677/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187736/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187313/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187321/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187686/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187691/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187697/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187709/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187680/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187710/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187713/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80809/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187683/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120527/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187019/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187274/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187023/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187726/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187314/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127095/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187659/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187705/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80675/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127070/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127077/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187319/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187025/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/186975/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127583/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127110/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127098/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127086/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80852/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127099/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187629/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/121321/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120420/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120427/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120522/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80857/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120520/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/126990/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80856/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120445/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/126994/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80808/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/126997/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120468/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120331/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80846/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127065/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80807/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120516/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80810/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80821/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120517/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80785/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80830/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80820/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120552/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80818/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120321/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80806/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120454/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127066/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80803/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80863/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120556/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80865/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120446/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120519/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120421/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80870/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80819/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80862/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80879/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80816/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80813/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120481/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127080/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80814/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80783/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80868/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80793/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120482/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127067/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120469/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120554/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120415/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80811/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127064/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/126996/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80782/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120448/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120470/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127062/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120518/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80795/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120557/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80860/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120464/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120444/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120444/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120485/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120518/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120491/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120447/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120521/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80817/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120479/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120330/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80883/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80845/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80847/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80805/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80848/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80828/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80849/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80850/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80861/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120472/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120530/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80808/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80809/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80810/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80811/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80820/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80821/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80827/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80831/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80834/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80835/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80836/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127070/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127072/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127062/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127063/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127064/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80840/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80841/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80845/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80846/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80858/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120474/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120480/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80836/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80869/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80781/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80872/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127083/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80880/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120455/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80831/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80864/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80835/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120457/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120458/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80779/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80822/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80871/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120526/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80792/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80870/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80875/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80876/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80878/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80879/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80880/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80881/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80882/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80883/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80884/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187710/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187709/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187712/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/187713/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120476/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120477/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120478/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127088/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127087/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80778/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80882/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80786/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127079/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127090/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127082/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127105/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120430/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80837/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127097/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127111/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127093/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127089/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120432/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120424/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/127087/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80823/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80855/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80824/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/80838/', 'https://borisov-praktik.by/catalog/oboi/bumazhnye_oboi_/120423/']
#
# def test():
#     with open(FILE_NAME, 'w', newline='') as f:  # newline нужно чтобы не было лишних переносов строк в ксв файле
#         writer = csv.writer(f, delimiter=';')  # delimiter нужен чтобы ксв разделял данные по колонкам
#         writer.writerow(['Артикул', 'Штрихкод', 'Наименование', 'Описание', 'Фотографии'])
#         # for element in test_list:
#         #     n = get_good_data(element)
#         #     writer.writerow((n['vendor_code'], n['barcode'], n['name'], n['description'], n['photos']))
#
#         with Pool(pool_process) as p:
#             p.map(make_all, test_list)
#
#
# def write_csv(data):
#     with open(FILE_NAME, 'a', newline='') as f:
#         writer = csv.writer(f, delimiter=';')
#         writer.writerow((data['vendor_code'], data['barcode'], data['name'], data['description'], data['photos']))
#
#
# def make_all(url):
#     data = get_good_data(url)
#     write_csv(data)



