#include "Oyun.h"
#include "Arayuz.h"
#include <iostream>

// Yapıcı
Oyun::Oyun() 
    : durum(OyunDurumu::DEVAM),
      beyazOyuncu(OyuncuTuru::INSAN, Renk::BEYAZ, "Beyaz"),
      siyahOyuncu(OyuncuTuru::BILGISAYAR, Renk::SIYAH, "Siyah"),
      motorDusunuyor(false),
      arayuz(nullptr) {
    
    motor = std::make_unique<AramaMotoru>(ayarlar.ttBoyutMB);
}

// Yıkıcı
Oyun::~Oyun() {
    motoruDurdur();
}

// Yeni oyun başlat
void Oyun::yeniOyun() {
    tahta.baslangicPozisyonu();
    hamleGecmisi.clear();
    fenGecmisi.clear();
    fenGecmisi.push_back(tahta.fenAl());
    durum = OyunDurumu::DEVAM;
    
    oyunBaslangic = std::chrono::steady_clock::now();
    beyazKalanSure = std::chrono::minutes(ayarlar.beyazSure);
    siyahKalanSure = std::chrono::minutes(ayarlar.siyahSure);
    
    // Motor beyazsa ilk hamleyi yap
    if (beyazOyuncu.tur == OyuncuTuru::BILGISAYAR) {
        motoruBaslat();
    }
}

// FEN'den başlat
void Oyun::fendenBaslat(const std::string& fen) {
    tahta.fenKur(fen);
    hamleGecmisi.clear();
    fenGecmisi.clear();
    fenGecmisi.push_back(tahta.fenAl());
    durum = OyunDurumu::DEVAM;
    
    // Durumu kontrol et
    durumKontrol();
}

// Ayarları yap
void Oyun::ayarlariYap(const OyunAyarlari& yeniAyarlar) {
    ayarlar = yeniAyarlar;
    motor = std::make_unique<AramaMotoru>(ayarlar.ttBoyutMB);
}

// Oyuncu ayarla
void Oyun::oyuncuAyarla(Renk renk, OyuncuTuru tur, const std::string& isim) {
    if (renk == Renk::BEYAZ) {
        beyazOyuncu.tur = tur;
        beyazOyuncu.isim = isim.empty() ? "Beyaz" : isim;
    } else {
        siyahOyuncu.tur = tur;
        siyahOyuncu.isim = isim.empty() ? "Siyah" : isim;
    }
}

// Hamle yap
bool Oyun::hamleYap(const Hamle& hamle) {
    // Oyun bitti mi?
    if (oyunBittiMi()) return false;
    
    // Legal mi?
    if (!tahta.legalMi(hamle)) return false;
    
    // Hamle yap
    tahta.hamleYap(hamle);
    
    // Hamle kaydet
    hamleKaydet(hamle);
    
    // Durum kontrol
    durum = durumKontrol();
    
    // Arayüze bildir
    if (arayuz) {
        arayuz->hamleEkle(hamle, hamleNotasyonu(hamle));
    }
    
    // Oyun bittiyse
    if (oyunBittiMi()) {
        if (arayuz) {
            arayuz->oyunSonuBildir(sonucMetni());
        }
        return true;
    }
    
    // Sıra motordaysa hamle yaptır
    Oyuncu& aktifOyuncu = (tahta.getSira() == Renk::BEYAZ) ? beyazOyuncu : siyahOyuncu;
    if (aktifOyuncu.tur == OyuncuTuru::BILGISAYAR) {
        motoruBaslat();
    }
    
    return true;
}

// Hamle yap (kare indeksleriyle)
bool Oyun::hamleYap(int kaynak, int hedef, TasTuru terfiTasi) {
    // Legal hamleleri al
    HamleListesi legalHamleler = legalHamleleriAl(kaynak);
    
    // Eşleşen hamleyi bul
    for (const Hamle& hamle : legalHamleler) {
        if (hamle.hedef == hedef) {
            if (hamle.tur == HamleTuru::TERFI || hamle.tur == HamleTuru::TERFI_ALMA) {
                if (hamle.terfiTasi == terfiTasi) {
                    return hamleYap(hamle);
                }
            } else {
                return hamleYap(hamle);
            }
        }
    }
    
    return false;
}

// Motor başlat
void Oyun::motoruBaslat() {
    if (motorDusunuyor) return;
    
    motorDusunuyor = true;
    
    // Motor thread'i başlat
    motorSonucu = std::async(std::launch::async, [this]() {
        motorDusun();
        return Hamle();
    });
}

