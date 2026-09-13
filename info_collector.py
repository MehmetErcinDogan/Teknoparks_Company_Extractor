import json
import os
import time
import nest_asyncio
from tqdm import tqdm
from duckduckgo_search import DDGS
from playwright.sync_api import sync_playwright
from llama_cpp import Llama

# Jupyter Notebook'ta asenkron (Playwright) çakışmalarını önlemek için:
nest_asyncio.apply()

# ==========================================
# 1. AYARLAR VE DOSYA YOLLARI
# ==========================================
GIRDI_DOSYASI = 'companies.json'
CIKTI_DOSYASI = 'output_evaluation.jsonl'
MODEL_YOLU = 'qwen2.5-3b-q4.gguf'
CV_DOSYASI = 'benim_cv.txt'

def cv_oku():
    """CV metnini dış dosyadan okur."""
    if not os.path.exists(CV_DOSYASI):
        print(f"UYARI: {CV_DOSYASI} bulunamadı! Lütfen CV'nizi bu dosyaya ekleyin.")
        return "CV verisi girilmedi."
    with open(CV_DOSYASI, 'r', encoding='utf-8') as f:
        return f.read().strip()

CV_METNI = cv_oku()

# ==========================================
# 2. YAPAY ZEKA MOTORU BAŞLATMA
# ==========================================
print("Yapay Zeka Modeli GPU'ya yükleniyor...")
try:
    llm = Llama(model_path=MODEL_YOLU, n_gpu_layers=-1, n_ctx=2048, verbose=False)
except Exception as e:
    print(f"Model yüklenirken hata oluştu: {e}")
    llm = None

# ==========================================
# 3. KAZIMA (SCRAPING) FONKSİYONLARI
# ==========================================
ddgs = DDGS()

def site_bul(firma_adi):
    """Firma adı ile resmi websitesini bulur."""
    try:
        sonuclar = list(ddgs.text(f"{firma_adi} teknopark resmi site", max_results=3))
        for s in sonuclar:
            url = s.get('href', '')
            if 'linkedin.com' not in url and 'kariyer.net' not in url:
                return url
        return None
    except:
        return None

def ilan_bul(firma_adi):
    """DuckDuckGo Dorking ile LinkedIn ilan linklerini bulur."""
    ilanlar = []
    try:
        sorgu = f"site:linkedin.com/jobs/view/ \"{firma_adi}\""
        sonuclar = list(ddgs.text(sorgu, max_results=5))
        for s in sonuclar:
            ilanlar.append({"baslik": s.get('title', ''), "link": s.get('href', '')})
    except:
        pass
    return ilanlar

def dinamik_metin_cek(url):
    """Playwright ile dinamik sitelerden temiz metin çeker."""
    if not url or url.lower() == "link yok":
        return "Web sitesi bilgisi yok."
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            saf_metin = page.evaluate("document.body.innerText")
            temiz_metin = " ".join(saf_metin.split())
            return temiz_metin[:1500] 
        except Exception:
            return "Site okunamadı veya zaman aşımına uğradı."
        finally:
            browser.close()

# ==========================================
# 4. ORKESTRATÖR VE ANA DÖNGÜ
# ==========================================
def ana_dongu():
    if not llm: return
    if not os.path.exists(GIRDI_DOSYASI):
        print(f"HATA: {GIRDI_DOSYASI} bulunamadı!")
        return

    with open(GIRDI_DOSYASI, 'r', encoding='utf-8') as f:
        sirketler = json.load(f)

    # İşlenmiş olanları tespit et (Kaldığı yerden devam etmesi için)
    islenmisler = set()
    if os.path.exists(CIKTI_DOSYASI):
        with open(CIKTI_DOSYASI, 'r', encoding='utf-8') as f:
            for satir in f:
                if satir.strip():
                    try:
                        veri = json.loads(satir)
                        islenmisler.add(veri.get("firma"))
                    except:
                        pass

    bekleyenler = [s for s in sirketler if s.get('Firma') not in islenmisler]
    print(f"\nToplam: {len(sirketler)} | İşlenen: {len(islenmisler)} | Kalan: {len(bekleyenler)}")

    with open(CIKTI_DOSYASI, 'a', encoding='utf-8') as dosya:
        for sirket in tqdm(bekleyenler, desc="Şirketler İşleniyor", unit="şirket"):
            firma_adi = sirket.get('Firma', 'Bilinmeyen Firma')
            mevcut_link = sirket.get('Link', '')

            # 1. Site ve Metin
            if not mevcut_link or mevcut_link.lower() == "link yok":
                mevcut_link = site_bul(firma_adi)
            
            firma_metni = dinamik_metin_cek(mevcut_link)
            
            # 2. İlanları Bul
            ilanlar = ilan_bul(firma_adi)
            ilan_metni = "Bulunan İlanlar:\n" + "\n".join([i['baslik'] for i in ilanlar]) if ilanlar else "Aktif ilan bulunamadı."
            time.sleep(1.5) # DDGS arama limiti koruması

            # 3. Yapay Zeka Analizi
            system_prompt = "Sen analitik bir İK asistanısın. SADECE JSON formatında çıktı ver."
            user_prompt = f"""
Kullanıcı CV Özeti:
{CV_METNI}

Firma Hakkında (Web Sitesinden):
{firma_metni}

{ilan_metni}

GÖREVLER:
1. "kategori": Firmayı aşağıdaki listeden EN UYGUN OLANINA ata. Yeni kategori uydurma.
   Liste: [Gömülü Sistemler ve Donanım, Savunma Sanayi, Yazılım Teknolojileri, Yapay Zeka ve Veri Analitiği, Biyomedikal ve Sağlık, Enerji ve Otomotiv, Telekomünikasyon, Diğer]
2. "ozet": Şirketin web sitesi metnine bakarak ne iş yaptığını en fazla 3 cümleyle özetle.
3. "uygun_ilanlar": "Bulunan İlanlar" listesindeki iş ilanlarını kullanıcının CV'si ile karşılaştır. SADECE kullanıcının yetkinliklerine uyan ilanların linklerini liste halinde ver. Uyan ilan yoksa veya ilan listesi boşsa [] döndür.

İstenen JSON Çıktısı:
{{
  "kategori": "Seçilen Kategori",
  "ozet": "Şirket özeti...",
  "uygun_ilanlar": ["link1", "link2"]
}}
"""
            try:
                response = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=400
                )
                
                ai_cevabi = response["choices"][0]["message"]["content"].strip()
                if ai_cevabi.startswith("```json"):
                    ai_cevabi = ai_cevabi.replace("```json", "", 1).rstrip("`").strip()
                
                analiz_sonucu = json.loads(ai_cevabi)
            except Exception as e:
                analiz_sonucu = {
                    "kategori": "Hata",
                    "ozet": "AI analizi sırasında hata oluştu.",
                    "cv_uyum_durumu": False,
                    "uyum_aciklamasi": str(e)
                }

            # 4. Veriyi kaydet
            nihai_veri = {
                "firma": firma_adi,
                "site_linki": mevcut_link,
                "ai_analizi": analiz_sonucu,
                "ilan_linkleri": [i['link'] for i in ilanlar]
            }
            
            dosya.write(json.dumps(nihai_veri, ensure_ascii=False) + '\n')
            dosya.flush() 

    print("\n--- İŞLEM TAMAMLANDI! ---")
    print(f"Sonuçlar '{CIKTI_DOSYASI}' dosyasına kaydedildi.")

if __name__ == "__main__":
    ana_dongu()