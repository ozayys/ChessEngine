#include "Degerlendirici.h"
#include "Tahta.h"
#include "HamleUretici.h"

// Statik değişken tanımlamaları
bool Degerlendirici::tablolarBaslatildi = false;
std::array<std::array<int, 64>, 6> Degerlendirici::ortaOyunPST[2];
std::array<std::array<int, 64>, 6> Degerlendirici::sonOyunPST[2];
std::array<int, 64> Degerlendirici::gecerPiyonBonus;
std::array<int, 64> Degerlendirici::izolePiyonCeza;
std::array<int, 64> Degerlendirici::geriPiyonCeza;
std::array<int, 64> Degerlendirici::ciftPiyonCeza;

// Piece-Square tabloları (orta oyun)
static const int PIYON_PST_ORTA[64] = {
      0,  0,  0,  0,  0,  0,  0,  0,
     50, 50, 50, 50, 50, 50, 50, 50,
     10, 10, 20, 30, 30, 20, 10, 10,
      5,  5, 10, 25, 25, 10,  5,  5,
      0,  0,  0, 20, 20,  0,  0,  0,
      5, -5,-10,  0,  0,-10, -5,  5,
      5, 10, 10,-20,-20, 10, 10,  5,
      0,  0,  0,  0,  0,  0,  0,  0
};

static const int AT_PST_ORTA[64] = {
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
};

static const int FIL_PST_ORTA[64] = {
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
};

static const int KALE_PST_ORTA[64] = {
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
};

static const int VEZIR_PST_ORTA[64] = {
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
};

static const int SAH_PST_ORTA[64] = {
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
};

// Tablo başlatma
void Degerlendirici::tablolariBaslat() {
    if (tablolarBaslatildi) return;
    
    // Beyaz için PST
    for (int kare = 0; kare < 64; kare++) {
        ortaOyunPST[0][0][kare] = PIYON_PST_ORTA[kare];
        ortaOyunPST[0][1][kare] = AT_PST_ORTA[kare];
        ortaOyunPST[0][2][kare] = FIL_PST_ORTA[kare];
        ortaOyunPST[0][3][kare] = KALE_PST_ORTA[kare];
        ortaOyunPST[0][4][kare] = VEZIR_PST_ORTA[kare];
        ortaOyunPST[0][5][kare] = SAH_PST_ORTA[kare];
        
        // Son oyun için aynı değerleri kullan (basitleştirme için)
        sonOyunPST[0][0][kare] = PIYON_PST_ORTA[kare];
        sonOyunPST[0][1][kare] = AT_PST_ORTA[kare];
        sonOyunPST[0][2][kare] = FIL_PST_ORTA[kare];
        sonOyunPST[0][3][kare] = KALE_PST_ORTA[kare];
        sonOyunPST[0][4][kare] = VEZIR_PST_ORTA[kare];
        sonOyunPST[0][5][kare] = SAH_PST_ORTA[kare];
    }
    
    // Siyah için PST (ters çevir)
    for (int kare = 0; kare < 64; kare++) {
        int tersKare = kare ^ 56; // Satırı ters çevir
        for (int tas = 0; tas < 6; tas++) {
            ortaOyunPST[1][tas][kare] = ortaOyunPST[0][tas][tersKare];
            sonOyunPST[1][tas][kare] = sonOyunPST[0][tas][tersKare];
        }
    }
    
    // Piyon değerlendirme tabloları
    for (int kare = 0; kare < 64; kare++) {
        int satir = satirIndeksi(kare);
        int sutun = sutunIndeksi(kare);
        
        // Geçer piyon bonusu (satıra göre artar)
        gecerPiyonBonus[kare] = satir * satir * 5;
        
        // İzole piyon cezası
        izolePiyonCeza[kare] = -20;
        
        // Geri piyon cezası
        geriPiyonCeza[kare] = -15;
        
        // Çift piyon cezası
        ciftPiyonCeza[kare] = -10;
    }
    
    tablolarBaslatildi = true;
}

// Statik başlatıcı
static struct DegerlendiriciBaslatici {
    DegerlendiriciBaslatici() {
        Degerlendirici::tablolariBaslat();
    }
} degerlendiriciBaslatici;

// Ana değerlendirme fonksiyonu
int Degerlendirici::degerlendir(const Tahta& tahta) {
    int skor = 0;
    
    // Materyal değerlendirmesi
    skor += materyalDegerlendir(tahta);
    
    // Pozisyonel değerlendirme
    skor += pozisyonelDegerlendir(tahta);
    
    // Piyon yapısı
    skor += piyonYapisiDegerlendir(tahta);
    
    // Mobilite
    skor += mobiliteDeğerlendir(tahta);
    
    // Şah güvenliği
    skor += sahGuvenligiDegerlendir(tahta);
    
    // Sıranın kimde olduğuna göre işaret değiştir
    return tahta.getSira() == Renk::BEYAZ ? skor : -skor;
}

