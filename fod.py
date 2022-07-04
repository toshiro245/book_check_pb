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
INPUT_ROW_LETTER = 'N'


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
        '巻', 
    ]

    for word in words:
        if word in get_title:
            get_title = get_title.replace(word, '')
            
    return get_title



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

    # サイトURL
    base_url = 'https://manga.fod.fujitv.co.jp/search?keyword={}'
    result_list = []
    for title in title_list:
        result = '配信なし'
        searched_word = title_convert(title)
        title_length = len(searched_word)

        url = base_url.format(title)
        driver.get(url)
        sleep(4)

        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        

        # 検索結果を全て取得
        books = soup.select('ul.comlist_column1 > li > div.product_info > h3 > a')[:10]
        book_urls = [ 'https://manga.fod.fujitv.co.jp' + book.get('href') for book in books ]

        count = 0
        for book_url in book_urls:
            driver.get(book_url)
            sleep(4)

            html = driver.page_source
            detail_soup = BeautifulSoup(html, 'lxml')

            book_title = detail_soup.select_one('div.product_info > h2').text.strip()

            # 無駄な文字を排除
            match_flag = False
            modified_book_title1 = title_convert(book_title)
            modified_book_title2 = delete_some_words(modified_book_title1)
            cleaned_book_title = book_title_modify(modified_book_title2)

            difference_of_title = len(cleaned_book_title) - title_length
            if (searched_word==cleaned_book_title[:title_length]) and (difference_of_title > 0) and (cleaned_book_title[-difference_of_title:].isdecimal()==True):
                match_flag = True


            if ((match_flag==True) and (count==0)) or ((match_flag==True) and ('分冊版' not in book_title) and ('カラー版' not in book_title)):
                # 完結しているか
                finish_label = detail_soup.select_one('p.label_container > label.finish')
                if finish_label:
                    result = '完結'
                
                # 完結していない場合、巻数確認
                else:
                    series_tag = detail_soup.select_one('article.com_container > h3.line_h3')
                    if series_tag:
                        series_txt = series_tag.text.strip()
                        howmany_books = series_txt.replace('作品一覧　全', '').replace('件', '')
                        if '分冊版' in book_title:
                            result = '分冊版' + howmany_books + '巻まで'
                        else:
                            result = howmany_books + '巻まで'

                    else:
                        result = '巻数不明'
                count += 1

                if ('分冊版' not in book_title) and ('カラー版' not in book_title):
                    break


        result_list.append(result)
        input_to_text(title, result, 'a', 'fod.txt')
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
        input_to_text('', '', 'w', 'fod.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
