import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import pywhatkit
import time
import threading
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime
import tempfile

class WhatsAppBotGUI:
    def __init__(self, root):
        self.root = root
        
        self.root.title('WhatsApp Excel Mesaj Botu - Otomatik Cevap Sistemi')
        self.contacts_file = ''
        self.message_file = ''
        self.contacts_df = None
        self.message = ''
        self.driver = None
        self.is_listening = False
        self.auto_reply_enabled = False
        self.auto_reply_message = ''
        self.auto_reply_rules = {}
        self.setup_ui()
        self.load_auto_reply_rules()
        self.update_keyword_listbox()

    def setup_ui(self):
        # Ana frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Sol panel - Mesaj gönderme
        left_frame = tk.LabelFrame(main_frame, text="Mesaj Gönderme", padx=5, pady=5)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        tk.Button(left_frame, text='Excel Dosyası Seç', command=self.select_contacts).grid(row=0, column=0, padx=5, pady=5)
        self.contacts_label = tk.Label(left_frame, text='Seçilmedi')
        self.contacts_label.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(left_frame, text='Mesaj Dosyası Seç', command=self.select_message).grid(row=1, column=0, padx=5, pady=5)
        self.message_label = tk.Label(left_frame, text='Seçilmedi')
        self.message_label.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(left_frame, text='Numaraları Yükle', command=self.load_contacts).grid(row=2, column=0, padx=5, pady=5)
        self.load_label = tk.Label(left_frame, text='')
        self.load_label.grid(row=2, column=1, padx=5, pady=5)

        self.contacts_text = scrolledtext.ScrolledText(left_frame, width=40, height=8)
        self.contacts_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        tk.Button(left_frame, text='Mesajları Gönder', command=self.start_sending).grid(row=4, column=0, columnspan=2, pady=10)

        # Sağ panel - Otomatik cevap sistemi
        right_frame = tk.LabelFrame(main_frame, text="Otomatik Cevap Sistemi", padx=5, pady=5)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Otomatik cevap ayarları
        reply_settings_frame = tk.LabelFrame(right_frame, text="Otomatik Cevap Ayarları", padx=5, pady=5)
        reply_settings_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        # Cevap türü seçimi
        tk.Label(reply_settings_frame, text="Cevap Türü:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.reply_type_var = tk.StringVar(value="smart")
        tk.Radiobutton(reply_settings_frame, text="Akıllı Cevap (Anahtar Kelimeli)", variable=self.reply_type_var, 
                      value="smart").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        tk.Radiobutton(reply_settings_frame, text="Sabit Cevap", variable=self.reply_type_var, 
                      value="fixed").grid(row=2, column=0, sticky='w', padx=5, pady=2)

        # Sabit cevap mesajı
        tk.Label(reply_settings_frame, text="Sabit Cevap Mesajı:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.auto_reply_text = scrolledtext.ScrolledText(reply_settings_frame, width=40, height=3)
        self.auto_reply_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.auto_reply_text.insert('1.0', 'Merhaba! Mesajınız alındı. En kısa sürede size dönüş yapacağız.')

        # Kontrol butonları
        self.auto_reply_var = tk.BooleanVar()
        tk.Checkbutton(reply_settings_frame, text="Otomatik Cevap Aktif", variable=self.auto_reply_var, 
                      command=self.toggle_auto_reply).grid(row=5, column=0, sticky='w', padx=5, pady=5)
        
        # Chrome Ayarları ve ilgili widgetları kaldırıldı.
        # Sadece anahtar kelime listesi ve Mesaj Dinlemeyi Başlat/Durdur butonu kalsın.

        # Anahtar kelime listesi (sadece görüntüleme)
        keyword_frame = tk.LabelFrame(right_frame, text="Mevcut Anahtar Kelimeler", padx=5, pady=5)
        keyword_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        self.keyword_listbox = scrolledtext.ScrolledText(keyword_frame, width=50, height=6, state='disabled')
        self.keyword_listbox.grid(row=0, column=0, padx=5, pady=5)

        # Butonlar
        button_frame = tk.Frame(right_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.listen_button = tk.Button(button_frame, text='Mesaj Dinlemeyi Başlat', command=self.toggle_listening)
        self.listen_button.pack(side='left', padx=5)

        # Durum göstergeleri
        self.status_frame = tk.Frame(right_frame)
        self.status_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        self.connection_status = tk.Label(self.status_frame, text="Bağlantı: Bağlı Değil", fg="red")
        self.connection_status.pack()
        
        self.listening_status = tk.Label(self.status_frame, text="Dinleme: Kapalı", fg="red")
        self.listening_status.pack()

        # Log alanı
        log_frame = tk.LabelFrame(self.root, text="Sistem Logları", padx=5, pady=5)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=12, state='disabled')
        self.log_text.pack(fill='both', expand=True)

    def toggle_auto_reply(self):
        self.auto_reply_enabled = self.auto_reply_var.get()
        self.auto_reply_message = self.auto_reply_text.get('1.0', tk.END).strip()
        status = "Aktif" if self.auto_reply_enabled else "Pasif"
        self.log(f"Otomatik cevap sistemi: {status}")

    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        if not self.auto_reply_enabled:
            messagebox.showwarning('Uyarı', 'Önce otomatik cevap sistemini aktifleştirin.')
            return
        # Eğer driver yoksa başlat
        if self.driver is None:
            self.setup_driver()
            # Eğer driver yine None ise hata ver ve çık
            if self.driver is None:
                self.log("Chrome başlatılamadı, dinleme başlatılamıyor!")
                return
        self.is_listening = True
        self.listen_button.config(text='Mesaj Dinlemeyi Durdur')
        self.auto_reply_var.set(True)
        self.auto_reply_enabled = True
        self.auto_reply_message = self.auto_reply_text.get('1.0', tk.END).strip()
        self.log("Chrome açılıyor ve direkt WhatsApp Web'e yönlendiriliyor...")
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def stop_listening(self):
        try:
            self.is_listening = False
            self.listen_button.config(text='Mesaj Dinlemeyi Başlat')
            self.listening_status.config(text="Dinleme: Kapalı", fg="red")
            self.log("Mesaj dinleme durduruldu.")
        except Exception as e:
            self.log(f"Dinleme durdurma hatası: {str(e)[:50]}...")

    def setup_driver(self):
        chrome_options = Options()
        self.log("Chrome başlatılıyor (sıfır ayar, açık hesaptan)...")
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.log("Chrome başarıyla başlatıldı")
            self.log("WhatsApp Web açılıyor...")
            self.driver.get("https://web.whatsapp.com")
            time.sleep(3)
            self.log("WhatsApp Web sayfası yüklendi")
            self.log("QR kodu telefonunuzla tarayın.")
            self.connection_status.config(text="Bağlantı: QR Kod Bekleniyor", fg="orange")
        except Exception as e:
            self.log(f"Chrome başlatma veya WhatsApp Web açma hatası: {str(e)[:100]}...")
            self.driver = None
            return False

        # GÜNCEL connection_selectors
        self.connection_selectors = [
            'div[role="grid"]',
            'div[data-testid="cell-frame-container"]',
            'div[aria-label="Sohbetler"]',
            'div[tabindex="-1"][role="row"]',
            'div[role="row"]',
            'div[data-testid="conversation"]',
            'div[data-testid="chat-list"]',
            'div[data-testid="conversation-list"]',
            'div[role="main"]'
        ]
        self.log("setup_driver tamamlandı.")

    def get_chat_rows(self):
        """Sohbet listesini güvenli bir şekilde alır"""
        # GÜNCEL sohbet satırı seçicileri
        chat_selectors = [
            'div._ak8l._ap1_',  # GÜNCEL SOHBET SATIRI SEÇİCİSİ
            'div[data-testid="cell-frame-container"]',
            'div[aria-label="Sohbetler"] [role="row"]',
            'div[tabindex="-1"][role="row"]',
            'div[role="grid"] [role="row"]',
            'div[role="row"]',
            'div[data-testid="conversation"]',
            'div[data-testid="chat-list"] [role="row"]',
            'div[data-testid="conversation-list"] [role="row"]',
            'div[role="main"] [role="row"]'
        ]
        
        for selector in chat_selectors:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                chat_rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if chat_rows:
                    self.log(f"Sohbet listesi bulundu: {selector} - {len(chat_rows)} sohbet")
                    return chat_rows
            except Exception as e:
                self.log(f"Seçici {selector} başarısız: {str(e)[:30]}...")
                continue
        self.log("Hiçbir sohbet listesi bulunamadı")
        return []

    def get_chat_name(self, chat_element):
        """Sohbet adını alır"""
        try:
            # Farklı seçicilerle sohbet adını bul
            name_selectors = [
                'span[data-testid="conversation-info-header-chat-title"]',
                'div[data-testid="cell-frame-title"]',
                'span[title]',
                'div[title]',
                'span[dir="auto"]',
                'div[dir="auto"]'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = chat_element.find_element(By.CSS_SELECTOR, selector)
                    if name_element:
                        name_text = name_element.text.strip()
                        if name_text:
                            return name_text
                        title_attr = name_element.get_attribute('title')
                        if title_attr:
                            return title_attr
                except Exception:
                    continue
            
            # Fallback: Element ID'si
            element_id = chat_element.get_attribute('id') or chat_element.get_attribute('data-testid')
            return f"Chat_{element_id or id(chat_element)}"
            
        except Exception as e:
            self.log(f"Sohbet adı alma hatası: {str(e)[:50]}...")
            return f"Chat_{id(chat_element)}"

    def debug_page_elements(self):
        """Sayfa elementlerini debug etmek için"""
        try:
            self.log("=== SAYFA DEBUG BİLGİLERİ ===")
            self.log(f"URL: {self.driver.current_url}")
            
            # Tüm data-testid'leri bul
            testid_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid]')
            testids = set()
            for elem in testid_elements:
                testid = elem.get_attribute('data-testid')
                if testid:
                    testids.add(testid)
            
            self.log(f"Bulunan data-testid'ler: {list(testids)[:10]}...")
            
            # Tüm role'leri bul
            role_elements = self.driver.find_elements(By.CSS_SELECTOR, '[role]')
            roles = set()
            for elem in role_elements:
                role = elem.get_attribute('role')
                if role:
                    roles.add(role)
            
            self.log(f"Bulunan role'ler: {list(roles)}")
            
        except Exception as e:
            self.log(f"Debug hatası: {str(e)[:50]}...")

    def get_recent_messages(self, count=5):
        """Son N mesajı alır"""
        try:
            message_selectors = [
                'div[data-testid="msg-meta"]',
                'div[data-testid="conversation-message"]',
                'div[role="row"] div[dir="ltr"]',
                'div[data-testid="msg-container"]',
                'div[data-testid="msg-text"]',
                'div[data-testid="msg-meta"] span'
            ]
            
            all_messages = []
            for msg_selector in message_selectors:
                try:
                    message_elements = self.driver.find_elements(By.CSS_SELECTOR, msg_selector)
                    if message_elements:
                        for element in message_elements:
                            message_text = element.text.strip()
                            if message_text and message_text not in all_messages:
                                all_messages.append(message_text)
                        break
                except Exception:
                    continue
            
            # Son N mesajı döndür
            return all_messages[-count:] if all_messages else []
            
        except Exception as e:
            self.log(f"Son mesajları alma hatası: {str(e)[:50]}...")
            return []

    def should_reply_to_message(self, message):
        """Mesaja cevap verilip verilmeyeceğini kontrol eder"""
        try:
            message_lower = message.lower()
            reply_type = self.reply_type_var.get()
            
            # Anahtar kelime kontrolü
            keyword_replies = self.auto_reply_rules.get("keyword_replies", {})
            for keyword, reply in keyword_replies.items():
                if keyword.lower() in message_lower:
                    self.log(f"Anahtar kelime bulundu: '{keyword}'")
                    return True
            
            # Cevap türüne göre kontrol
            if reply_type == "smart":
                # Akıllı cevap modunda her mesaja cevap ver
                return True
            elif reply_type == "fixed":
                # Sabit cevap modunda her mesaja cevap ver
                return True
            
            return False
            
        except Exception as e:
            self.log(f"Mesaj kontrol hatası: {str(e)[:50]}...")
            return False

    def get_last_message(self):
        """Son mesajı güvenli bir şekilde alır"""
        try:
            message_selectors = [
                'div[data-testid="msg-meta"]',
                'div[data-testid="conversation-message"]',
                'div[role="row"] div[dir="ltr"]',
                'div[data-testid="msg-container"]',
                'div[data-testid="msg-text"]'
            ]
            
            for msg_selector in message_selectors:
                try:
                    message_elements = self.driver.find_elements(By.CSS_SELECTOR, msg_selector)
                    if message_elements:
                        # Son mesajı al
                        last_message = message_elements[-1].text.strip()
                        if last_message:
                            return last_message
                except Exception:
                    continue
            return None
        except Exception as e:
            self.log(f"Mesaj alma hatası: {str(e)[:50]}...")
            return None

    def go_back_to_chat_list(self):
        """Sohbetler listesine geri dönmek için farklı yöntemler dener"""
        try:
            # Farklı geri dönme butonlarını dene
            back_selectors = [
                'span[data-icon="back-light"]',
                'button[aria-label="Geri"]',
                'button[aria-label="Back"]',
                'div[data-testid="back"]',
                'button[data-testid="back"]'
            ]
            
            for selector in back_selectors:
                try:
                    back_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    back_btn.click()
                    time.sleep(2)
                    return
                except Exception:
                    continue
            
            # Klavye ile geri dönmeyi dene
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(2)
            
        except Exception as e:
            self.log(f"Geri dönme hatası: {str(e)[:50]}...")

    def send_auto_reply(self, received_message):
        try:
            # Cevap türüne göre mesaj belirle
            if self.reply_type_var.get() == "smart":
                reply_message = self.get_smart_reply(received_message)
            else:
                reply_message = self.auto_reply_text.get('1.0', tk.END).strip()
            
            # Mesaj kutusunu bul ve mesajı gönder
            if self.send_message_to_current_chat(reply_message):
                self.log(f"Otomatik cevap gönderildi: {reply_message[:50]}...")
            else:
                self.log("Otomatik cevap gönderilemedi!")
                
        except Exception as e:
            self.log(f"Otomatik cevap gönderme hatası: {str(e)[:100]}...")

    def send_message_to_current_chat(self, message):
        """Mevcut sohbete mesaj gönderir"""
        try:
            # Mesaj kutusunu bulmak için farklı seçicileri dene
            message_box_selectors = [
                'div[contenteditable="true"][role="textbox"]',
                'div[contenteditable="true"][data-tab="10"]',
                'div[contenteditable="true"]',
                'div[data-testid="conversation-compose-box-input"]',
                'div[data-testid="compose-box-input"]',
                'div[data-testid="compose-box"]'
            ]
            
            message_box = None
            for selector in message_box_selectors:
                try:
                    message_boxes = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if message_boxes:
                        message_box = message_boxes[-1]
                        break
                except Exception:
                    continue
            
            if not message_box:
                self.log("Mesaj kutusu bulunamadı!")
                return False
            
            try:
                self.log("Mesaj kutusuna tıklanıyor...")
                message_box.click()
                time.sleep(2)  # Bekleme süresi artırıldı
                from selenium.webdriver.common.keys import Keys
                self.log("Mesaj kutusu temizleniyor (Ctrl+A + Delete)...")
                message_box.send_keys(Keys.CONTROL, 'a')
                message_box.send_keys(Keys.DELETE)
                time.sleep(1)  # Bekleme süresi artırıldı
                self.log(f"Mesaj yazılıyor: {message[:50]}...")
                message_box.send_keys(message)
                time.sleep(1.5)  # Bekleme süresi artırıldı
                self.log("Enter ile mesaj gönderiliyor...")
                message_box.send_keys(Keys.ENTER)
                time.sleep(3)  # Mesajın gönderilmesi için bekleme süresi artırıldı
                self.log("Mesaj gönderme işlemi tamamlandı.")
                return True
                
            except Exception as e:
                self.log(f"Mesaj gönderme hatası: {str(e)[:50]}...")
                return False
                
        except Exception as e:
            self.log(f"Mesaj kutusu bulma hatası: {str(e)[:50]}...")
            return False

    def select_contacts(self):
        file = filedialog.askopenfilename(filetypes=[('Excel Files', '*.xlsx')])
        if file:
            self.contacts_file = file
            self.contacts_label.config(text=os.path.basename(file))

    def select_message(self):
        file = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt')])
        if file:
            self.message_file = file
            self.message_label.config(text=os.path.basename(file))

    def load_contacts(self):
        if not self.contacts_file:
            messagebox.showerror('Hata', 'Lütfen bir Excel dosyası seçin.')
            return
        try:
            df = pd.read_excel(self.contacts_file)
            if 'Telefon' not in df.columns or 'Firma Adı' not in df.columns:
                messagebox.showerror('Hata', 'Excel dosyasında "Firma Adı" ve "Telefon" sütunları bulunmalı.')
                return
            # Sadece 05, +905 veya 5 ile başlayan numaraları al
            self.contacts_df = df[df['Telefon'].notna() & (
                df['Telefon'].astype(str).str.strip().str.startswith('05') |
                df['Telefon'].astype(str).str.strip().str.startswith('+905') |
                df['Telefon'].astype(str).str.strip().str.startswith('5')
            )].copy()
            def format_number(x):
                x = str(x)
                x = re.sub(r'\D', '', x)  # Sadece rakamlar kalsın
                if x.startswith('0'):
                    x = x[1:]
                if not x.startswith('90'):
                    x = '90' + x
                return x
            self.contacts_df['Telefon'] = self.contacts_df['Telefon'].astype(str).apply(format_number)
            self.contacts_text.delete('1.0', tk.END)
            for idx, row in self.contacts_df.iterrows():
                self.contacts_text.insert(tk.END, f"{row['Firma Adı']} - {row['Telefon']}\n")
            self.load_label.config(text=f"{len(self.contacts_df)} numara yüklendi.")
        except Exception as e:
            messagebox.showerror('Hata', f'Excel dosyası okunamadı: {e}')

    def load_message(self):
        if not self.message_file:
            messagebox.showerror('Hata', 'Lütfen bir mesaj dosyası seçin.')
            return False
        try:
            with open(self.message_file, 'r', encoding='utf-8') as f:
                self.message = f.read().strip()
            return True
        except Exception as e:
            messagebox.showerror('Hata', f'Mesaj dosyası okunamadı: {e}')
            return False

    def start_sending(self):
        if self.contacts_df is None or self.contacts_df.empty:
            messagebox.showerror('Hata', 'Önce numaraları yükleyin.')
            return
        if not self.load_message():
            return
        threading.Thread(target=self.send_messages, daemon=True).start()

    def send_messages(self):
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log('Lütfen WhatsApp Web QR kodunu telefonunuzla tarayın...')
        time.sleep(10)
        for idx, row in self.contacts_df.iterrows():
            phone = str(row['Telefon'])
            name = str(row['Firma Adı'])
            # Mesaj şablonundaki {firma_adi} placeholder'ını işletme adıyla değiştir
            personalized_message = self.message.replace('{firma_adi}', name)
            self.log(f'Gönderilecek mesaj: {personalized_message}')
            try:
                pywhatkit.sendwhatmsg_instantly(f'+{phone}', personalized_message, wait_time=8, tab_close=True, close_time=5)
                self.log(f'{name} ({phone}) numarasına mesaj gönderildi.')
            except Exception as e:
                self.log(f'Hata: {name} ({phone}) numarasına mesaj gönderilemedi. {e}')
            self.root.update()
            time.sleep(3)  # 3 saniye bekle
        self.log('Mesajlar gönderildi.')

        self.log_text.config(state='disabled')

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def load_auto_reply_rules(self):
        try:
            import os
            rules_path = os.path.join(os.path.dirname(__file__), "auto_reply_rules.json")
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.auto_reply_rules = json.load(f)
            self.log("Otomatik cevap kuralları yüklendi.")
        except Exception as e:
            self.log(f"Otomatik cevap kuralları yüklenemedi: {e}")
            # Varsayılan kurallar
            self.auto_reply_rules = {
                "default_reply": "Merhaba! Mesajınız alındı. En kısa sürede size dönüş yapacağız.",
                "keyword_replies": {},
                "time_based_replies": {}
            }



    def update_keyword_listbox(self):
        """Anahtar kelime listesini günceller"""
        self.keyword_listbox.config(state='normal')
        self.keyword_listbox.delete('1.0', tk.END)
        
        keyword_replies = self.auto_reply_rules.get("keyword_replies", {})
        if keyword_replies:
            for keyword, reply in keyword_replies.items():
                self.keyword_listbox.insert(tk.END, f"🔑 {keyword}\n")
                self.keyword_listbox.insert(tk.END, f"   💬 {reply}\n\n")
        else:
            self.keyword_listbox.insert(tk.END, "Anahtar kelime bulunamadı.")
        
        self.keyword_listbox.config(state='disabled')



    def get_smart_reply(self, message):
        """Gelen mesaja göre akıllı cevap oluşturur"""
        message_lower = message.lower()
        
        # Anahtar kelime kontrolü
        for keyword, reply in self.auto_reply_rules.get("keyword_replies", {}).items():
            if keyword in message_lower:
                return reply
        
        # Zaman bazlı cevap
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            return self.auto_reply_rules.get("time_based_replies", {}).get("morning", self.auto_reply_rules.get("default_reply"))
        elif 12 <= current_hour < 18:
            return self.auto_reply_rules.get("time_based_replies", {}).get("evening", self.auto_reply_rules.get("default_reply"))
        else:
            return self.auto_reply_rules.get("time_based_replies", {}).get("night", self.auto_reply_rules.get("default_reply"))

    def listen_for_messages(self):
        self.log("Dinleme başlatıldı. WhatsApp Web bağlantısı kontrol ediliyor...")
        try:
            # Sohbet listesinin yüklendiğinden emin ol
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="grid"]'))
            )
            self.log("Bağlantı başarılı, sohbet listesi bulundu.")
            self.listening_status.config(text="Dinleme: Aktif", fg="green")
            self.connection_status.config(text="Bağlantı: Bağlandı", fg="green")
        except Exception as e:
            self.log(f"Sohbet listesi bulunamadı: {str(e)[:100]}...")
            self.listening_status.config(text="Dinleme: Kapalı", fg="red")
            return

        last_processed_messages = set()
        while self.is_listening:
            try:
                chat_rows = self.get_chat_rows()
                for chat in chat_rows[:10]:  # İlk 10 sohbeti kontrol et
                    try:
                        # Sadece okunmamış mesajı olan sohbetleri kontrol et
                        unread = False
                        try:
                            # Okunmamış mesaj sayısı olan badge'i bul (güncel seçici)
                            unread_badge = chat.find_element(By.CSS_SELECTOR, 'span[aria-label$="okunmamış mesaj"]')
                            if unread_badge and unread_badge.is_displayed():
                                unread = True
                        except Exception:
                            unread = False
                        if not unread:
                            continue
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chat)
                        chat.click()
                        time.sleep(2)
                        # Mesaj balonlarının yüklenmesini bekle
                        try:
                            self.log("Mesaj balonlarının yüklenmesi bekleniyor...")
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.selectable-text.copyable-text'))
                            )
                            self.log("Mesaj balonları yüklendi.")
                        except Exception as e:
                            self.log(f"Mesaj balonları yüklenemedi: {str(e)[:50]}...")
                        # Son mesajı bul
                        message_bubbles = self.driver.find_elements(By.CSS_SELECTOR, 'span.selectable-text.copyable-text')
                        self.log(f"Bulunan mesaj balonu sayısı: {len(message_bubbles)}")
                        for i, bubble in enumerate(message_bubbles):
                            self.log(f"Mesaj balonu {i}: {bubble.text[:50]}")
                        if message_bubbles:
                            last_message = message_bubbles[-1].text
                            if last_message and last_message not in last_processed_messages:
                                last_processed_messages.add(last_message)
                                self.log(f"Gelen mesaj: {last_message}")
                                if self.auto_reply_enabled and self.auto_reply_message:
                                    self.send_auto_reply(last_message)
                        # Sohbetler listesine geri dön
                        self.go_back_to_chat_list()
                        time.sleep(1)
                    except Exception as e:
                        self.log(f"Sohbet işleme hatası: {str(e)[:100]}...")
                        self.go_back_to_chat_list()
                        continue
                time.sleep(5)
            except Exception as e:
                self.log(f"Dinleme hatası: {str(e)[:100]}...")
                time.sleep(5)

    def on_closing(self):
        try:
            if self.is_listening:
                self.stop_listening()
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    self.log(f"Driver kapatma hatası: {str(e)[:50]}...")
            self.root.destroy()
        except Exception as e:
            self.log(f"Kapatma hatası: {str(e)[:50]}...")
            self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = WhatsAppBotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop() 