import json
import os
import time
from tqdm import tqdm

GIRDI_DOSYASI = 'companies.json'
CIKTI_DOSYASI = 'sonuclar.jsonl'  # Her satır bir JSON olacak
CV_DOSYASI = 'benim_cv.txt'

def cv_oku():
    if not os.path.exists(CV_DOSYASI):
        print(f"HATA: {CV_DOSYASI} dosyası yok!")
        return ""
    with open(CV_DOSYASI, 'r', encoding='utf-8') as f:
        return f.read().strip()

def ana_dongu():
    cv_metni = cv_oku()
    if not cv_metni: return

    # 1. Girdi listesini oku
    with open(GIRDI_DOSYASI, 'r', encoding='utf-8') as f:
        sirketler = json.load(f)

    # 2. İşlenmiş şirketleri RAM'i yormadan satır satır tespit et
    islenmis_sirketler = set()
    if os.path.exists(CIKTI_DOSYASI):
        with open(CIKTI_DOSYASI, 'r', encoding='utf-8') as f:
            for satir in f:
                if satir.strip():
                    islenmis_sirketler.add(json.loads(satir).get("firma"))

    # 'Firma' etiketine göre filtrele
    bekleyenler = [s for s in sirketler if s.get('Firma') not in islenmis_sirketler]
    print(f"Toplam: {len(sirketler)} | İşlenen: {len(islenmis_sirketler)} | Kalan: {len(bekleyenler)}\n")

    # 3. Ana Döngü: Dosyayı 'append' (ekleme) modunda aç, veriyi RAM'de tutmadan direkt diske yaz
    with open(CIKTI_DOSYASI, 'a', encoding='utf-8') as cikti_dosyasi:
        for sirket in tqdm(bekleyenler, desc="İşleniyor", unit="şirket"):
            firma_adi = sirket.get('Firma')
            tanitim_metni = sirket.get('Tanıtım', '')
            mevcut_link = sirket.get('Link', '')
            
            # --- 2. VE 3. BİLEŞENLER (KAZIMA VE YAPAY ZEKA) BURADA ÇALIŞACAK ---
            time.sleep(0.1) # Sahte işlem süresi (Test için)
            
            # Üretilecek nihai veri yapısı
            sonuc = {
                "firma": firma_adi,
                "kategori": "Test Kategorisi",
                "ozet": "Şirket hakkında üretilen 2 cümlelik özet.",
                "uygun_ilanlar": ["link1", "link2"] # CV ile eşleşen linkler
            }
            # ---------------------------------------------

            # Diske anında yaz ve RAM'den at
            cikti_dosyasi.write(json.dumps(sonuc, ensure_ascii=False) + '\n')
            cikti_dosyasi.flush() # İşletim sistemini diske yazmaya zorlar

    print("\nİşlem tamamlandı!")

if __name__ == "__main__":
    ana_dongu()