// Materyal değerlendirmesi
int Degerlendirici::materyalDegerlendir(const Tahta& tahta) {
    int skor = 0;
    
    for (int tas = 0; tas < 6; tas++) {
        int beyazSayisi = BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::BEYAZ, static_cast<TasTuru>(tas)));
        int siyahSayisi = BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::SIYAH, static_cast<TasTuru>(tas)));
        
        skor += (beyazSayisi - siyahSayisi) * ORTA_OYUN_TAS_DEGERLERI[tas];
    }
    
    return skor;
}

// Pozisyonel değerlendirme
int Degerlendirici::pozisyonelDegerlendir(const Tahta& tahta) {
    int skor = 0;
    OyunEvresi evre = oyunEvresiBelirle(tahta);
    
    // Her taş için PST değerleri
    for (int renk = 0; renk < 2; renk++) {
        int renkCarpani = (renk == 0) ? 1 : -1;
        
        for (int tas = 0; tas < 6; tas++) {
            Bitboard taslar = tahta.getBitboard(static_cast<Renk>(renk), static_cast<TasTuru>(tas));
            
            while (taslar) {
                int kare = BitboardYardimci::enDusukBitIndeksi(taslar);
                int pstDeger = 0;
                
                if (evre == OyunEvresi::ACILIS || evre == OyunEvresi::ORTA_OYUN) {
                    pstDeger = ortaOyunPST[renk][tas][kare];
                } else {
                    pstDeger = sonOyunPST[renk][tas][kare];
                }
                
                skor += renkCarpani * pstDeger;
            }
        }
    }
    
    return skor;
}

// Piyon yapısı değerlendirme
int Degerlendirici::piyonYapisiDegerlendir(const Tahta& tahta) {
    int skor = 0;
    
    // Beyaz piyonlar
    Bitboard beyazPiyonlar = tahta.getBitboard(Renk::BEYAZ, TasTuru::PIYON);
    Bitboard siyahPiyonlar = tahta.getBitboard(Renk::SIYAH, TasTuru::PIYON);
    
    // Geçer piyonlar
    Bitboard beyazGecerler = gecerPiyonlar(tahta, Renk::BEYAZ);
    Bitboard siyahGecerler = gecerPiyonlar(tahta, Renk::SIYAH);
    
    while (beyazGecerler) {
        int kare = BitboardYardimci::enDusukBitIndeksi(beyazGecerler);
        skor += gecerPiyonBonus[kare];
    }
    
    while (siyahGecerler) {
        int kare = BitboardYardimci::enDusukBitIndeksi(siyahGecerler);
        skor -= gecerPiyonBonus[kare ^ 56]; // Siyah için ters çevir
    }
    
    // İzole piyonlar
    Bitboard beyazIzoleler = izolePiyonlar(tahta, Renk::BEYAZ);
    Bitboard siyahIzoleler = izolePiyonlar(tahta, Renk::SIYAH);
    
    skor += BitboardYardimci::bitSayisi(beyazIzoleler) * (-20);
    skor -= BitboardYardimci::bitSayisi(siyahIzoleler) * (-20);
    
    return skor;
}

// Mobilite değerlendirme
int Degerlendirici::mobiliteDeğerlendir(const Tahta& tahta) {
    int skor = 0;
    
    // Basit mobilite: legal hamle sayısı
    HamleListesi beyazHamleler, siyahHamleler;
    
    // Geçici olarak sırayı değiştir
    Tahta tmpTahta = tahta;
    
    if (tahta.getSira() == Renk::BEYAZ) {
        HamleUretici::tumHamleleriUret(tmpTahta, beyazHamleler);
        tmpTahta.setSira(Renk::SIYAH);
        HamleUretici::tumHamleleriUret(tmpTahta, siyahHamleler);
    } else {
        HamleUretici::tumHamleleriUret(tmpTahta, siyahHamleler);
        tmpTahta.setSira(Renk::BEYAZ);
        HamleUretici::tumHamleleriUret(tmpTahta, beyazHamleler);
    }
    
    skor += (beyazHamleler.getBoyut() - siyahHamleler.getBoyut()) * 2;
    
    return skor;
}

