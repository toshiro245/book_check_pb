import re
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
INPUT_ROW_LETTER = 'P'


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
        '分冊版', 'ﾓﾉｸﾛ版', 'ｶﾗｰ版',
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



# スクレイピング関数
def scraping(title_list, driver):

    # サイトURL
    base_url = 'https://bookwalker.jp/search/?qcat=&word={}'
    result_list = []
    safesearch_flag = False

    for title in title_list:
        result = ''
        searched_word = title_convert(title)

        url = base_url.format(title)
        driver.get(url)
        sleep(4)

        if not safesearch_flag:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(1)
                driver.find_element(By.CSS_SELECTOR, '#safesearch-advise > p > #safe-search-all').click()
                safesearch_flag = True
                sleep(3)
            except:
                pass

        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        

        # 検索タイトルと一致するものを全て取得
        pre_book_list = []
        books = soup.select('ul.m-tile-list > li.m-tile')[:5]
        for book in books:
            book_title = book.select_one('div.m-book-item__info-block p.m-book-item__title > a').text.strip()

            # 無駄な文字を排除
            modified_book_title1 = delete_kakko(book_title)
            modified_book_title2 = title_convert(modified_book_title1)
            cleaned_book_title = delete_some_words(modified_book_title2)

            if searched_word == cleaned_book_title:
                pre_book_list.append(book)


        # タイトルが一致するものの中から、単行本のタグを取得
        if pre_book_list:
            hit_book = pre_book_list[0]
            hit_title = hit_book.select_one('div.m-book-item__info-block p.m-book-item__title > a').text
            hit_title = delete_kakko(hit_title)
            check_title = hit_title

            for pre_book in pre_book_list:
                book_title = pre_book.select_one('div.m-book-item__info-block p.m-book-item__title > a').text
                book_title = delete_kakko(book_title)
                if ('分冊版' not in book_title) and ('カラー版' not in book_title) and (hit_title != book_title):
                    hit_book = pre_book
                    check_title = book_title

            # 完結しているか確認
            finish_tag = hit_book.select_one('div.m-book-item__tag-box > span.a-tag-comp')
            if finish_tag:
                result = '完結'

            if not result:
                series = hit_book.select_one('div.m-book-item__series > span.ico-txt')
                if series:
                    howmany_books = series.text.replace('シリーズ', '')
                    if '分冊版' in check_title:
                        result = '分冊版' + howmany_books + 'まで'
                    
                    else:
                        result = howmany_books + 'まで'

                else:
                    result = '巻数不明'

                

        else:
            result = '配信なし'
            

        result_list.append(result)
        input_to_text(title, result, 'a', 'bookwalker.txt')
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
        input_to_text('', '', 'w', 'bookwalker.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
