import time
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from urllib.parse import urljoin

class SirketKaziyici:
    def __init__(self):
        self.ddgs = DDGS()
        # Web sitelerine bağlanırken bot gibi görünmemek için tarayıcı başlığı ekliyoruz
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def sirket_sitesini_bul(self, firma_adi):
        """DuckDuckGo üzerinden şirketin resmi web sitesini bulur."""
        try:
            sorgu = f"{firma_adi} resmi site"
            sonuclar = list(self.ddgs.text(sorgu, max_results=3))
            
            # Bulunan ilk mantıklı URL'yi döndür (LinkedIn vs değilse)
            for sonuc in sonuclar:
                url = sonuc.get('href', '')
                if 'linkedin.com' not in url and 'kariyer.net' not in url:
                    return url
            return None
        except Exception as e:
            print(f"Site arama hatası ({firma_adi}): {e}")
            return None

    def metni_temizle(self, html_icerik):
        """HTML içindeki gereksiz menü, footer ve scriptleri atıp saf metni alır."""
        soup = BeautifulSoup(html_icerik, 'lxml')
        
        # Gereksiz etiketleri HTML'den sil
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
            
        # Paragraf (<p>) ve başlıkları topla (En değerli veriler buradadır)
        metin_parcalari = []
        for etiket in soup.find_all(['p', 'h1', 'h2', 'h3', 'span']):
            text = etiket.get_text(strip=True)
            if len(text) > 20: # Çok kısa (menü linki vb) metinleri alma
                metin_parcalari.append(text)
                
        # Yapay zekanın RAM'ini taşırmamak için ilk 1500 karakteri (yaklaşık 200 kelime) al
        saf_metin = " ".join(metin_parcalari)
        return saf_metin[:1500]

    def hakkimizda_metni_cek(self, url):
        """Web sitesine girer ve içerik metnini çeker."""
        if not url:
            return "Web sitesi bulunamadı."
            
        try:
            # Ana sayfaya istek at
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return "Siteye erişilemedi."
                
            ana_sayfa_metni = self.metni_temizle(response.text)
            
            # Eğer ana sayfada çok az bilgi varsa, 'hakkımızda' sayfasını aramayı deneyebiliriz
            # Şimdilik sadece ana sayfa içeriğini döndürüyoruz (Hızı artırmak için)
            return ana_sayfa_metni
            
        except Exception as e:
            return f"Sayfa çekme hatası: {e}"

    def is_ilanlarini_bul(self, firma_adi):
        """LinkedIn girişine takılmadan açık iş ilanlarını arar."""
        ilan_linkleri = []
        try:
            # Sadece LinkedIn Jobs sayfalarında bu şirketi aratıyoruz
            sorgu = f"site:linkedin.com/jobs/view/ \"{firma_adi}\""
            sonuclar = list(self.ddgs.text(sorgu, max_results=5))
            
            for sonuc in sonuclar:
                link = sonuc.get('href')
                baslik = sonuc.get('title')
                if link and 'linkedin.com/jobs' in link:
                    # Sadece başlığı ve linki sözlük olarak tut
                    ilan_linkleri.append({
                        "baslik": baslik,
                        "link": link
                    })
        except Exception as e:
            print(f"İlan arama hatası ({firma_adi}): {e}")
            
        return ilan_linkleri

    def sirketi_analiz_et(self, firma_adi):
        """Tüm adımları tek bir fonksiyonda birleştirir."""
        site_url = self.sirket_sitesini_bul(firma_adi)
        time.sleep(2) # IP banı yememek için DuckDuckGo'ya nefes aldırıyoruz
        
        firma_metni = self.hakkimizda_metni_cek(site_url)
        
        ilanlar = self.is_ilanlarini_bul(firma_adi)
        time.sleep(2) # Tekrar nefes aldırıyoruz
        
        return {
            "site_url": site_url,
            "firma_metni": firma_metni,
            "ilanlar": ilanlar
        }

# --- TEST KODU ---
if __name__ == "__main__":
    kaziyici = SirketKaziyici()
    test_firma = "Aselsan" # Buraya json'daki herhangi bir şirketi yazabilirsiniz
    
    print(f"'{test_firma}' için internette arama yapılıyor...")
    sonuc = kaziyici.sirketi_analiz_et(test_firma)
    
    print("\n--- BULUNAN SİTE ---")
    print(sonuc['site_url'])
    print("\n--- ÇEKİLEN METİN (İlk 500 Karakter) ---")
    print(sonuc['firma_metni'][:500] + "...")
    print("\n--- BULUNAN İŞ İLANLARI ---")
    for ilan in sonuc['ilanlar']:
        print(f"- {ilan['baslik']}\n  Link: {ilan['link']}")