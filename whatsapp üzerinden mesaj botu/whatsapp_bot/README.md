# WhatsApp Excel Mesaj Botu - Otomatik Cevap Sistemi

Bu bot, Excel dosyasından numaraları okuyarak toplu mesaj gönderebilir ve gelen mesajlara otomatik cevap verebilir.

## Özellikler

### 📤 Mesaj Gönderme
- Excel dosyasından telefon numaralarını okuma
- Özelleştirilebilir mesaj şablonları
- Toplu mesaj gönderme
- Türkçe telefon numarası formatı desteği

### 🤖 Otomatik Cevap Sistemi
- Gelen mesajları dinleme
- Akıllı cevap sistemi (anahtar kelime bazlı)
- Zaman bazlı cevaplar
- Sabit cevap seçeneği
- Gerçek zamanlı mesaj takibi

## Kurulum

1. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Chrome tarayıcısının yüklü olduğundan emin olun.

## Kullanım

### Mesaj Gönderme
1. "Excel Dosyası Seç" butonuna tıklayın
2. "Mesaj Dosyası Seç" butonuna tıklayın
3. "Numaraları Yükle" butonuna tıklayın
4. "Mesajları Gönder" butonuna tıklayın
5. QR kodu telefonunuzla tarayın

### Otomatik Cevap Sistemi
1. "Otomatik Cevap Aktif" kutusunu işaretleyin
2. Cevap türünü seçin:
   - **Akıllı Cevap**: Mesaj içeriğine göre otomatik cevap
   - **Sabit Cevap**: Her mesaja aynı cevabı gönder
3. "Mesaj Dinlemeyi Başlat" butonuna tıklayın
4. QR kodu telefonunuzla tarayın

## Excel Dosya Formatı

Excel dosyanızda aşağıdaki sütunlar bulunmalıdır:
- **Firma Adı**: İşletme adı
- **Telefon**: Telefon numarası (05, +905 veya 5 ile başlamalı)

## Mesaj Şablonu

Mesaj dosyanızda `{firma_adi}` placeholder'ını kullanabilirsiniz. Bu, her numara için işletme adıyla değiştirilecektir.

Örnek:
```
Merhaba {firma_adi}, 
Emlak hizmetlerimiz hakkında bilgi almak ister misiniz?
```

## Akıllı Cevap Sistemi

Bot, gelen mesajlardaki anahtar kelimelere göre otomatik cevap verir:

- **fiyat** → Fiyat bilgisi için detaylı bilgi ister
- **satılık** → Satılık mülkler hakkında bilgi verir
- **kiralık** → Kiralık mülkler hakkında bilgi verir
- **emlak** → Genel emlak hizmetleri hakkında bilgi verir
- **merhaba/selam** → Selamlama cevabı
- **teşekkür** → Rica ederim cevabı

## Zaman Bazlı Cevaplar

Bot, günün saatine göre farklı cevaplar verir:
- **06:00-12:00**: Günaydın mesajı
- **12:00-18:00**: İyi akşamlar mesajı
- **18:00-06:00**: İyi geceler mesajı

## Güvenlik ve Uyarılar

⚠️ **Önemli Uyarılar:**
- WhatsApp'ın kullanım şartlarına uygun kullanın
- Spam mesaj göndermekten kaçının
- Kişisel verileri koruyun
- Bot kullanımından sorumlu olun

## Sorun Giderme

### Chrome Driver Hatası
- Chrome tarayıcısının güncel olduğundan emin olun
- İnternet bağlantınızı kontrol edin

### QR Kod Tarama
- QR kodu telefonunuzla tarayın
- WhatsApp Web'in açık olduğundan emin olun

### Mesaj Gönderme Hatası
- Numara formatını kontrol edin
- İnternet bağlantınızı kontrol edin
- WhatsApp'ın çalışır durumda olduğundan emin olun

## Teknik Detaylar

- **Python 3.7+** gereklidir
- **Selenium WebDriver** kullanılır
- **Chrome tarayıcısı** gereklidir
- **WhatsApp Web** üzerinden çalışır

## Lisans

Bu proje eğitim amaçlı geliştirilmiştir. Ticari kullanım için gerekli izinleri alın. 