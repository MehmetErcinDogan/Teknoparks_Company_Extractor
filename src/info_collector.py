import json
import os
import sys
import time
import gc
from typing import Dict, List
from tqdm import tqdm
from ddgs import DDGS
from playwright.sync_api import sync_playwright
from llama_cpp import Llama


try:
    # 1. Durum: Normal .py dosyası olarak terminalden çalıştırılıyorsa
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    # 2. Durum: Jupyter Notebook içinden çalıştırılıyorsa (__file__ bulunamaz)
    # Jüpiter varsayılan olarak bulunduğu 'src' klasörünü dizin sayar.
    if os.path.basename(os.getcwd()) == 'src':
        ROOT_DIR = os.path.dirname(os.getcwd())
    else:
        ROOT_DIR = os.getcwd()

os.chdir(ROOT_DIR)

# Sadece Jupyter'da çalışıyorsa asenkron yamayı uygula (Pylance hatası vermez)
if 'ipykernel' in sys.modules:
    import nest_asyncio
    nest_asyncio.apply()

# ==========================================
# 1. AYARLAR VE DOSYA YOLLARI
# ==========================================
GIRDI_DOSYASI = 'outputs/companies.json'
CIKTI_DOSYASI = 'outputs/evaluation_output.jsonl'
MODEL_YOLU = 'qwen2.5-3b-q4.gguf'
CV_DOSYASI = 'inputs/benim_cv.txt'
PROMPT_DOSYASI = 'inputs/prompt_sablonu.txt'

def metin_dosyasi_oku(dosya_yolu: str, uyari_mesaji: str) -> str:
    if not os.path.exists(dosya_yolu):
        print(f"UYARI: {dosya_yolu} bulunamadı! {uyari_mesaji}")
        return ""
    with open(dosya_yolu, 'r', encoding='utf-8') as f:
        return f.read().strip()

CV_METNI = metin_dosyasi_oku(CV_DOSYASI, "Lütfen CV'nizi bu dosyaya ekleyin.")
PROMPT_SABLONU = metin_dosyasi_oku(PROMPT_DOSYASI, "Lütfen prompt_sablonu.txt dosyasını oluşturun.")

# ==========================================
# 2. YAPAY ZEKA MOTORU BAŞLATMA
# ==========================================
print("Yapay Zeka Modeli GPU'ya yükleniyor...")
try:
    llm = Llama(model_path=MODEL_YOLU, n_gpu_layers=-1, n_ctx=2048, verbose=False)
    print("Model Yüklendi")
except Exception as e:
    print(f"Model yüklenirken hata oluştu: {e}")
    llm = None

# ==========================================
# 3. KAZIMA (SCRAPING) FONKSİYONLARI
# ==========================================
ddgs = DDGS()

def site_bul(firma_adi: str) -> str | None:
    try:
        sonuclar = list(ddgs.text(f"{firma_adi} resmi site", max_results=3))
        for s in sonuclar:
            url = s.get('href', '')
            if 'linkedin.com' not in url and 'kariyer.net' not in url:
                return url
        return None
    except:
        return None

def ilan_bul(firma_adi: str) -> List[Dict[str, str]]:
    ilanlar = []
    try:
        sorgu = f"site:linkedin.com/jobs/view/ \"{firma_adi}\""
        sonuclar = list(ddgs.text(sorgu, max_results=5))
        for s in sonuclar:
            url = s.get('href', '')
            # Sadece gerçek LinkedIn iş ilanı linklerini filtrele
            if 'linkedin.com/jobs/view' in url or 'linkedin.com/jobs' in url:
                ilanlar.append({
                    "baslik": s.get('title', 'İş İlanı'), 
                    "link": url
                })
    except:
        pass
    return ilanlar

def dinamik_metin_cek(url: str | None) -> str:
    if not url or url.lower() == "link yok":
        return "Web sitesi bilgisi yok."
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            saf_metin = page.evaluate("document.body.innerText")
            if saf_metin:
                temiz_metin = " ".join(str(saf_metin).split())
                return temiz_metin[:1500]
            return "Siteden metin alınamadı."
        except Exception:
            return "Site okunamadı veya zaman aşımına uğradı."
        finally:
            browser.close()

