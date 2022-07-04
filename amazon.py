import re
import requests

from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.common.by import By


from sheet_driver_setting import sheet_setting, driver_setting
from tools import title_convert, input_to_spreadsheet, input_to_text



# ユーザー設定項目//////////////////////////////////////////////////////////////

# スプレッドシートキー3つ
SPREADSHEET_KEY = '#####'

# jsonファイル名
SERVICE_ACCOUNT_FILE = '####'

# 「タイトル」が何行目に記載されているか
FIRST_COLUMN = 1

# 入力する列のアルファベット
INPUT_ROW_LETTER = 'M'


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
        'ｺﾐｯｸｽ版', '分冊版', 'ﾓﾉｸﾛ版', 'ｶﾗｰ版',
        '巻', '単行本版',
    ]

    for word in words:
        if word in get_title:
            get_title = get_title.replace(word, '')
            
    return get_title


# タイトルに含まれる括弧内の文字を削除
def delete_kakko(book_title):
    book_title = book_title.replace('（', '(').replace('）', ')')
    new_book_title = re.sub('\(.*\)', '', book_title)

    return new_book_title


# タイトルに含まれる巻数を削除
def book_title_modify(book_title):
    kansuji = [
        '一', '二', '三', '四', '五',
        '六', '七', '八', '九', '十',
    ]
    title_length = len(book_title)

    for i in range(1, title_length+1):

        title_part = book_title[-i:]
        kansuji_flag = False

        count = 0
        for s in title_part:
            if s in kansuji:
                count += 1
        
        if count == len(title_part):
            kansuji_flag = True
        
        if (kansuji_flag==False):
            new_title = book_title[:title_length+1-i]
            break

    return new_title


# スクレイピング関数
def scraping(title_list, driver):

    over_18_check = False
    
    # サイトURL
    base_url = 'https://www.amazon.co.jp/ref=nav_logo'
    driver.get(base_url)
    sleep(4)

    # kindleストア選択
    driver.find_element(By.CSS_SELECTOR, '#nav-search-dropdown-card').click()
    sleep(1)
    driver.find_element(By.CSS_SELECTOR, 'select.searchSelect > option[value="search-alias=digital-text"]').click()
    sleep(1)

    result_list = []
    for title in title_list:
        result = ''
        searched_word = title_convert(title)
        title_length = len(searched_word)

        # search
        search_bar = driver.find_element(By.CSS_SELECTOR, '#twotabsearchtextbox')
        search_bar.clear()
        sleep(1)
        search_bar.send_keys(title)
        driver.find_element(By.CSS_SELECTOR, '#nav-search-submit-button').click()
        sleep(4)

        if not over_18_check:
            try:
                driver.find_element(By.CSS_SELECTOR, 'div.a-popover-inner > div.s-align-children-center > span.a-button-primary').click()
                sleep(4)
                over_18_check = True
            except:
                pass

        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        

        # 検索タイトルと一致するものを全て取得
        pre_book_list = []
        books = soup.select('div.s-result-list > div[data-component-type="s-search-result"]')[:5]
        for book in books:
            book_title = book.select_one('h2.a-size-mini').text.strip()

            genre = ''
            price_tag = book.select_one('div.s-price-instructions-style')
            if price_tag:
                genre = price_tag.text
            
            is_available = False
            is_available = book.select_one('div.a-spacing-top-mini span.a-declarative > form')
            if is_available:
                is_available = True

            # タイトル修正
            match_flag = False
            modified_book_title1 = delete_kakko(book_title)
            modified_book_title2 = title_convert(modified_book_title1)
            modified_book_title3 = delete_some_words(modified_book_title2)
            cleaned_book_title = book_title_modify(modified_book_title3)

            difference_of_title = len(cleaned_book_title) - title_length
            if (searched_word==cleaned_book_title[:title_length]) and (difference_of_title >= 0) and ((cleaned_book_title[-difference_of_title:].isdecimal()==True) or difference_of_title == 0):
                match_flag = True

            if (match_flag == True) and ('Kindle版' in genre) and (is_available == True):
                pre_book_list.append(book)


        # タイトルが一致するものの中から、単行本のタグを取得
        if pre_book_list:
            hit_book = pre_book_list[0]
            hit_title = hit_book.select_one('h2.a-size-mini').text
            check_title = hit_title

            for pre_book in pre_book_list:
                book_title = pre_book.select_one('h2.a-size-mini').text
                if ('分冊版' not in book_title) and ('カラー版' not in book_title) and (hit_title != book_title):
                    hit_book = pre_book
                    check_title = book_title
          
            # 巻数確認
            detail_page_url = 'https://www.amazon.co.jp' + hit_book.select_one('h2.a-size-mini > a').get('href')

            driver.get(detail_page_url)
            sleep(4)

            html = driver.page_source
            detail_soup = BeautifulSoup(html, 'lxml')

            series_tag = detail_soup.select_one('#SeriesWidgetShvl > div.shoveler-heading > span')
            if series_tag:
                series_txt = series_tag.text.strip()
                howmany_books = series_txt.replace('このシリーズの一覧 (全', '').replace(')', '')

                if '分冊版' in check_title:
                    result = '分冊版' + howmany_books + 'まで'
                else:
                    result = howmany_books + 'まで'
            
            else:
                result = '巻数不明'

        else:
            result = '配信なし'
            

        result_list.append(result)
        input_to_text(title, result, 'a', 'amazon.txt')
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
        input_to_text('', '', 'w', 'amazon.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
