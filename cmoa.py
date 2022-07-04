from bs4 import BeautifulSoup
from time import sleep


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
INPUT_ROW_LETTER = 'C'


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
        '【コミックス版】', '【分冊版】', 'コミックス版', '分冊版', 
        '【モノクロ版】', '【カラー版】', 'モノクロ版', 'カラー版',
    ]

    for word in words:
        if word in get_title:
            get_title = get_title.replace(word, '')
            
    return get_title



# スクレイピング関数
def scraping(title_list, driver):

    # サイトURL
    base_url = 'https://www.cmoa.jp/search/result/?header_word={}&x=0&y=0'
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
        books = soup.select('div.search_result_table li.search_result_box')[:5]
        for book in books:
            book_title = book.select_one('div.search_result_box_right > div.search_result_box_right_sec1 > p > a').text.strip()
            # 無駄な文字を排除
            cleaned_book_title = delete_some_words(book_title)
            cleaned_book_title = title_convert(cleaned_book_title)

            if searched_word == cleaned_book_title:
                pre_book_list.append(book)


        # タイトルが一致するものの中から、単行本のタグを取得
        if pre_book_list:
            hit_book = pre_book_list[0]
            hit_title = hit_book.select_one('div.search_result_box_right > div.search_result_box_right_sec1 > p > a').text

            for pre_book in pre_book_list:
                book_title = pre_book.select_one('div.search_result_box_right > div.search_result_box_right_sec1 > p > a').text
                if ('分冊版' not in book_title) and ('カラー版' not in book_title) and (hit_title != book_title):
                    hit_book = pre_book
          
            # 完結しているか
            book_condition_tag = hit_book.select_one('div.search_result_box_right > div.search_result_box_right_sec1 > p > span.end_m')
            if book_condition_tag:
                result = '完結'
                
            # 完結していない場合、巻数を確認
            if not result:
                # タイトル
                book_title_tag = hit_book.select_one('div.search_result_box_right > div.search_result_box_right_sec1 > p > a')
                book_title = book_title_tag.text

                # 巻数
                howmany_books = hit_book.select_one('div.search_result_box_right_sec2left > div.color_or > span.margin_right10').text
                k = howmany_books.find('～')
                if k != -1:
                    howmany_books = howmany_books[k+1:]

                if '分冊版' in book_title:
                    result = '分冊版' + howmany_books + 'まで'
                else:
                    result = howmany_books + 'まで'

        else:
            result = '配信なし'
            

        result_list.append(result)
        input_to_text(title, result, 'a', 'cmoa.txt')
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
        input_to_text('', '', 'w', 'cmoa.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