// Şah güvenliği değerlendirme
int Degerlendirici::sahGuvenligiDegerlendir(const Tahta& tahta) {
    int skor = 0;
    
    // Basit şah güvenliği: rok yapıldı mı?
    if (!tahta.kisaRokYapabilirMi(Renk::BEYAZ) && !tahta.uzunRokYapabilirMi(Renk::BEYAZ)) {
        // Beyaz rok yaptı
        skor += 20;
    }
    
    if (!tahta.kisaRokYapabilirMi(Renk::SIYAH) && !tahta.uzunRokYapabilirMi(Renk::SIYAH)) {
        // Siyah rok yaptı
        skor -= 20;
    }
    
    return skor;
}

// Oyun evresi belirleme
OyunEvresi Degerlendirici::oyunEvresiBelirle(const Tahta& tahta) {
    int toplamMateryal = 0;
    
    // Vezir ve kale sayısı
    int vezirSayisi = BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::BEYAZ, TasTuru::VEZIR)) +
                      BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::SIYAH, TasTuru::VEZIR));
    
    int kaleSayisi = BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::BEYAZ, TasTuru::KALE)) +
                     BitboardYardimci::bitSayisi(tahta.getBitboard(Renk::SIYAH, TasTuru::KALE));
    
    // Açılış: Çok fazla taş var
    if (vezirSayisi == 2 && kaleSayisi >= 3) {
        return OyunEvresi::ACILIS;
    }
    
    // Son oyun: Az taş kaldı
    if (vezirSayisi == 0 || (vezirSayisi == 1 && kaleSayisi <= 2)) {
        return OyunEvresi::SON_OYUN;
    }
    
    return OyunEvresi::ORTA_OYUN;
}

// Geçer piyonlar
Bitboard Degerlendirici::gecerPiyonlar(const Tahta& tahta, Renk renk) {
    Bitboard piyonlar = tahta.getBitboard(renk, TasTuru::PIYON);
    Bitboard rakipPiyonlar = tahta.getBitboard(tersRenk(renk), TasTuru::PIYON);
    Bitboard gecerler = 0;
    
    while (piyonlar) {
        int kare = BitboardYardimci::enDusukBitIndeksi(piyonlar);
        int satir = satirIndeksi(kare);
        int sutun = sutunIndeksi(kare);
        
        bool gecer = true;
        
        // İleri yöndeki rakip piyonları kontrol et
        if (renk == Renk::BEYAZ) {
            for (int s = satir + 1; s < 8; s++) {
                // Aynı sütun
                if (BitboardYardimci::bitVar(rakipPiyonlar, kareIndeksi(s, sutun))) {
                    gecer = false;
                    break;
                }
                // Sol sütun
                if (sutun > 0 && BitboardYardimci::bitVar(rakipPiyonlar, kareIndeksi(s, sutun - 1))) {
                    gecer = false;
                    break;
                }
                // Sağ sütun
                if (sutun < 7 && BitboardYardimci::bitVar(rakipPiyonlar, kareIndeksi(s, sutun + 1))) {
                    gecer = false;
                    break;
                }
            }
        } else {
            for (int s = satir - 1; s >= 0; s--) {
                // Aynı sütun
                if (BitboardYardimci::bitVar(rakipPiyonlar, kareIndeksi(s, sutun))) {
                    gecer = false;
                    break;
                }
                // Sol sütun
                if (sutun > 0 && BitboardYardimci::bitVar(rakipPiyonlar, kareIndeksi(s, sutun - 1))) {
                    gecer = false;
                    break;
                }
                // Sağ sütun
                if (sutun < 7 && BitboardYardimci::bitVar(rakipPiyonlar, kareIndeksi(s, sutun + 1))) {
                    gecer = false;
                    break;
                }
            }
        }
        
        if (gecer) {
            BitboardYardimci::bitEkle(gecerler, kare);
        }
    }
    
    return gecerler;
}

// İzole piyonlar
Bitboard Degerlendirici::izolePiyonlar(const Tahta& tahta, Renk renk) {
    Bitboard piyonlar = tahta.getBitboard(renk, TasTuru::PIYON);
    Bitboard izoleler = 0;
    
    while (piyonlar) {
        int kare = BitboardYardimci::enDusukBitIndeksi(piyonlar);
        int sutun = sutunIndeksi(kare);
        
        bool izole = true;
        
        // Sol sütunu kontrol et
        if (sutun > 0) {
            Bitboard solSutun = DOSYA_A << (sutun - 1);
            if (tahta.getBitboard(renk, TasTuru::PIYON) & solSutun) {
                izole = false;
            }
        }
        
        // Sağ sütunu kontrol et
        if (sutun < 7 && izole) {
            Bitboard sagSutun = DOSYA_A << (sutun + 1);
            if (tahta.getBitboard(renk, TasTuru::PIYON) & sagSutun) {
                izole = false;
            }
        }
        
        if (izole) {
            BitboardYardimci::bitEkle(izoleler, kare);
        }
    }
    
    return izoleler;
}