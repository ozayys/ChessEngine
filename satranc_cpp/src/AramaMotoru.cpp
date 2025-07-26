#include "AramaMotoru.h"
#include "Tahta.h"
#include "HamleUretici.h"
#include "Degerlendirici.h"
#include <iostream>
#include <algorithm>
#include <cstring>

// TranspositionTable implementasyonu
TranspositionTable::TranspositionTable(size_t boyutMB) 
    : suankiYas(0), hit(0), miss(0) {
    // MB'dan giriş sayısına çevir
    size_t girisSayisi = (boyutMB * 1024 * 1024) / sizeof(TTGiris);
    // 2'nin kuvveti yap
    boyut = 1;
    while (boyut < girisSayisi) boyut <<= 1;
    
    tablo.resize(boyut);
    temizle();
}

void TranspositionTable::temizle() {
    for (auto& giris : tablo) {
        giris.hash = 0;
        giris.derinlik = -1;
    }
    hit = miss = 0;
}

void TranspositionTable::kaydet(uint64_t hash, int derinlik, int skor, 
                               TTBayrak bayrak, const Hamle& enIyiHamle) {
    size_t indeks = hash & (boyut - 1);
    TTGiris& giris = tablo[indeks];
    
    // Değiştirme stratejisi: daha derin veya aynı yaş
    if (giris.derinlik <= derinlik || giris.yas < suankiYas) {
        giris.hash = hash;
        giris.derinlik = derinlik;
        giris.skor = skor;
        giris.bayrak = bayrak;
        giris.enIyiHamle = enIyiHamle;
        giris.yas = suankiYas;
    }
}

bool TranspositionTable::ara(uint64_t hash, TTGiris& giris) const {
    size_t indeks = hash & (boyut - 1);
    const TTGiris& tabloGiris = tablo[indeks];
    
    if (tabloGiris.hash == hash && tabloGiris.derinlik >= 0) {
        giris = tabloGiris;
        hit++;
        return true;
    }
    
    miss++;
    return false;
}

double TranspositionTable::hitOrani() const {
    size_t toplam = hit + miss;
    return toplam > 0 ? (double)hit / toplam : 0.0;
}

// PVTablosu implementasyonu
void PVTablosu::temizle() {
    std::memset(pvUzunluk, 0, sizeof(pvUzunluk));
}

void PVTablosu::guncelle(int ply, const Hamle& hamle) {
    pv[ply][ply] = hamle;
    pvUzunluk[ply] = pvUzunluk[ply + 1];
    
    for (int i = ply + 1; i < pvUzunluk[ply]; i++) {
        pv[ply][i] = pv[ply + 1][i];
    }
}

void PVTablosu::kopyala(int ply) {
    pvUzunluk[ply] = ply + 1;
}

std::vector<Hamle> PVTablosu::pvAl(int derinlik) const {
    std::vector<Hamle> sonuc;
    for (int i = 0; i < std::min(derinlik, pvUzunluk[0]); i++) {
        sonuc.push_back(pv[0][i]);
    }
    return sonuc;
}

// AramaMotoru implementasyonu
AramaMotoru::AramaMotoru(size_t ttBoyutMB) 
    : maxDerinlik(0), aramaDevam(true), motorDusunuyor(false) {
    tt = std::make_unique<TranspositionTable>(ttBoyutMB);
    std::memset(killerHamleler, 0, sizeof(killerHamleler));
    std::memset(historyTablo, 0, sizeof(historyTablo));
}

Hamle AramaMotoru::enIyiHamleyiBul(Tahta& tahta, int derinlik, 
                                   std::chrono::milliseconds sure) {
    aramaBaslangic = std::chrono::steady_clock::now();
    maxDerinlik = derinlik;
    maxSure = sure;
    aramaDevam = true;
    istatistikler.sifirla();
    
    Hamle enIyiHamle;
    int enIyiSkor = -SONSUZ;
    
    // İteratif derinleştirme
    for (int d = 1; d <= derinlik && aramaDevam; d++) {
        int skor = iteratifDerinlestirme(tahta, d);
        
        if (aramaDevam && pvTablo.pvAl(1).size() > 0) {
            enIyiHamle = pvTablo.pvAl(1)[0];
            enIyiSkor = skor;
            
            // Bilgi çıktısı
            auto pv = pvTablo.pvAl(d);
            std::cout << "info depth " << d << " score cp " << skor;
            std::cout << " nodes " << istatistikler.dugumSayisi;
            std::cout << " pv";
            for (const auto& hamle : pv) {
                std::cout << " " << hamle.notasyon();
            }
            std::cout << std::endl;
        }
        
        // Mat bulunduysa daha derine bakma
        if (std::abs(enIyiSkor) > MAT_DEGERI - 100) {
            break;
        }
    }
    
    // İstatistikleri güncelle
    auto simdi = std::chrono::steady_clock::now();
    istatistikler.gecenSure = std::chrono::duration_cast<std::chrono::milliseconds>(simdi - aramaBaslangic);
    
    return enIyiHamle;
}

