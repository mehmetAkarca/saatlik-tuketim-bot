import os
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.message import EmailMessage

# --- AYARLAR ---
SITE_URL = 'http://195.214.140.20:8082/login.php'
KULLANICI_ADI = 'TARIZOCAM'
SIFRE = 'izocaM2019'
INDIRME_KLASORU = Path('.') / 'indirilenler'

def mail_gonder(dosya_yolu, dosya_adi):
    MAIL_SIFRE = os.environ.get('MAIL_SIFRE') # GitHub Secrets'tan gelecek
    GONDERICI = "updatestatu.4@gmail.com" # Burayı güncelleyin
    ALICI = "mhmtakarca@gmail.com"      # Burayı güncelleyin

    msg = EmailMessage()
    msg['Subject'] = f'Otomatik Rapor: {dosya_adi}'
    msg['From'] = GONDERICI
    msg['To'] = ALICI
    msg.set_content(f"{dosya_adi} tarihli rapor ekte sunulmuştur.")

    with open(dosya_yolu, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='xlsx', filename=dosya_adi)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GONDERICI, MAIL_SIFRE)
        smtp.send_message(msg)

# --- ANA AKIŞ ---
INDIRME_KLASORU.mkdir(parents=True, exist_ok=True)
dun = datetime.now() - timedelta(days=1)
tr_tarih = f"{dun.day} {['','Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'][dun.month]} {dun.year}"
hedef_ad = f"proses_saatlik_{dun.year}_{dun.month:02d}_{dun.day:02d}.xlsx"
hedef = INDIRME_KLASORU / hedef_ad

opts = webdriver.ChromeOptions()
opts.add_argument('--headless') # Sunucu için şart
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
wait = WebDriverWait(driver, 20)

try:
    driver.get(SITE_URL)
    wait.until(EC.presence_of_element_located((By.NAME, 'email'))).send_keys(KULLANICI_ADI)
    driver.find_element(By.NAME, 'password').send_keys(SIFRE)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    
    wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Saatlik Tüketim Geçmişi'))).click()
    wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, tr_tarih))).click()
    
    excel_url = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Excel'e Aktar"))).get_attribute('href')
    
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    
    response = session.get(excel_url)
    with open(hedef, 'wb') as f:
        f.write(response.content)
    
    mail_gonder(hedef, hedef_ad)
    print("✅ İşlem tamam.")
except Exception as e:
    print(f"❌ Hata: {e}")
finally:
    driver.quit()
