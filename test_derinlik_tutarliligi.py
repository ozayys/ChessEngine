#!/usr/bin/env python3
"""
Derinlik tutarlılığı detaylı test
"""

from Tahta import Tahta
from Arama import Arama
from Degerlendirme import Degerlendirici
import time

def test_derinlik_skor_degisimi():
    """Farklı derinliklerde skor değişimini test et"""
    print("=== Derinlik-Skor Değişimi Testi ===\n")
    
    tahta = Tahta()
    
    # Test pozisyonu oluştur
    test_hamleler = [
        (52, 36),  # e2-e4
        (12, 28),  # e7-e5
        (62, 45),  # g1-f3
        (1, 18),   # b8-c6
        (61, 34),  # f1-c4
        (5, 12),   # f7-f6 (zayıf hamle)
    ]
    
    for hamle in test_hamleler:
        tahta.hamle_yap(hamle)
    
    print("Test pozisyonu hazırlandı (Siyah f6 oynadı - zayıf hamle)\n")
    
    skorlar = []
    
    # Her derinlik için skor hesapla
    for derinlik in range(1, 7):
        # Her test için yeni arama nesnesi ve temiz TT
        arama = Arama(derinlik=derinlik)
        arama.transposition_table.temizle()
        arama._pv_aramasi = False  # Normal arama modu
        
        # En iyi hamleyi bul ve skoru al
        print(f"\nDerinlik {derinlik} analizi:")
        baslangic = time.time()
        
        # Direkt alpha-beta ile skor al
        skor = arama.alpha_beta(tahta, derinlik, float('-inf'), float('inf'), tahta.beyaz_sira)
        
        sure = time.time() - baslangic
        skorlar.append((derinlik, skor))
        
        print(f"  Skor: {skor/100:.2f}")
        print(f"  Süre: {sure:.2f}s")
        print(f"  Düğüm sayısı: {arama.dugum_sayisi:,}")
        
        # Transposition table istatistikleri
        if arama.transposition_table.hit + arama.transposition_table.miss > 0:
            hit_rate = arama.transposition_table.hit / (arama.transposition_table.hit + arama.transposition_table.miss) * 100
            print(f"  TT Hit Rate: {hit_rate:.1f}%")
    
    # Skor değişimlerini analiz et
    print("\n=== Skor Değişim Analizi ===")
    for i in range(len(skorlar)):
        derinlik, skor = skorlar[i]
        print(f"Derinlik {derinlik}: {skor/100:+.2f}", end="")
        
        if i > 0:
            degisim = abs(skorlar[i][1] - skorlar[i-1][1])
            print(f" (değişim: {degisim/100:.2f})", end="")
        print()
    
    # Toplam değişim
    if len(skorlar) > 1:
        toplam_degisim = abs(skorlar[-1][1] - skorlar[0][1])
        print(f"\nToplam değişim (D1->D{len(skorlar)}): {toplam_degisim/100:.2f}")
        
        # Ortalama değişim
        toplam = 0
        for i in range(1, len(skorlar)):
            toplam += abs(skorlar[i][1] - skorlar[i-1][1])
        ort_degisim = toplam / (len(skorlar) - 1)
        print(f"Ortalama değişim: {ort_degisim/100:.2f}")

def test_basit_pozisyon():
    """Basit pozisyonda tutarlılık testi"""
    print("\n\n=== Basit Pozisyon Testi ===\n")
    
    tahta = Tahta()
    
    # Sadece birkaç hamle
    tahta.hamle_yap((52, 36))  # e2-e4
    tahta.hamle_yap((12, 28))  # e7-e5
    
    print("Basit pozisyon (1.e4 e5)\n")
    
    for derinlik in range(1, 6):
        arama = Arama(derinlik=derinlik)
        arama.transposition_table.temizle()
        arama._pv_aramasi = False
        
        # İki farklı yöntemle skor al
        skor1 = arama.alpha_beta(tahta, derinlik, float('-inf'), float('inf'), tahta.beyaz_sira)
        
        # İkinci test için TT'yi temizle
        arama.transposition_table.temizle()
        skor2 = arama.pozisyon_degerlendir_pv(tahta)
        
        print(f"Derinlik {derinlik}:")
        print(f"  Alpha-Beta skoru: {skor1/100:+.2f}")
        print(f"  PV değerlendirme: {skor2/100:+.2f}")
        print(f"  Fark: {abs(skor1-skor2)/100:.2f}")

def test_quiescence_etkisi():
    """Quiescence search'ün etkisini test et"""
    print("\n\n=== Quiescence Search Etkisi ===\n")
    
    tahta = Tahta()
    
    # Alma pozisyonu oluştur
    hamleler = [
        (52, 36),  # e2-e4
        (12, 28),  # e7-e5
        (62, 45),  # g1-f3
        (1, 18),   # b8-c6
        (45, 28),  # f3xe5 - piyon alır
    ]
    
    for hamle in hamleler:
        tahta.hamle_yap(hamle)
    
    print("Test pozisyonu: Beyaz e5 piyonunu aldı\n")
    
    arama = Arama(derinlik=3)
    degerlendirici = Degerlendirici()
    
    # Statik değerlendirme
    statik_skor = degerlendirici.degerlendir(tahta)
    
    # Quiescence search
    qs_skor = arama.quiescence_search(tahta, float('-inf'), float('inf'), tahta.beyaz_sira)
    
    # Normal alpha-beta (derinlik 0'da QS kullanıyor)
    ab_skor = arama.alpha_beta(tahta, 0, float('-inf'), float('inf'), tahta.beyaz_sira)
    
    print(f"Statik değerlendirme: {statik_skor/100:+.2f}")
    print(f"Quiescence search: {qs_skor/100:+.2f}")
    print(f"Alpha-Beta (D0): {ab_skor/100:+.2f}")
    print(f"\nFark (QS - Statik): {(qs_skor-statik_skor)/100:.2f}")

if __name__ == "__main__":
    print("Chess Engine Derinlik Tutarlılığı Test Suite\n")
    print("="*60)
    
    test_derinlik_skor_degisimi()
    test_basit_pozisyon()
    test_quiescence_etkisi()
    
    print("\n" + "="*60)
    print("Testler tamamlandı!")