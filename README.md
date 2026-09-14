# AI Destekli Teknopark Firma İnceleyici

Bu proje, İstanbul Teknopark'ta yer alan firmaların bilgilerini web üzerinden çekip, kendi bilgilerim ile eşleştirerek yapay zeka desteğiyle değerlendirmek için geliştirdiğim kişisel bir araçtır.

Kendi spesifik problemimi çözmesi amacıyla script mantığıyla, hızlıca hazırlanmıştır. Çok sistematik veya her web sayfasında %100 çalışacak kusursuz bir yapı hedeflenmemiştir. Ancak benzer bir ihtiyacı olanların işini görebilmesi adına açık kaynak olarak paylaşıyorum.

## Dosya Yapısı

* **`inputs/`**: Kişiselleştirme dosyalarının bulunduğu dizin. Kendi CV'nizi (`benim_cv.txt`) ve modelin kullanacağı prompt şablonunu (`prompt_sablonu.txt`) buradan düzenleyebilirsiniz.

* **`src/`**: Veri çekme, işleme ve dönüştürme işlemlerini yapan ana Python script'leri (`info_collector.py`, `converter.py`) ve Jupyter Notebook (`company_extractor.ipynb`) dosyası.

* **`outputs/`**: İşlem sonucunda üretilen ara dosyalar ve nihai sonuçlar (JSON, HTML ve Excel formatında).

## Kurulum ve Gereksinimler

Projede yerel bir LLM (Büyük Dil Modeli) kullanılmıştır. Boyut kısıtlamaları nedeniyle model dosyası repoya dahil **edilmemiştir**.

1. **Modeli İndirme:** Projeyi kullanabilmek için Hugging Face üzerinden `.gguf` formatında bir model indirmeniz gerekmektedir. Ben kendi bilgisayarımın donanımına ve işin niteliğine uygun bulduğum için **`qwen 2.5-4b-q4`** modelini kullandım. İndirdiğiniz modeli ilgili dizine yerleştirmeniz gerekmektedir.

2. **GPU ve Docker Notu:** Repodaki Dockerfile içerisinde yer alan derleme işlemleri, kullandığım donanımdaki spesifik GPU destek sorunlarını (hazır binary dosyalarının kartımı desteklememesi) çözmek için eklenmiştir. Eğer RTX serisi bir karta sahipseniz veya standart sürümler bilgisayarınızda çalışıyorsa, bu derleme adımını yapmanıza gerek kalmayabilir.

## Kullanım Hakları ve İletişim

* **Lisans:** Bu proje **kesinlikle ticari kullanım için değildir**. Bireysel kullanıma ve geliştirmeye tamamen serbesttir.

* **İletişim:** Geri bildirimde bulunmak isterseniz veya **yeni yapay zeka projeleri hakkında görüşmek isterseniz** bana LinkedIn üzerinden ulaşabilirsiniz: 👉 [linkedin.com/in/MehmetErcinDogan](https://linkedin.com/in/MehmetErcinDogan)