# ==========================================
# 4. ORKESTRATÖR VE ANA DÖNGÜ
# ==========================================
def ana_dongu():
    if not llm or not PROMPT_SABLONU:
        return
        
    if not os.path.exists(GIRDI_DOSYASI):
        print(f"HATA: {GIRDI_DOSYASI} bulunamadı!")
        return

    with open(GIRDI_DOSYASI, 'r', encoding='utf-8') as f:
        sirketler = json.load(f)

    islenmisler = set()
    kullanilan_kategoriler = set()
    
    if os.path.exists(CIKTI_DOSYASI):
        with open(CIKTI_DOSYASI, 'r', encoding='utf-8') as f:
            for satir in f:
                if satir.strip():
                    try:
                        veri = json.loads(satir)
                        islenmisler.add(veri.get("firma"))
                        kategori = veri.get("ai_analizi", {}).get("kategori")
                        if kategori and kategori != "Hata":
                            kullanilan_kategoriler.add(kategori)
                    except:
                        pass

    bekleyenler = [s for s in sirketler if s.get('Firma') not in islenmisler]
    print(f"\nToplam: {len(sirketler)} | İşlenen: {len(islenmisler)} | Kalan: {len(bekleyenler)}")

    with open(CIKTI_DOSYASI, 'a', encoding='utf-8') as dosya:
        for sirket in tqdm(bekleyenler, desc="Şirketler İşleniyor", unit="şirket"):
            firma_adi = sirket.get('Firma', 'Bilinmeyen Firma')
            firma_tanitimi = sirket.get('Tanıtım', 'Belirtilmemiş')
            mevcut_link = sirket.get('Link', '')
            print(f"Firma için başladı:{firma_adi}")
            # 1. Kazıma İşlemi
            if not mevcut_link or mevcut_link.lower() == "link yok":
                mevcut_link = site_bul(firma_adi)
            
            firma_metni = dinamik_metin_cek(mevcut_link)
            
            ilanlar = ilan_bul(firma_adi)
            ilan_metni = "Bulunan İlanlar:\n"
            if ilanlar:
                for idx, ilan in enumerate(ilanlar):
                    ilan_metni += f"[{idx}] İlan: {ilan['baslik']}\n"
            else:
                ilan_metni = "Aktif ilan bulunamadı."
                
            time.sleep(1.5)

            # 2. AI Hazırlığı
            mevcut_kat_str = ", ".join(kullanilan_kategoriler) if kullanilan_kategoriler else "Henüz kategori yok, ilkini sen belirle."
            
            user_prompt = PROMPT_SABLONU.replace("{cv_metni}", CV_METNI) \
                            .replace("{firma_tanitimi}", firma_tanitimi) \
                            .replace("{firma_metni}", firma_metni) \
                            .replace("{ilan_metni}", ilan_metni) \
                            .replace("{mevcut_kategoriler}", mevcut_kat_str)
            
            system_prompt = "Sen bir veri analisti ve İK uzmanısın. SADECE JSON şablonunu doldur. Açıklama yapma."

            # 3. AI Çağrısı
            try:
                response = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=400,
                    stream=False
                )
                
                ai_cevabi = None
                if isinstance(response, dict):
                    choices = response.get("choices", [])
                    if choices and isinstance(choices[0], dict):
                        ai_cevabi = choices[0].get("message", {}).get("content")

                if ai_cevabi:
                    ai_cevabi = ai_cevabi.strip()
                    if ai_cevabi.startswith("```json"):
                        ai_cevabi = ai_cevabi.replace("```json", "", 1).rstrip("`").strip()
                    
                    analiz_sonucu = json.loads(ai_cevabi)
                    
                    # Yeni kategori ekleme
                    yeni_kat = analiz_sonucu.get("kategori")
                    if yeni_kat and yeni_kat not in kullanilan_kategoriler:
                        kullanilan_kategoriler.add(yeni_kat)
                        
                    # İndeks -> Link Çevirisi
                    uygun_indeksler = analiz_sonucu.get("uygun_ilan_indeksleri", [])
                    secilen_linkler = []
                    
                    if isinstance(uygun_indeksler, list):
                        for idx in uygun_indeksler:
                            if isinstance(idx, int) and 0 <= idx < len(ilanlar):
                                secilen_linkler.append(ilanlar[idx]['link'])
                    
                    analiz_sonucu["uygun_ilan_linkleri"] = secilen_linkler
                    analiz_sonucu.pop("uygun_ilan_indeksleri", None)

                else:
                    raise ValueError("Yapay zeka boş yanıt döndürdü.")
                    
            except Exception as e:
                analiz_sonucu = {
                    "kategori": "Hata",
                    "ozet": "AI analizi sırasında hata oluştu.",
                    "uygun_ilan_linkleri": []
                }
                print(f"\n{firma_adi} için AI Hatası: {str(e)}")

            # 4. Kaydetme
            nihai_veri = {
                "firma": firma_adi,
                "site_linki": mevcut_link,
                "ai_analizi": analiz_sonucu
            }
            
            dosya.write(json.dumps(nihai_veri, ensure_ascii=False) + '\n')
            dosya.flush() 
            gc.collect()

    print("\n--- İŞLEM TAMAMLANDI! ---")

if __name__ == "__main__":
    ana_dongu()