// Motor durdur
void Oyun::motoruDurdur() {
    if (motorDusunuyor && motor) {
        motor->aramaDurdur();
        if (motorSonucu.valid()) {
            motorSonucu.wait();
        }
        motorDusunuyor = false;
    }
}

// Motor hazır mı?
bool Oyun::motorHazirMi() {
    if (!motorDusunuyor) return false;
    
    return motorSonucu.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready;
}

// Motor hamlesini al
void Oyun::motorHamlesiniAl() {
    if (!motorHazirMi()) return;
    
    Hamle hamle = motorSonucu.get();
    motorDusunuyor = false;
    
    if (hamle.kaynak != hamle.hedef) {
        hamleYap(hamle);
    }
}

// Motor düşün
void Oyun::motorDusun() {
    // Süre hesapla
    Renk renk = tahta.getSira();
    auto kalanSure = kalanSure(renk);
    
    int derinlik = ayarlar.motorDerinlik;
    std::chrono::milliseconds dusunmeSuresi(5000); // 5 saniye varsayılan
    
    // Arayüze bilgi gönder
    if (arayuz) {
        arayuz->motorBilgisiGuncelle(0, 0, 0, "Düşünüyor...");
    }
    
    // En iyi hamleyi bul
    Hamle enIyiHamle = motor->enIyiHamleyiBul(tahta, derinlik, dusunmeSuresi);
    
    // İstatistikleri al
    auto stats = motor->getIstatistikler();
    
    // Arayüze bilgi gönder
    if (arayuz) {
        arayuz->motorBilgisiGuncelle(derinlik, 0, stats.dugumSayisi, 
                                    enIyiHamle.notasyon());
    }
    
    // Hamleyi döndür
    motorSonucu = std::async(std::launch::deferred, [enIyiHamle]() {
        return enIyiHamle;
    });
}

// Durum kontrol
OyunDurumu Oyun::durumKontrol() {
    // Legal hamle var mı?
    if (!legalHamlelerVar()) {
        if (tahta.sahCekildiMi(tahta.getSira())) {
            return OyunDurumu::MAT;
        } else {
            return OyunDurumu::PAT;
        }
    }
    
    // 50 hamle kuralı
    if (elliHamleKuraliMi()) {
        return OyunDurumu::BERABERE_50_HAMLE;
    }
    
    // 3 tekrar
    if (berabereTekrariMi()) {
        return OyunDurumu::BERABERE_TEKRAR;
    }
    
    // Yetersiz materyal
    if (yetersizMateryalMi()) {
        return OyunDurumu::BERABERE_YETERSIZ_MATERYAL;
    }
    
    return OyunDurumu::DEVAM;
}

// Legal hamleler var mı?
bool Oyun::legalHamlelerVar() const {
    HamleListesi hamleler;
    HamleUretici::tumHamleleriUret(tahta, hamleler);
    
    // Her hamleyi kontrol et
    Tahta tmpTahta = tahta;
    for (const Hamle& hamle : hamleler) {
        tmpTahta.hamleYap(hamle);
        bool legal = !tmpTahta.sahCekildiMi(tersRenk(tmpTahta.getSira()));
        tmpTahta.hamleGeriAl(hamle);
        
        if (legal) return true;
    }
    
    return false;
}

// Legal hamleleri al
HamleListesi Oyun::legalHamleleriAl() const {
    HamleListesi tumHamleler, legalHamleler;
    HamleUretici::tumHamleleriUret(tahta, tumHamleler);
    
    Tahta tmpTahta = tahta;
    for (const Hamle& hamle : tumHamleler) {
        tmpTahta.hamleYap(hamle);
        if (!tmpTahta.sahCekildiMi(tersRenk(tmpTahta.getSira()))) {
            legalHamleler.ekle(hamle);
        }
        tmpTahta.hamleGeriAl(hamle);
    }
    
    return legalHamleler;
}

// Belirli bir kareden legal hamleleri al
HamleListesi Oyun::legalHamleleriAl(int kare) const {
    HamleListesi tumHamleler, legalHamleler;
    HamleUretici::tumHamleleriUret(tahta, tumHamleler);
    
    Tahta tmpTahta = tahta;
    for (const Hamle& hamle : tumHamleler) {
        if (hamle.kaynak == kare) {
            tmpTahta.hamleYap(hamle);
            if (!tmpTahta.sahCekildiMi(tersRenk(tmpTahta.getSira()))) {
                legalHamleler.ekle(hamle);
            }
            tmpTahta.hamleGeriAl(hamle);
        }
    }
    
    return legalHamleler;
}

