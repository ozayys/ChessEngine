# Satranç Oyunu - İnsan vs Motor

Bu proje, Python ve Pygame kullanarak geliştirilmiş tam özellikli bir satranç oyunudur. İnsan oyuncular beyaz taşlarla oynarken, yapay zeka motoru siyah taşlarla oynar.

## 🎯 Özellikler

### Oyun Özellikleri
- **Tam GUI Desteği**: Pygame ile güzel görsellik
- **Taş Resimleri**: Özel tasarım taş görselleri
- **İnsan vs Motor**: Beyaz taşlarla insan, siyah taşlarla AI
- **Legal Hamle Kontrolü**: Tüm satranç kuralları uygulandı
- **Özel Hamleler**: Rok, en passant, piyon terfisi

### Teknik Özellikler
- **Bitboard Tabanlı**: Yüksek performans için 64-bit bitboard
- **Alpha-Beta Pruning**: Gelişmiş arama algoritması
- **Hamle Sıralama**: Alma hamleleri öncelikli değerlendirme
- **Piece-Square Tables**: Pozisyonel değerlendirme
- **Modüler Yapı**: Temiz, bakımı kolay kod mimarisi

## 📦 Dosya Yapısı

```
/
├── ana.py              # Ana oyun GUI'si
├── Tahta.py            # Bitboard tabanlı tahta sınıfı
├── HamleUret.py        # Pseudo-legal hamle üreticisi
├── LegalHamle.py       # Legal hamle filtreleyici
├── Arama.py            # Alpha-beta arama algoritması
├── Degerlendirme.py    # Pozisyon değerlendirici
├── Zobrist.py          # Hash tablosu (gelecek için)
├── test_proje.py       # Test dosyası
├── taslar/             # Taş resimleri dizini
│   ├── beyazSah.png
│   ├── beyazVezir.png
│   ├── beyazKale.png
│   ├── beyazFil.png
│   ├── beyazAt.png
│   ├── beyazPiyon.png
│   ├── siyahSah.png
│   ├── siyahVezir.png
│   ├── siyahKale.png
│   ├── siyahFil.png
│   ├── siyahAt.png
│   └── siyahPiyon.png
└── README.md           # Bu dosya
```

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.7+
- Pygame

### Kurulum
```bash
# Pygame'i yükleyin
pip install pygame

# Projeyi klonlayın veya indirin
git clone [proje-url]
cd satranc-projesi
```

### Çalıştırma
```bash
# Oyunu başlatın
python3 ana.py

# Testleri çalıştırın (opsiyonel)
python3 test_proje.py
```

## 🎮 Oyun Kontrolleri

### Mouse Kontrolleri
- **Sol Tık**: Taş seçme ve hamle yapma
- **Taş Seçimi**: Beyaz taşa tıklayarak seç
- **Hamle Yapma**: Seçili taşla hedef kareye tıkla
- **Mümkün Hamleler**: Yeşil vurgular mümkün hamleleri gösterir

### Klavye Kontrolleri
- **R**: Oyunu yeniden başlat
- **ESC**: Oyundan çıkış
- **1-9**: Motor derinliğini ayarla (1=kolay, 9=zor)

## 🧠 Motor Özellikleri

### Arama Algoritması
- **Alpha-Beta Pruning**: Optimizasyon ile hızlı arama
- **Değişken Derinlik**: 1-8 seviye arası zorluk
- **Hamle Sıralama**: Alma hamleleri önce değerlendirilir

### Değerlendirme Sistemi
- **Malzeme Değeri**: Standart taş değerleri
- **Piece-Square Tables**: Pozisyonel bonuslar
- **Oyun Fazı Tespiti**: Açılış/orta oyun/son oyun

### Performans
- **Derinlik 3**: ~420 düğüm/hamle (hızlı)
- **Derinlik 4-5**: Orta seviye (önerilen)
- **Derinlik 6+**: Güçlü ama yavaş

## 🔧 Geliştirici Notları

### Bitboard Sistemi
Projede 64-bit integer'lar kullanılarak her taş türü için ayrı bitboard'lar tutulur:
```python
self.beyaz_piyon = 0x000000000000FF00  # Başlangıç pozisyonu
self.siyah_piyon = 0x00FF000000000000
```

### Hamle Formatı
Hamleler tuple formatında saklanır:
```python
(kaynak_kare, hedef_kare, tas_turu, hamle_turu)
# Örnek: (12, 28, 'piyon', 'iki_kare')
```

### Debug Modu
Debug çıktılarını görmek için terminal'den çalıştırın:
```bash
python3 ana.py
```

## 🐛 Bilinen Sorunlar ve Çözümler

### Taş Resimleri Yüklenmezse
- `taslar/` dizininin var olduğundan emin olun
- PNG dosyalarının doğru isimlerde olduğunu kontrol edin
- Resim dosyalarının bozuk olmadığını kontrol edin

### Motor Hamle Yapmıyorsa
- Arama derinliğini düşürün (1-3 arası)
- Terminal çıktılarını kontrol edin
- `test_proje.py` ile temel işlevleri test edin

### Performans Sorunları
- Derinliği düşürün
- Eski donanımlarda derinlik 2-3 kullanın
- Debug çıktılarını kapatmak için kod düzenleyin

## 📈 Gelecek Geliştirmeler

### Planlanan Özellikler
- [ ] Zaman kontrolü
- [ ] Açılış kitabı
- [ ] Son oyun tabloları
- [ ] Multi-threading arama
- [ ] UCI protokol desteği
- [ ] PGN dosya desteği
- [ ] Ses efektleri

### Performans İyileştirmeleri
- [ ] Transposition table
- [ ] Iterative deepening
- [ ] Quiescence search
- [ ] Late move reduction
- [ ] Null move pruning

## 🤝 Katkıda Bulunma

1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'i push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında dağıtılmaktadır.

## 🙏 Teşekkürler

- Pygame topluluğu
- Satranç programlama kaynakları
- Beta test eden arkadaşlar

---

**İyi oyunlar! ♟️**