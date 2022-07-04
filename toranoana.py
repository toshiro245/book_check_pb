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
INPUT_ROW_LETTER = 'R'


# 途中からスタートしたい場合の設定/////////////////

# 途中から始めたい場合はTrue, 最初からの場合はFalse
is_restart = False
# is_restart = True

# 何行目から再開したいか
restart_line = 22

# //////////////////////////////////////////////////////////////////////////



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
    base_url_danshi = 'https://ecs.toranoana.jp/tora/ec/app/catalog/list?searchWord={title}&commodity_kind_name=%E6%9B%B8%E7%B1%8D&currentPage={page}'
    base_url_joshi = 'https://ecs.toranoana.jp/joshi/ec/app/catalog/list?searchWord={title}&commodity_kind_name=%E6%9B%B8%E7%B1%8D&currentPage={page}'
    result_list = []
    

    for title in title_list[:30]:
        title = title.replace('%', '％')
        
        result = ''
        searched_word = title_convert(title)
        title_length = len(searched_word)

        url = base_url_danshi.format(title=title, page='1')
        driver.get(url)
        sleep(4)

        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        # ページ数取得
        last_page_tag = soup.select('#pagerLinkArea > a.pagingCount')
        if last_page_tag:
            last_page = int(last_page_tag[-1].text)
        else:
            last_page = 1
        

        # 検索タイトルと一致するものを全て取得
        pre_book_list = []
        book_title_list = []
        for page_num in range(1, last_page+1):
            
            # 男性向け
            if page_num != 1:
                url = base_url_danshi.format(title=title, page=str(page_num))
                driver.get(url)
                sleep(4)       
            
            books = driver.find_elements(By.CSS_SELECTOR, 'ul.product-list-container > li.product-list-item')
            for book in books:
                book_title = book.find_element(By.CSS_SELECTOR, 'h3.product-list-title > a').text.strip()
                # 無駄な文字を排除
                match_flag = False
                modified_book_title = title_convert(book_title)
                cleaned_book_title = book_title_modify(modified_book_title)

                difference_of_title = len(cleaned_book_title) - title_length
                if (searched_word==cleaned_book_title[:title_length]) and (difference_of_title > 0) and (cleaned_book_title[-difference_of_title:].isdecimal()==True):
                    match_flag = True

                if (match_flag == True) and (modified_book_title not in book_title_list) and (modified_book_title != searched_word):
                    pre_book_list.append(book)
                    book_title_list.append(modified_book_title)
                

            # 女性向け
            url = base_url_joshi.format(title=title, page=str(page_num))
            driver.get(url)
            sleep(4)

            books = driver.find_elements(By.CSS_SELECTOR, 'ul.product-list-container > li.product-list-item')
            for book in books:
                book_title = book.find_element(By.CSS_SELECTOR, 'h3.product-list-title > a').text.strip()
                # 無駄な文字を排除
                match_flag = False
                modified_book_title = title_convert(book_title)
                cleaned_book_title = book_title_modify(modified_book_title)

                difference_of_title = len(cleaned_book_title) - title_length
                if (searched_word==cleaned_book_title[:title_length]) and (difference_of_title > 0) and (cleaned_book_title[-difference_of_title:].isdecimal()==True):
                    match_flag = True

                if (match_flag == True) and (modified_book_title not in book_title_list) and (modified_book_title != searched_word):
                    pre_book_list.append(book)
                    book_title_list.append(modified_book_title)



        if pre_book_list:
            howmany_books = len(pre_book_list)
            result = str(howmany_books) + '冊まで'
            

        else:
            result = '配信なし'

            

        result_list.append(result)
        input_to_text(title, result, 'a', 'toranoana.txt')
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
        input_to_text('', '', 'w', 'toranoana.txt')

    # スクレイピング実行
    result_list = scraping(title_list, driver)

    # スプレッドシートへ書き込み
    input_to_spreadsheet(INPUT_ROW_LETTER, first_column, result_list, worksheet)



# 実行
if __name__ == '__main__':
    main()
