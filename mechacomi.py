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
INPUT_ROW_LETTER = 'S'


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


# 括弧内の文字を削除
def delete_kakko(book_title):
    book_title = book_title.replace('（', '(').replace('）', ')')
    new_book_title = re.sub('\(.*\)', '', book_title)

    return new_book_title


# スクレイピング関数
def scraping(title_list, driver):

    # サイトURL
    base_url = 'https://sp.comics.mecha.cc/books?utf8=%E2%9C%93&text={}'
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
        books = soup.select('ul.book_list > li')[:5]
        for book in books:
            book_title = book.select_one('div.detail span.title > a').text.strip()

            # 無駄な文字を排除
            cleaned_book_title = title_convert(book_title)
            cleaned_book_title = delete_some_words(cleaned_book_title)

            if searched_word == cleaned_book_title:
                pre_book_list.append(book)


        # タイトルが一致するものの中から、単行本のタグを取得
        if pre_book_list:
            hit_book = pre_book_list[0]
            hit_title = hit_book.select_one('div.detail span.title > a').text

            for pre_book in pre_book_list:
                book_title = pre_book.select_one('div.detail span.title > a').text
                if ('分冊版' not in book_title) and ('カラー' not in book_title) and (hit_title != book_title):
                    hit_book = pre_book
                

            # 完結しているか
            tags = hit_book.select_one('dd.tags > ul.clearfix')
            if tags:
                finish_or_not = tags.text
                if '完結' in finish_or_not:
                    result = '完結'

            if not result:
                detail_url = 'https://sp.comics.mecha.cc' + hit_book.select_one('div.detail span.title > a').get('href')
                driver.get(detail_url)
                sleep(4)

                html = driver.page_source
                detail_soup = BeautifulSoup(html, 'lxml')

                book_or_story = detail_soup.select_one('article > ul.c-nav')
                if book_or_story:
                    detail_url_volume = driver.current_url + '/volumes'
                    driver.get(detail_url_volume)
                    sleep(2)

                    page_num_list = driver.find_elements(By.CSS_SELECTOR, 'div.p-tmpPage > div.pagination > a') 
                    if page_num_list:
                        page_nums = len(page_num_list)

                        if page_nums > 0:
                            page_num_max = str(page_num_list[-2].text)

                            detail_url_volume_last = driver.current_url + f'?page={page_num_max}'
                            driver.get(detail_url_volume_last)
                            sleep(2)

                    detail_book_list = driver.find_elements(By.CSS_SELECTOR, 'ol.p-volumeList > li.p-volumeList_item')
                    howmany_books = detail_book_list[-1].find_element(By.CSS_SELECTOR, 'dl.p-volumeInfo_body > dt.p-volumeList_no').text.strip()

                    result = howmany_books + 'まで'


                else:
                    howmany_books_tag = detail_soup.select_one('dl.p-bookInfo_defList > dd:-soup-contains("まで配信")')
                    howmany_books = howmany_books_tag.text.strip().replace('まで配信中', '')
                    howmany_books = delete_kakko(howmany_books)

                    result = '分冊版' + howmany_books + 'まで'

                
        else:
            result = '配信なし'
            

        result_list.append(result)
        input_to_text(title, result, 'a', 'mechacomi.txt')
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
        input_to_text('', '', 'w', 'mechacomi.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
