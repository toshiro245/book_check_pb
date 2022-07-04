import os
import re
import mojimoji


# タイトルのスペースや記号などの誤差許容するために、変換
def title_convert(title):
    code_regex = re.compile('[ 　!"#$%&\'\\\\()*+,-./:;<=>?@[\\]^_`{|}~〜＝＋「」〔〕“”〈〉『』【】＆＊・（）＄＃＠。、？！｀＋￥％･・☆]')
    
    title = str(title)

    # カタカナ、数字、英語を全て半角へ変換
    cleaned_title1 = mojimoji.zen_to_han(title)

    # 特殊文字、空白等削除
    cleaned_title2 = code_regex.sub('', cleaned_title1) 

    # アルファベットを全て小文字へ変換
    cleaned_title3 = cleaned_title2.lower()

    return cleaned_title3



# スプレッドシートへの書き込み
def input_to_spreadsheet(input_row_letter, first_column, result_list, worksheet):
    input_colomun = f'{input_row_letter + str(first_column+1)}:{input_row_letter + str(first_column+len(result_list))}'
    cell_list = worksheet.range(input_colomun)
    for cell, category in zip(cell_list, result_list):
        cell.value = category

    worksheet.update_cells(cell_list)



# テキストファイルへデータを保存
def input_to_text(title, result, mode='a', file_name=None):
    dir_name = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(dir_name, file_name)
    
    input_text = title + ',' +result + '\n'
    if mode == 'w':
        input_text = ''
        
    with open(p, mode) as text_file:
        text_file.write(input_text)


