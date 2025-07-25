# Satranç Motoru

Pygame tabanlı, bitboard mimarisi kullanan güçlü bir satranç motoru ve GUI uygulaması.

## Özellikler

### Motor Özellikleri
- **Alpha-Beta Pruning**: Optimize edilmiş arama algoritması
- **Transposition Table**: Pozisyon önbellekleme (32MB varsayılan)
- **Iterative Deepening**: Derinlik bazlı kademeli arama
- **Quiescence Search**: Sakin pozisyon araması
- **Move Ordering**: 
  - MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
  - Killer Moves
  - History Heuristic
- **Zobrist Hashing**: Hızlı pozisyon karşılaştırma
- **Bitboard Mimarisi**: 64-bit integer tabanlı hızlı tahta temsili

### Değerlendirme Sistemi
- Malzeme değerlendirmesi
- Piece-Square Tables (PST)
- Mobilite analizi
- Şah güvenliği
- Piyon yapısı değerlendirmesi
- Oyun fazı tespiti (açılış/orta oyun/son oyun)

### GUI Özellikleri
- Modern ve kullanıcı dostu arayüz
- Hamle vurgulama
- Legal hamle gösterimi
- Piyon terfisi menüsü
- Değerlendirme skoru gösterimi
- Hamle sayacı ve düşünme süresi

## Kurulum

```bash
# Gerekli kütüphaneleri yükleyin
pip install pygame

# Oyunu başlatın
python3 ana.py
```

## Kullanım

- Sol tık ile taş seçin ve hedef kareye tıklayarak hamle yapın
- Motor otomatik olarak siyah taşları oynar
- ESC tuşu ile çıkış
- R tuşu ile oyunu yeniden başlatın

## Performans Optimizasyonları

### Arama Optimizasyonları
1. **Transposition Table**: Aynı pozisyonların tekrar değerlendirilmesini önler
2. **Killer Moves**: İyi hamleleri hatırlar ve öncelikli olarak dener
3. **History Heuristic**: Geçmişte iyi sonuç veren hamleleri önceliklendirir
4. **Move Ordering**: Hamleleri en olası iyiden kötüye sıralar

### Değerlendirme Optimizasyonları
1. **Evaluation Cache**: Değerlendirme sonuçlarını önbellekler
2. **Lazy Evaluation**: Büyük malzeme farkında detaylı değerlendirme yapmaz
3. **Incremental Zobrist**: Hash değerini artımlı olarak günceller

### Veri Yapısı Optimizasyonları
1. **Bitboards**: Hızlı bit operasyonları ile tahta işlemleri
2. **Precalculated Masks**: Sık kullanılan maskeleri önceden hesaplar
3. **Fast Copy**: Tahta kopyalama için optimize edilmiş metod

## Teknik Detaylar

### Arama Derinliği
- Varsayılan: 6 ply
- Quiescence search ile efektif derinlik daha fazla
- Zaman limiti: Hamle başına 3 saniye

### Değerlendirme Ağırlıkları
- Piyon: 100
- At: 320
- Fil: 330
- Kale: 500
- Vezir: 900

## Test

Mat hesaplama testlerini çalıştırmak için:

```bash
python3 test_mat.py
```

## Lisans

Bu proje açık kaynak kodludur ve eğitim amaçlı kullanılabilir.