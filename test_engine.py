#!/usr/bin/env python3
"""
Chess engine test script - Principal Variation ve derinlik testleri
"""

from Tahta import Tahta
from Arama import Arama
from Degerlendirme import Degerlendirici
import time

def test_principal_variation():
    """Principal variation değerlendirmesini test et"""
    print("=== Principal Variation Testi ===\n")
    
    tahta = Tahta()
    arama = Arama(derinlik=4)
    degerlendirici = Degerlendirici()
    
    # Başlangıç pozisyonu
    print("1. Başlangıç pozisyonu:")
    statik_skor = degerlendirici.pozisyon_degerlendir(tahta)
    pv_skor = arama.pozisyon_degerlendir_pv(tahta)
    print(f"   Statik değerlendirme: {statik_skor/100:.2f}")
    print(f"   PV değerlendirme: {pv_skor/100:.2f}")
    print(f"   Fark: {(pv_skor - statik_skor)/100:.2f}\n")
    
    # Birkaç hamle yapalım
    hamleler = [
        (52, 36),  # e2-e4
        (12, 28),  # e7-e5
        (62, 45),  # g1-f3
        (1, 18),   # b8-c6
    ]
    
    for i, hamle in enumerate(hamleler):
        tahta.hamle_yap(hamle)
        print(f"{i+2}. Hamle {hamle} sonrası:")
        
        statik_skor = degerlendirici.pozisyon_degerlendir(tahta)
        pv_skor = arama.pozisyon_degerlendir_pv(tahta)
        
        print(f"   Statik değerlendirme: {statik_skor/100:.2f}")
        print(f"   PV değerlendirme: {pv_skor/100:.2f}")
        print(f"   Fark: {(pv_skor - statik_skor)/100:.2f}")
        print(f"   Sıra: {'Beyaz' if tahta.beyaz_sira else 'Siyah'}\n")

def test_derinlik_farki():
    """Farklı derinliklerde arama kalitesini test et"""
    print("\n=== Derinlik Testi ===\n")
    
    tahta = Tahta()
    
    # Birkaç hamle yap
    hamleler = [
        (52, 36),  # e2-e4
        (12, 28),  # e7-e5
        (62, 45),  # g1-f3
        (1, 18),   # b8-c6
        (61, 34),  # f1-c4
    ]
    
    for hamle in hamleler:
        tahta.hamle_yap(hamle)
    
    print("Test pozisyonu hazırlandı (İtalyan Açılışı)\n")
    
    # Farklı derinliklerde test
    for derinlik in [1, 2, 3, 4, 5]:
        print(f"Derinlik {derinlik}:")
        
        arama = Arama(derinlik=derinlik)
        baslangic = time.time()
        
        en_iyi_hamle = arama.en_iyi_hamle_bul(tahta, zaman_limiti=10)
        
        sure = time.time() - baslangic
        istatistikler = arama.get_istatistikler()
        
        if en_iyi_hamle:
            print(f"   En iyi hamle: {en_iyi_hamle}")
            print(f"   Süre: {sure:.2f}s")
            print(f"   Değerlendirilen pozisyon: {istatistikler['dugum_sayisi']:,}")
            print(f"   Pozisyon/saniye: {int(istatistikler['dugum_sayisi']/sure):,}")
        else:
            print("   Hamle bulunamadı!")
        
        print()

def test_degerlendirme_tutarliligi():
    """Aynı pozisyonda değerlendirme tutarlılığını test et"""
    print("\n=== Değerlendirme Tutarlılığı Testi ===\n")
    
    tahta = Tahta()
    arama = Arama(derinlik=3)
    
    # Test pozisyonu
    hamleler = [
        (52, 36),  # e2-e4
        (12, 20),  # e7-e6
        (51, 35),  # d2-d4
        (11, 27),  # d7-d5
    ]
    
    for hamle in hamleler:
        tahta.hamle_yap(hamle)
    
    print("Fransız Savunması test pozisyonu")
    print("Aynı pozisyonu 5 kez değerlendiriyoruz:\n")
    
    for i in range(5):
        pv_skor = arama.pozisyon_degerlendir_pv(tahta)
        print(f"   Deneme {i+1}: {pv_skor/100:.2f}")
        time.sleep(0.1)  # Cache'i test etmek için kısa bekleme

if __name__ == "__main__":
    print("Chess Engine Test Suite\n")
    print("="*50)
    
    test_principal_variation()
    test_derinlik_farki()
    test_degerlendirme_tutarliligi()
    
    print("\n" + "="*50)
    print("Testler tamamlandı!")