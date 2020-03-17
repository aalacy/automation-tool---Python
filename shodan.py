import os
import json
import re
import time
import pdb
import urllib.parse
from urllib.parse import urlparse
from lxml import etree
from urllib3 import HTTPConnectionPool

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display

BASE_PATH = os.path.abspath(os.curdir)

# Show virtual window instead of headless selenium
Display(visible=0, size=(620, 840)).start()

option = webdriver.ChromeOptions()
option.add_argument('--no-sandbox')
driver = webdriver.Chrome(executable_path= './data/chromedriver.exe', chrome_options=option)
driver.get('https://www.crunchbase.com/home')
pdb.set_trace()
# http = urllib3.PoolManager()
# res = http.request('GET', 'https://www.shodan.io/search?query=grove.co')  
# data = etree.HTML(res.data) 
# href = 'https://www.shodan.io' + data.xpath('//div[@class="search-result"][1]//a[2]/@href')[0]


# res = driver.find_element_by_xpath('//div[@class="search-result"]')

