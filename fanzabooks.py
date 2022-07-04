import requests

from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.common.by import By

from sheet_driver_setting import sheet_setting, driver_setting
from tools import title_convert, input_to_spreadsheet, input_to_text



# ユーザー設定項目//////////////////////////////////////////////////////////////

# スプレッドシートキー3つ
SPREADSHEET_KEY = '###'

# jsonファイル名
SERVICE_ACCOUNT_FILE = '###'

# 「タイトル」が何行目に記載されているか
FIRST_COLUMN = 1

# 入力する列のアルファベット
INPUT_ROW_LETTER = 'G'


# 途中からスタートしたい場合の設定/////////////////

# 途中から始めたい場合はTrue, 最初からの場合はFalse
is_restart = False
# is_restart = True

# 何行目から再開したいか
restart_line = 22

# //////////////////////////////////////////////////////////////////////////



# 取得したタイトルのうち、不要な文言を削除
def delete_some_words(get_title):
    words = [
        '【電子限定版】', '【FANZA限定版】', '【電子特装版】', '（単話）', 
        'シリーズ', '【フルカラー成人版】', '【1話立ち読み付き】', '【単行本版】',
        '【特装版】', '【デジタル特装版】', '【特典付き】', '【フルカラー】',
        '【FANZA限定特典付き】', '【FANZA特装版】', 
    ]

    for word in words:
        if word in get_title:
            get_title = get_title.replace(word, '')
            
    return get_title



# スクレイピング関数
def scraping(title_list, driver):
    
    # サイトURL
    base_url = 'https://book.dmm.co.jp/search/?service=ebook&searchstr={}'
    result_list = []
    over_18_check = False

    for title in title_list:
        result = ''
        searched_word = title_convert(title)

        url = base_url.format(title)
        driver.get(url)
        sleep(4)

        if not over_18_check:
            driver.find_element(By.CSS_SELECTOR, "div.ageCheck__btnBox > div.ageCheck__btn:nth-of-type(2)").click()
            over_18_check = True
            sleep(3)

        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        

        # 検索タイトルと一致するものを全て取得
        pre_book_list = []
        books = soup.select('#fn-list > li.m-boxListBookProduct__item')[:5]
        for book in books:
            book_title = book.select_one('span.m-boxListBookProductTmb__img > img').get('alt')
            # 無駄な文字を排除
            cleaned_book_title = delete_some_words(book_title)
            cleaned_book_title = title_convert(cleaned_book_title)

            if searched_word == cleaned_book_title:
                pre_book_list.append(book)


        # タイトルが一致するものの中から、単行本のタグを取得
        if pre_book_list:
            hit_book = pre_book_list[0]
            detail_url = hit_book.select_one('div.m-boxListBookProductTmb > a.fn-addI3Parameters').get('href')
            driver.get(detail_url)
            sleep(3)

            html = driver.page_source
            detail_soup = BeautifulSoup(html, 'lxml')

            # 完結済みかどうか
            finish_or_not_tag = detail_soup.select_one('div.m-boxDetailProduct__info__itemStatusList > ul.m-boxDetailProductInfoStatusList')
            if finish_or_not_tag:
                if '完結' in finish_or_not_tag.text:
                    result = '完結'
          
            # 完結していない場合、巻数を確認
            if not result:
                series = detail_soup.select_one('div.l-areaDetailSeriesWorks div.m-boxSeriesBasket')
                if series:
                    series_text = series.select_one('div.m-boxHeadSeriesBasket > div.m-boxHeadSeriesBasket__ttl').text
                    initial = series_text.find('品')
                    last = series_text.find('まで')
                    howmany_books = series_text[initial+1:last].strip()

                else:
                    howmany_books = '1巻'

                result = str(howmany_books) + 'まで'

        else:
            result = '配信なし'
            

        result_list.append(result)
        input_to_text(title, result, 'a', 'fanzabooks.txt')
        print(f'{title}-{result}')
    
    return result_list



# main関数
def main():
    # スプレッドシート初期設定
    worksheet = sheet_setting(SERVICE_ACCOUNT_FILE, SPREADSHEET_KEY)

    # タイトルリスト取得
    if is_restart:
        first_column = restart_line - 1
    else:
        first_column = FIRST_COLUMN
    title_list = worksheet.col_values(1)[first_column:]
    
    # Driver Setting
    driver = driver_setting()

    # データ保存用テキストファイルの更新
    if is_restart == False:
        input_to_text('', '', 'w', 'fanzabooks.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
