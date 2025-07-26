#ifndef SABITLER_H
#define SABITLER_H

#include <cstdint>
#include <string>

// Bitboard tipi
using Bitboard = uint64_t;

// Taş türleri
enum class TasTuru {
    PIYON = 0,
    AT = 1,
    FIL = 2,
    KALE = 3,
    VEZIR = 4,
    SAH = 5,
    YOK = 6
};

// Renkler
enum class Renk {
    BEYAZ = 0,
    SIYAH = 1,
    YOK = 2
};

// Hamle türleri
enum class HamleTuru {
    NORMAL,
    ALMA,
    TERFI,
    TERFI_ALMA,
    KISA_ROK,
    UZUN_ROK,
    EN_PASSANT,
    IKI_KARE
};

// Sabitler
constexpr int TAHTA_BOYUTU = 8;
constexpr int KARE_SAYISI = 64;
constexpr int SONSUZ = 1000000;
constexpr int MAT_DEGERI = 100000;
constexpr int BERABERE = 0;

// Kare indeksleri (a1 = 0, h8 = 63)
constexpr int A1 = 0, B1 = 1, C1 = 2, D1 = 3, E1 = 4, F1 = 5, G1 = 6, H1 = 7;
constexpr int A8 = 56, B8 = 57, C8 = 58, D8 = 59, E8 = 60, F8 = 61, G8 = 62, H8 = 63;

// Başlangıç pozisyonları (bitboard)
constexpr Bitboard BASLANGIC_BEYAZ_PIYON = 0x000000000000FF00ULL;
constexpr Bitboard BASLANGIC_BEYAZ_AT = 0x0000000000000042ULL;
constexpr Bitboard BASLANGIC_BEYAZ_FIL = 0x0000000000000024ULL;
constexpr Bitboard BASLANGIC_BEYAZ_KALE = 0x0000000000000081ULL;
constexpr Bitboard BASLANGIC_BEYAZ_VEZIR = 0x0000000000000008ULL;
constexpr Bitboard BASLANGIC_BEYAZ_SAH = 0x0000000000000010ULL;

constexpr Bitboard BASLANGIC_SIYAH_PIYON = 0x00FF000000000000ULL;
constexpr Bitboard BASLANGIC_SIYAH_AT = 0x4200000000000000ULL;
constexpr Bitboard BASLANGIC_SIYAH_FIL = 0x2400000000000000ULL;
constexpr Bitboard BASLANGIC_SIYAH_KALE = 0x8100000000000000ULL;
constexpr Bitboard BASLANGIC_SIYAH_VEZIR = 0x0800000000000000ULL;
constexpr Bitboard BASLANGIC_SIYAH_SAH = 0x1000000000000000ULL;

// Dosya ve satır maskeleri
constexpr Bitboard DOSYA_A = 0x0101010101010101ULL;
constexpr Bitboard DOSYA_B = 0x0202020202020202ULL;
constexpr Bitboard DOSYA_C = 0x0404040404040404ULL;
constexpr Bitboard DOSYA_D = 0x0808080808080808ULL;
constexpr Bitboard DOSYA_E = 0x1010101010101010ULL;
constexpr Bitboard DOSYA_F = 0x2020202020202020ULL;
constexpr Bitboard DOSYA_G = 0x4040404040404040ULL;
constexpr Bitboard DOSYA_H = 0x8080808080808080ULL;

constexpr Bitboard SATIR_1 = 0x00000000000000FFULL;
constexpr Bitboard SATIR_2 = 0x000000000000FF00ULL;
constexpr Bitboard SATIR_3 = 0x0000000000FF0000ULL;
constexpr Bitboard SATIR_4 = 0x00000000FF000000ULL;
constexpr Bitboard SATIR_5 = 0x000000FF00000000ULL;
constexpr Bitboard SATIR_6 = 0x0000FF0000000000ULL;
constexpr Bitboard SATIR_7 = 0x00FF000000000000ULL;
constexpr Bitboard SATIR_8 = 0xFF00000000000000ULL;

// Taş değerleri (centipawn)
constexpr int TAS_DEGERLERI[6] = {
    100,   // Piyon
    320,   // At
    330,   // Fil
    500,   // Kale
    900,   // Vezir
    20000  // Şah
};

// Transposition table bayrakları
enum class TTBayrak {
    EXACT,
    LOWER,
    UPPER
};

// Oyun evresi
enum class OyunEvresi {
    ACILIS,
    ORTA_OYUN,
    SON_OYUN
};

// Yardımcı fonksiyonlar için inline tanımlar
inline int satirIndeksi(int kare) { return kare / 8; }
inline int sutunIndeksi(int kare) { return kare % 8; }
inline int kareIndeksi(int satir, int sutun) { return satir * 8 + sutun; }

// Renk tersini al
inline Renk tersRenk(Renk renk) {
    return renk == Renk::BEYAZ ? Renk::SIYAH : Renk::BEYAZ;
}

// String dönüşümleri
inline std::string tasAdi(TasTuru tur) {
    switch (tur) {
        case TasTuru::PIYON: return "piyon";
        case TasTuru::AT: return "at";
        case TasTuru::FIL: return "fil";
        case TasTuru::KALE: return "kale";
        case TasTuru::VEZIR: return "vezir";
        case TasTuru::SAH: return "şah";
        default: return "yok";
    }
}

inline std::string renkAdi(Renk renk) {
    return renk == Renk::BEYAZ ? "beyaz" : "siyah";
}

#endif // SABITLER_H