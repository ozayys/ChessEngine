# Piyon Terfisi Özelliği / Pawn Promotion Feature

## Açıklama / Description

Satranç oyununda bir piyon son sıraya ulaştığında, oyuncu vezir, kale, fil veya at taşlarından birini seçebilir. Bu özellik, görsel ve kullanıcı dostu bir seçim menüsü sunar.

When a pawn reaches the last rank in chess, the player can choose to promote it to a Queen, Rook, Bishop, or Knight. This feature provides a visual and user-friendly selection menu.

## Özellikler / Features

### Görsel Menü / Visual Menu
- **Modern Tasarım**: Yuvarlatılmış köşeler, gölge efektleri ve gradient benzeri görünüm
- **Animasyonlar**: Menü açılırken fade-in animasyonu
- **Hover Efektleri**: Fare ile üzerine gelindiğinde taşlar büyür ve vurgulanır
- **Altın Rengi Vurgulama**: Terfi edecek piyon altın rengiyle parlar

### Kontroller / Controls
- **Fare ile Seçim**: Tıklayarak taş seçimi
- **Klavye Kısayolları**:
  - `Q` veya `1`: Vezir
  - `R` veya `2`: Kale
  - `B` veya `3`: Fil
  - `N` veya `4`: At

### Görsel Detaylar / Visual Details
- Terfi menüsü ekranın ortasında belirir
- Yarı saydam arka plan ile odaklanma sağlanır
- Her taş seçeneği için:
  - Hover durumunda %15 büyüme efekti
  - Altın rengi çerçeve vurgulaması
  - Taş ismi ve klavye kısayolu gösterimi
- Terfi edecek piyon parlayan animasyon ile vurgulanır

## Teknik Detaylar / Technical Details

### Kod Yapısı / Code Structure
```python
# ana.py içinde eklenen özellikler:
- terfi_menusu_ciz(): Görsel menüyü çizer
- terfi_menusu_tikla(): Fare tıklamalarını işler
- terfi_klavye_secimi(): Klavye girişlerini işler
- terfi_hamlesini_yap(): Seçilen taşla terfiyi gerçekleştirir
```

### Animasyon Değişkenleri / Animation Variables
- `terfi_menu_alpha`: Fade-in animasyonu için alpha değeri
- `hover_scale`: Her taş için hover büyütme oranı
- `hover_tas`: Şu anda hover edilen taş

## Kullanım / Usage

1. Oyun sırasında bir piyon son sıraya ulaştığında otomatik olarak terfi menüsü açılır
2. Fare ile istediğiniz taşın üzerine gelin ve tıklayın
3. Veya klavye kısayollarını kullanın (Q/R/B/N veya 1/2/3/4)
4. Seçim yapıldıktan sonra piyon seçilen taşa dönüşür ve oyun devam eder

## Ekran Görüntüsü Açıklaması / Screenshot Description

Menü açıldığında:
- Koyu arka plan üzerinde modern görünümlü bir panel
- "Piyon Terfisi" başlığı
- 4 taş seçeneği yan yana dizilmiş
- Her taşın altında küçük numara göstergesi
- Alt kısımda klavye kısayolları bilgisi
- Terfi edecek piyon altın rengiyle parlar