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
INPUT_ROW_LETTER = 'J'


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
    ]

    for word in words:
        if word in get_title:
            get_title = get_title.replace(word, '')
            
    return get_title




# スクレイピング関数
def scraping(title_list, driver):

    # サイトURL
    base_url = 'https://comic.jp/comic/store/search?Keyword={}'
    result_list = []
    for title in title_list:
        result = ''
        searched_word = title_convert(title)

        url = base_url.format(title)
        driver.get(url)
        sleep(4)

        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        

        # 検索タイトルと一致するものを全て取得
        pre_book_list = []
        books = soup.select('ul.item-list > li.item')[:5]
        for book in books:
            book_title = book.select_one('div.content > span.title').text.strip()

            # 無駄な文字を排除
            cleaned_book_title = title_convert(book_title)
            cleaned_book_title = delete_some_words(cleaned_book_title)

            if searched_word == cleaned_book_title:
                pre_book_list.append(book)


        # タイトルが一致するものの中から、単行本のタグを取得
        if pre_book_list:
            hit_book = pre_book_list[0]
            hit_title = hit_book.select_one('div.content > span.title').text
            check_title = hit_title

            for pre_book in pre_book_list:
                book_title = pre_book.select_one('div.content > span.title').text
                if ('分冊版' not in book_title) and ('カラー版' not in book_title) and (hit_title != book_title):
                    hit_book = pre_book
                    check_title = book_title

            detail_url = 'https://comic.jp' + hit_book.select_one('a').get('href')
          
            r = requests.get(detail_url, timeout=5)
            r.raise_for_status()
            sleep(3)
            soup = BeautifulSoup(r.content, 'lxml')
                
            # 完結しているか確認
            finish_or_not = soup.select_one('div.number-volumn > span.completed-flag')
            if finish_or_not:
                result = '完結'

            else:
                howmany_books = soup.select_one('div.number-volumn > span.volumn').text.replace('配信中', '').replace('\n', '').strip()
                if '分冊版' in check_title:
                    result = '分冊版' + howmany_books
                else:
                    result = howmany_books

        else:
            result = '配信なし'
            

        result_list.append(result)
        input_to_text(title, result, 'a', 'comicjp.txt')
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
        input_to_text('', '', 'w', 'comicjp.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