int AramaMotoru::iteratifDerinlestirme(Tahta& tahta, int maxDerinlik) {
    pvTablo.temizle();
    
    // Aspiration window
    int alpha = -SONSUZ;
    int beta = SONSUZ;
    
    int skor = alphaBeta(tahta, maxDerinlik, alpha, beta, 0);
    
    return skor;
}

int AramaMotoru::alphaBeta(Tahta& tahta, int derinlik, int alpha, int beta, int ply) {
    istatistikler.dugumSayisi++;
    
    // Zaman kontrolü
    if ((istatistikler.dugumSayisi & 4095) == 0 && !zamanKontrol()) {
        aramaDevam = false;
        return 0;
    }
    
    // Berabere kontrolü (3 tekrar)
    if (ply > 0 && tahta.getElliHamleKurali() >= 100) {
        return BERABERE;
    }
    
    // Transposition table araması
    TTGiris ttGiris;
    bool ttVurusu = tt->ara(tahta.getZobristHash(), ttGiris);
    
    if (ttVurusu && ttGiris.derinlik >= derinlik && ply > 0) {
        if (ttGiris.bayrak == TTBayrak::EXACT) {
            return ttGiris.skor;
        } else if (ttGiris.bayrak == TTBayrak::LOWER && ttGiris.skor > alpha) {
            alpha = ttGiris.skor;
        } else if (ttGiris.bayrak == TTBayrak::UPPER && ttGiris.skor < beta) {
            beta = ttGiris.skor;
        }
        
        if (alpha >= beta) {
            return ttGiris.skor;
        }
    }
    
    // Derinlik 0'a ulaştıysa quiescence araması
    if (derinlik <= 0) {
        return quiescence(tahta, alpha, beta, ply);
    }
    
    // Hamle üret
    HamleListesi hamleler;
    HamleUretici::tumHamleleriUret(tahta, hamleler);
    
    // Mat veya pat kontrolü
    if (hamleler.bosMu()) {
        if (tahta.sahCekildiMi(tahta.getSira())) {
            return -MAT_DEGERI + ply; // Mat
        } else {
            return BERABERE; // Pat
        }
    }
    
    // Hamle sıralama
    Hamle* ttHamle = ttVurusu ? &ttGiris.enIyiHamle : nullptr;
    hamleleriSirala(hamleler, tahta, ttHamle, ply);
    
    int enIyiSkor = -SONSUZ;
    Hamle enIyiHamle;
    TTBayrak ttBayrak = TTBayrak::UPPER;
    
    // Hamleleri dene
    for (int i = 0; i < hamleler.getBoyut(); i++) {
        const Hamle& hamle = hamleler[i];
        
        // Hamle yap
        tahta.hamleYap(hamle);
        
        // Legal mi kontrolü
        if (tahta.sahCekildiMi(tersRenk(tahta.getSira()))) {
            tahta.hamleGeriAl(hamle);
            continue;
        }
        
        int skor;
        
        // PVS (Principal Variation Search)
        if (i == 0) {
            skor = -alphaBeta(tahta, derinlik - 1, -beta, -alpha, ply + 1);
        } else {
            // Null window araması
            skor = -alphaBeta(tahta, derinlik - 1, -alpha - 1, -alpha, ply + 1);
            
            if (skor > alpha && skor < beta) {
                // Tam pencere ile yeniden ara
                skor = -alphaBeta(tahta, derinlik - 1, -beta, -alpha, ply + 1);
            }
        }
        
        // Hamle geri al
        tahta.hamleGeriAl(hamle);
        
        // Arama durdurulduysa çık
        if (!aramaDevam) {
            return 0;
        }
        
        // En iyi skor güncelleme
        if (skor > enIyiSkor) {
            enIyiSkor = skor;
            enIyiHamle = hamle;
            
            if (skor > alpha) {
                alpha = skor;
                ttBayrak = TTBayrak::EXACT;
                
                // PV güncelle
                pvTablo.guncelle(ply, hamle);
                
                if (skor >= beta) {
                    // Beta kesme
                    istatistikler.betaKesmeleri++;
                    ttBayrak = TTBayrak::LOWER;
                    
                    // Killer hamle güncelle
                    if (hamle.alinanTas == TasTuru::YOK) {
                        killerHamleEkle(hamle, ply);
                    }
                    
                    // History güncelle
                    historyGuncelle(hamle, derinlik);
                    
                    break;
                }
            }
        }
    }
    
    // Transposition table'a kaydet
    tt->kaydet(tahta.getZobristHash(), derinlik, enIyiSkor, ttBayrak, enIyiHamle);
    
    return enIyiSkor;
}

