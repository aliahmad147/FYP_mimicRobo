from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import webbrowser
# webbrowser.get('firefox').open_new_tab('http://www.google.com')
driver = webdriver.Chrome('C:\chromedriver')
#driver = webdriver.Firefox("C:\geckodriver")
print ("Done")
url = 'C:/Users/Ahmad/PycharmProjects/GUI_test/page_test.pdf'
driver.get(url)
while True:
    time.sleep(1.5)
    driver.refresh()
