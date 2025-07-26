#ifndef DEGERLENDIRICI_H
#define DEGERLENDIRICI_H

#include "Sabitler.h"
#include "BitboardYardimci.h"
#include <array>

// İleri tanımlama
class Tahta;

class Degerlendirici {
private:
    // Piece-Square tabloları (PST) - Orta oyun ve son oyun için ayrı
    static std::array<std::array<int, 64>, 6> ortaOyunPST[2]; // [renk][taş türü][kare]
    static std::array<std::array<int, 64>, 6> sonOyunPST[2];
    
    // Piyon yapısı değerlendirme tabloları
    static std::array<int, 64> gecerPiyonBonus;
    static std::array<int, 64> izolePiyonCeza;
    static std::array<int, 64> geriPiyonCeza;
    static std::array<int, 64> ciftPiyonCeza;
    
    // Taş değerleri (orta oyun ve son oyun)
    static constexpr int ORTA_OYUN_TAS_DEGERLERI[6] = {
        100,   // Piyon
        320,   // At
        330,   // Fil
        500,   // Kale
        900,   // Vezir
        20000  // Şah
    };
    
    static constexpr int SON_OYUN_TAS_DEGERLERI[6] = {
        110,   // Piyon (son oyunda daha değerli)
        320,   // At
        330,   // Fil
        500,   // Kale
        900,   // Vezir
        20000  // Şah
    };
    
    // Değerlendirme parametreleri
    static constexpr int FIL_CIFTI_BONUS = 50;
    static constexpr int KALE_ACIK_SUTUN_BONUS = 20;
    static constexpr int KALE_YARI_ACIK_SUTUN_BONUS = 10;
    static constexpr int KALE_7_SATIR_BONUS = 30;
    static constexpr int AT_MERKEZ_BONUS = 15;
    static constexpr int VEZIR_ERKEN_CIKIS_CEZA = -30;
    static constexpr int SAH_GUVENLIGI_KATSAYI = 2;
    static constexpr int TEMPO_BONUS = 10;
    
    // Tablo başlatma
    static bool tablolarBaslatildi;
    static void tablolariBaslat();
    
public:
    // Ana değerlendirme fonksiyonu
    static int degerlendir(const Tahta& tahta);
    
    // Bileşen değerlendirmeleri
    static int materyalDegerlendir(const Tahta& tahta);
    static int pozisyonelDegerlendir(const Tahta& tahta);
    static int piyonYapisiDegerlendir(const Tahta& tahta);
    static int mobiliteDeğerlendir(const Tahta& tahta);
    static int sahGuvenligiDegerlendir(const Tahta& tahta);
    static int merkezKontroluDegerlendir(const Tahta& tahta);
    
    // Yardımcı değerlendirmeler
    static int filCiftiBonus(const Tahta& tahta, Renk renk);
    static int kaleAktivitesi(const Tahta& tahta, Renk renk);
    static int atPozisyonu(const Tahta& tahta, Renk renk);
    static int vezirAktivitesi(const Tahta& tahta, Renk renk);
    
    // Piyon yapısı analizi
    static Bitboard gecerPiyonlar(const Tahta& tahta, Renk renk);
    static Bitboard izolePiyonlar(const Tahta& tahta, Renk renk);
    static Bitboard geriPiyonlar(const Tahta& tahta, Renk renk);
    static Bitboard ciftPiyonlar(const Tahta& tahta, Renk renk);
    static Bitboard zayifPiyonlar(const Tahta& tahta, Renk renk);
    
    // Oyun evresi belirleme
    static OyunEvresi oyunEvresiBelirle(const Tahta& tahta);
    static int evreKatsayisi(const Tahta& tahta); // 0-256 arası (0=tam son oyun, 256=tam orta oyun)
    
    // Özel durumlar
    static int sonOyunDegerlendirmesi(const Tahta& tahta);
    static bool yetersizMateryal(const Tahta& tahta);
    static int drawishFactor(const Tahta& tahta); // Berabere eğilimi
    
    // PST erişimi
    static int pieceSquareValue(TasTuru tas, Renk renk, int kare, OyunEvresi evre);
    
    // Mobilite hesaplamaları
    static int tasMobilitesi(const Tahta& tahta, int kare, TasTuru tas, Renk renk);
    
    // Tehdit değerlendirmesi
    static int tehditDegerlendir(const Tahta& tahta, Renk renk);
    
    // Şah güvenliği detayları
    static int sahKalkaniBonusu(const Tahta& tahta, Renk renk);
    static int sahSaldiriTehdidi(const Tahta& tahta, Renk renk);
    
    // Açık hatlar ve kareler
    static Bitboard acikSutunlar(const Tahta& tahta);
    static Bitboard yariAcikSutunlar(const Tahta& tahta, Renk renk);
    static int acikHatKontrolu(const Tahta& tahta, Renk renk);
    
    // İnisiyatif ve tempo
    static int inisiyatifDegerlendir(const Tahta& tahta);
    
private:
    // Yardımcı fonksiyonlar
    static int interpolate(int ortaOyunDeger, int sonOyunDeger, int evreKatsayisi);
    static Bitboard onPiyonlar(const Tahta& tahta, Renk renk, int kare);
    static Bitboard arkaPiyonlar(const Tahta& tahta, Renk renk, int kare);
};

#endif // DEGERLENDIRICI_H