int AramaMotoru::quiescence(Tahta& tahta, int alpha, int beta, int ply) {
    istatistikler.qDugumSayisi++;
    
    // Pozisyon değerlendirmesi
    int evalSkor = Degerlendirici::degerlendir(tahta);
    
    if (evalSkor >= beta) {
        return beta;
    }
    
    if (evalSkor > alpha) {
        alpha = evalSkor;
    }
    
    // Sadece alma hamlelerini üret
    HamleListesi hamleler;
    HamleUretici::saldiriHamleleriUret(tahta, hamleler);
    
    // Hamle sıralama
    hamleleriSirala(hamleler, tahta, nullptr, ply);
    
    // Hamleleri dene
    for (const Hamle& hamle : hamleler) {
        // Hamle yap
        tahta.hamleYap(hamle);
        
        // Legal mi kontrolü
        if (tahta.sahCekildiMi(tersRenk(tahta.getSira()))) {
            tahta.hamleGeriAl(hamle);
            continue;
        }
        
        int skor = -quiescence(tahta, -beta, -alpha, ply + 1);
        
        // Hamle geri al
        tahta.hamleGeriAl(hamle);
        
        if (skor >= beta) {
            return beta;
        }
        
        if (skor > alpha) {
            alpha = skor;
        }
    }
    
    return alpha;
}

void AramaMotoru::hamleleriSirala(HamleListesi& hamleler, const Tahta& tahta, 
                                  const Hamle* ttHamle, int ply) {
    // Her hamle için skor hesapla
    for (int i = 0; i < hamleler.getBoyut(); i++) {
        hamleler[i].skor = hamleSkoru(hamleler[i], tahta, ttHamle, ply);
    }
    
    // Sıralama
    hamleler.sirala();
}

int AramaMotoru::hamleSkoru(const Hamle& hamle, const Tahta& tahta, 
                            const Hamle* ttHamle, int ply) {
    // TT hamlesi
    if (ttHamle && hamle == *ttHamle) {
        return HASH_HAMLE_SKOR;
    }
    
    // Alma hamlesi
    if (hamle.alinanTas != TasTuru::YOK) {
        // MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
        int kazancDegeri = TAS_DEGERLERI[static_cast<int>(hamle.alinanTas)];
        int saldirganDegeri = TAS_DEGERLERI[static_cast<int>(hamle.tas)];
        return KAZANC_SKOR_TABAN + kazancDegeri - saldirganDegeri;
    }
    
    // Killer hamleler
    if (killerHamleMi(hamle, ply)) {
        return hamle == killerHamleler[ply][0] ? KILLER_SKOR_1 : KILLER_SKOR_2;
    }
    
    // History heuristic
    return historySkoru(hamle);
}

void AramaMotoru::killerHamleEkle(const Hamle& hamle, int ply) {
    if (ply >= MAX_PLY) return;
    
    if (hamle != killerHamleler[ply][0]) {
        killerHamleler[ply][1] = killerHamleler[ply][0];
        killerHamleler[ply][0] = hamle;
    }
}

bool AramaMotoru::killerHamleMi(const Hamle& hamle, int ply) const {
    if (ply >= MAX_PLY) return false;
    return hamle == killerHamleler[ply][0] || hamle == killerHamleler[ply][1];
}

void AramaMotoru::historyGuncelle(const Hamle& hamle, int derinlik) {
    historyTablo[hamle.kaynak][hamle.hedef] += derinlik * derinlik;
    
    // Overflow kontrolü
    if (historyTablo[hamle.kaynak][hamle.hedef] > 100000) {
        // Tüm değerleri yarıya indir
        for (int i = 0; i < 64; i++) {
            for (int j = 0; j < 64; j++) {
                historyTablo[i][j] /= 2;
            }
        }
    }
}

int AramaMotoru::historySkoru(const Hamle& hamle) const {
    return historyTablo[hamle.kaynak][hamle.hedef] / HISTORY_SKOR_BOLENI;
}

bool AramaMotoru::zamanKontrol() const {
    if (maxSure.count() <= 0) return true;
    
    auto simdi = std::chrono::steady_clock::now();
    auto gecen = std::chrono::duration_cast<std::chrono::milliseconds>(simdi - aramaBaslangic);
    
    return gecen < maxSure;
}

// Saldırı hamleleri üretme (HamleUretici'ye eklenecek)
void HamleUretici::saldiriHamleleriUret(const Tahta& tahta, HamleListesi& hamleler) {
    hamleler.temizle();
    
    HamleListesi tumHamleler;
    tumHamleleriUret(tahta, tumHamleler);
    
    // Sadece alma hamlelerini filtrele
    for (const Hamle& hamle : tumHamleler) {
        if (hamle.alinanTas != TasTuru::YOK || 
            hamle.tur == HamleTuru::TERFI || 
            hamle.tur == HamleTuru::TERFI_ALMA) {
            hamleler.ekle(hamle);
        }
    }
}