// Sonuç metni
std::string Oyun::sonucMetni() const {
    switch (durum) {
        case OyunDurumu::MAT:
            return (tahta.getSira() == Renk::BEYAZ) ? "Siyah Kazandı (Mat)" : "Beyaz Kazandı (Mat)";
        case OyunDurumu::PAT:
            return "Berabere (Pat)";
        case OyunDurumu::BERABERE_TEKRAR:
            return "Berabere (3 Tekrar)";
        case OyunDurumu::BERABERE_50_HAMLE:
            return "Berabere (50 Hamle Kuralı)";
        case OyunDurumu::BERABERE_YETERSIZ_MATERYAL:
            return "Berabere (Yetersiz Materyal)";
        case OyunDurumu::ZAMAN_BITTI:
            return (tahta.getSira() == Renk::BEYAZ) ? "Siyah Kazandı (Zaman)" : "Beyaz Kazandı (Zaman)";
        default:
            return "Devam Ediyor";
    }
}

// Hamle kaydet
void Oyun::hamleKaydet(const Hamle& hamle) {
    hamleGecmisi.push_back(hamle);
    fenGecmisi.push_back(tahta.fenAl());
    
    // Zaman güncelle
    sureGuncelle();
}

// 3 tekrar kontrolü
bool Oyun::berabereTekrariMi() const {
    if (fenGecmisi.size() < 9) return false;
    
    std::string suankiFen = tahta.fenAl();
    int tekrar = 0;
    
    // Son hamlelerde aynı pozisyon var mı?
    for (int i = fenGecmisi.size() - 4; i >= 0; i -= 2) {
        if (fenGecmisi[i].substr(0, fenGecmisi[i].find(' ')) == 
            suankiFen.substr(0, suankiFen.find(' '))) {
            tekrar++;
            if (tekrar >= 2) return true; // Toplam 3 tekrar
        }
    }
    
    return false;
}

// 50 hamle kuralı
bool Oyun::elliHamleKuraliMi() const {
    return tahta.getElliHamleKurali() >= 100;
}

// Yetersiz materyal
bool Oyun::yetersizMateryalMi() const {
    // Sadece şahlar kaldıysa
    int toplamTas = 0;
    for (int renk = 0; renk < 2; renk++) {
        for (int tas = 0; tas < 5; tas++) { // Şah hariç
            toplamTas += BitboardYardimci::bitSayisi(
                tahta.getBitboard(static_cast<Renk>(renk), static_cast<TasTuru>(tas))
            );
        }
    }
    
    if (toplamTas == 0) return true;
    
    // Şah + fil veya şah + at
    if (toplamTas == 1) {
        // Sadece bir fil veya at varsa
        int filSayisi = BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::BEYAZ, TasTuru::FIL)) +
                        BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::SIYAH, TasTuru::FIL));
        int atSayisi = BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::BEYAZ, TasTuru::AT)) +
                       BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::SIYAH, TasTuru::AT));
        
        if (filSayisi == 1 || atSayisi == 1) return true;
    }
    
    return false;
}

// Hamle notasyonu
std::string Oyun::hamleNotasyonu(const Hamle& hamle) const {
    // Basit notasyon
    return hamle.notasyon();
}

// Süre güncelle
void Oyun::sureGuncelle() {
    auto simdi = std::chrono::steady_clock::now();
    auto gecen = std::chrono::duration_cast<std::chrono::milliseconds>(simdi - hamleBaslangic);
    
    if (tahta.getSira() == Renk::SIYAH) { // Beyaz hamle yaptı
        beyazKalanSure -= gecen;
        if (ayarlar.ekSure > 0) {
            beyazKalanSure += std::chrono::seconds(ayarlar.ekSure);
        }
    } else { // Siyah hamle yaptı
        siyahKalanSure -= gecen;
        if (ayarlar.ekSure > 0) {
            siyahKalanSure += std::chrono::seconds(ayarlar.ekSure);
        }
    }
    
    hamleBaslangic = simdi;
}

// Kalan süre
std::chrono::milliseconds Oyun::kalanSure(Renk renk) const {
    return renk == Renk::BEYAZ ? beyazKalanSure : siyahKalanSure;
}

// Hamle geri al
void Oyun::hamleGeriAl() {
    if (hamleGecmisi.empty()) return;
    
    // Motor çalışıyorsa durdur
    motoruDurdur();
    
    // Son hamleyi geri al
    Hamle sonHamle = hamleGecmisi.back();
    tahta.hamleGeriAl(sonHamle);
    
    hamleGecmisi.pop_back();
    fenGecmisi.pop_back();
    
    // Durum güncelle
    durum = OyunDurumu::DEVAM;
    
    // Arayüze bildir
    if (arayuz) {
        // Hamle geçmişini güncelle
    }
}