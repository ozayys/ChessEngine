#ifndef BITBOARD_YARDIMCI_H
#define BITBOARD_YARDIMCI_H

#include "Sabitler.h"
#include <bit>
#include <array>

class BitboardYardimci {
public:
    // Bit sayma fonksiyonları
    static inline int bitSayisi(Bitboard bb) {
        return __builtin_popcountll(bb);
    }
    
    // En düşük biti bul ve temizle
    static inline int enDusukBitIndeksi(Bitboard& bb) {
        int indeks = __builtin_ctzll(bb);
        bb &= bb - 1; // En düşük biti temizle
        return indeks;
    }
    
    // Belirli bir kareye bit ekle
    static inline void bitEkle(Bitboard& bb, int kare) {
        bb |= (1ULL << kare);
    }
    
    // Belirli bir karedeki biti temizle
    static inline void bitTemizle(Bitboard& bb, int kare) {
        bb &= ~(1ULL << kare);
    }
    
    // Belirli bir karede bit var mı?
    static inline bool bitVar(Bitboard bb, int kare) {
        return bb & (1ULL << kare);
    }
    
    // Bitboard'u tersine çevir
    static inline Bitboard tersineÇevir(Bitboard bb) {
        return __builtin_bswap64(bb);
    }
    
    // Doğu kaydırma (sağa)
    static inline Bitboard doguKaydir(Bitboard bb) {
        return (bb & ~DOSYA_H) << 1;
    }
    
    // Batı kaydırma (sola)
    static inline Bitboard batiKaydir(Bitboard bb) {
        return (bb & ~DOSYA_A) >> 1;
    }
    
    // Kuzey kaydırma (yukarı)
    static inline Bitboard kuzeyKaydir(Bitboard bb) {
        return bb << 8;
    }
    
    // Güney kaydırma (aşağı)
    static inline Bitboard guneyKaydir(Bitboard bb) {
        return bb >> 8;
    }
    
    // Kuzey-doğu kaydırma
    static inline Bitboard kuzeyDoguKaydir(Bitboard bb) {
        return (bb & ~DOSYA_H) << 9;
    }
    
    // Kuzey-batı kaydırma
    static inline Bitboard kuzeyBatiKaydir(Bitboard bb) {
        return (bb & ~DOSYA_A) << 7;
    }
    
    // Güney-doğu kaydırma
    static inline Bitboard guneyDoguKaydir(Bitboard bb) {
        return (bb & ~DOSYA_H) >> 7;
    }
    
    // Güney-batı kaydırma
    static inline Bitboard guneyBatiKaydir(Bitboard bb) {
        return (bb & ~DOSYA_A) >> 9;
    }
    
    // Işın saldırıları için magic bitboard tabloları (statik olarak başlatılacak)
    static std::array<std::array<Bitboard, 64>, 64> ISIN_SALDIRI;
    
    // At hamle tablosu
    static std::array<Bitboard, 64> AT_HAMLELERI;
    
    // Şah hamle tablosu
    static std::array<Bitboard, 64> SAH_HAMLELERI;
    
    // Piyon saldırı tabloları
    static std::array<std::array<Bitboard, 64>, 2> PIYON_SALDIRILARI;
    
    // Tabloları başlat
    static void tablolariBaslat();
    
    // Işın saldırısı hesapla (kale ve fil için)
    static Bitboard isinSaldirisi(int kaynak, int hedef, Bitboard engeller);
    
    // Kale saldırıları
    static Bitboard kaleSaldiriları(int kare, Bitboard engeller);
    
    // Fil saldırıları
    static Bitboard filSaldiriları(int kare, Bitboard engeller);
    
    // Vezir saldırıları
    static Bitboard vezirSaldiriları(int kare, Bitboard engeller);

private:
    // Magic bitboard için yardımcı fonksiyonlar
    static Bitboard pozitifIsinSaldirisi(int kare, Bitboard engeller, int yon);
    static Bitboard negatifIsinSaldirisi(int kare, Bitboard engeller, int yon);
};

#endif // BITBOARD_YARDIMCI_H