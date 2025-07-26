#ifndef ARAMA_MOTORU_H
#define ARAMA_MOTORU_H

#include "Sabitler.h"
#include "Hamle.h"
#include <vector>
#include <chrono>
#include <atomic>
#include <memory>

// İleri tanımlamalar
class Tahta;

// Transposition Table girişi
struct TTGiris {
    uint64_t hash;
    int derinlik;
    int skor;
    TTBayrak bayrak;
    Hamle enIyiHamle;
    uint8_t yas;
};

// Transposition Table
class TranspositionTable {
private:
    static constexpr size_t VARSAYILAN_BOYUT_MB = 64;
    std::vector<TTGiris> tablo;
    size_t boyut;
    uint8_t suankiYas;
    
    // İstatistikler
    mutable size_t hit;
    mutable size_t miss;
    
public:
    TranspositionTable(size_t boyutMB = VARSAYILAN_BOYUT_MB);
    ~TranspositionTable() = default;
    
    void kaydet(uint64_t hash, int derinlik, int skor, TTBayrak bayrak, 
                const Hamle& enIyiHamle);
    bool ara(uint64_t hash, TTGiris& giris) const;
    void temizle();
    void yasArtir() { suankiYas++; }
    
    // İstatistikler
    double hitOrani() const;
    void istatistikleriSifirla() { hit = miss = 0; }
};

// Arama istatistikleri
struct AramaIstatistikleri {
    uint64_t dugumSayisi;
    uint64_t qDugumSayisi;
    uint64_t ttHit;
    uint64_t ttMiss;
    uint64_t betaKesmeleri;
    uint64_t nullMoveKesmeleri;
    int maxDerinlik;
    std::chrono::milliseconds gecenSure;
    
    void sifirla() {
        dugumSayisi = qDugumSayisi = ttHit = ttMiss = 0;
        betaKesmeleri = nullMoveKesmeleri = 0;
        maxDerinlik = 0;
    }
    
    uint64_t saniyeBasinaDugum() const {
        auto ms = gecenSure.count();
        return ms > 0 ? (dugumSayisi * 1000) / ms : 0;
    }
};

// Principal Variation (PV) tablosu
class PVTablosu {
private:
    static constexpr int MAX_DERINLIK = 64;
    Hamle pv[MAX_DERINLIK][MAX_DERINLIK];
    int pvUzunluk[MAX_DERINLIK];
    
public:
    PVTablosu() { temizle(); }
    
    void guncelle(int ply, const Hamle& hamle);
    void kopyala(int ply);
    std::vector<Hamle> pvAl(int derinlik) const;
    void temizle();
};

// Arama motoru ana sınıfı
class AramaMotoru {
private:
    // Arama parametreleri
    int maxDerinlik;
    std::chrono::milliseconds maxSure;
    std::atomic<bool> aramaDevam;
    
    // Veri yapıları
    std::unique_ptr<TranspositionTable> tt;
    PVTablosu pvTablo;
    AramaIstatistikleri istatistikler;
    
    // Killer moves ve history heuristic
    static constexpr int MAX_PLY = 128;
    Hamle killerHamleler[MAX_PLY][2];
    int historyTablo[64][64]; // [kaynak][hedef]
    
    // Move ordering skorları
    static constexpr int HASH_HAMLE_SKOR = 1000000;
    static constexpr int KAZANC_SKOR_TABAN = 100000;
    static constexpr int KILLER_SKOR_1 = 90000;
    static constexpr int KILLER_SKOR_2 = 80000;
    static constexpr int HISTORY_SKOR_BOLENI = 100;
    
    // Arama parametreleri
    static constexpr int NULL_MOVE_REDUCTION = 2;
    static constexpr int LMR_MOVES_THRESHOLD = 4;
    static constexpr int LMR_DEPTH_THRESHOLD = 3;
    static constexpr int ASPIRATION_WINDOW = 50;
    
    // Zaman kontrolü
    std::chrono::steady_clock::time_point aramaBaslangic;
    bool zamanKontrol() const;
    
public:
    AramaMotoru(size_t ttBoyutMB = 64);
    ~AramaMotoru() = default;
    
    // Ana arama fonksiyonu
    Hamle enIyiHamleyiBul(Tahta& tahta, int derinlik, 
                          std::chrono::milliseconds sure = std::chrono::milliseconds(0));
    
    // Arama kontrolü
    void aramaDurdur() { aramaDevam = false; }
    bool aramaDevamMi() const { return aramaDevam; }
    
    // İstatistikler
    const AramaIstatistikleri& getIstatistikler() const { return istatistikler; }
    
    // TT yönetimi
    void ttTemizle() { tt->temizle(); }
    void ttYasArtir() { tt->yasArtir(); }
    
private:
    // Arama algoritmaları
    int alphaBeta(Tahta& tahta, int derinlik, int alpha, int beta, int ply);
    int quiescence(Tahta& tahta, int alpha, int beta, int ply);
    
    // İteratif derinleştirme
    int iteratifDerinlestirme(Tahta& tahta, int maxDerinlik);
    
    // Hamle sıralama
    void hamleleriSirala(HamleListesi& hamleler, const Tahta& tahta, 
                        const Hamle* ttHamle, int ply);
    int hamleSkoru(const Hamle& hamle, const Tahta& tahta, 
                   const Hamle* ttHamle, int ply);
    
    // Arama iyileştirmeleri
    bool nullMovePruning(Tahta& tahta, int derinlik, int beta, int ply);
    int lateMoveReduction(int derinlik, int hamleNumarasi, bool pvNode);
    
    // Killer moves yönetimi
    void killerHamleEkle(const Hamle& hamle, int ply);
    bool killerHamleMi(const Hamle& hamle, int ply) const;
    
    // History heuristic
    void historyGuncelle(const Hamle& hamle, int derinlik);
    int historySkoru(const Hamle& hamle) const;
    
    // Yardımcı fonksiyonlar
    bool berabereTekrariMi(const Tahta& tahta) const;
    int matSkoru(int ply) const;
    
    // Debug ve bilgi çıktısı
    void aramaBaslangicBilgisi(int derinlik) const;
    void derinlikBilgisi(int derinlik, int skor, const std::vector<Hamle>& pv) const;
    void aramaSonucBilgisi() const;
};

#endif // ARAMA_MOTORU_H