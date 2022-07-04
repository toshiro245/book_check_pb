import gspread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from oauth2client.service_account import ServiceAccountCredentials



# スプレッドシート設定
def sheet_setting(service_account_file, spreadsheet_key):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_file, scope)
    gc = gspread.authorize(credentials)

    worksheet = gc.open_by_key(spreadsheet_key).get_worksheet(0)

    return worksheet



# Driver Setting
def driver_setting():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=options)
    driver.implicitly_wait(5)

    return driver