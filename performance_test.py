"""
Satranç motoru performans testi
"""

import time
from Tahta import Tahta
from Arama import Arama
from LegalHamle import LegalHamleBulucu

def test_performans():
    """Motor performansını test et"""
    print("Satranç Motoru Performans Testi")
    print("="*50)
    
    # Test pozisyonları
    test_durumlar = [
        "Başlangıç pozisyonu",
        "Orta oyun pozisyonu",
        "Son oyun pozisyonu"
    ]
    
    for i, durum in enumerate(test_durumlar):
        print(f"\n{durum}:")
        print("-"*30)
        
        tahta = Tahta()
        
        # Orta oyun için bazı hamleler yap
        if i == 1:
            test_hamleler = [
                (12, 28),  # e2-e4
                (52, 36),  # e7-e5
                (6, 21),   # g1-f3
                (57, 42),  # b8-c6
                (5, 26),   # f1-c4
                (61, 25),  # f8-c5
            ]
            for hamle in test_hamleler:
                tahta.hamle_yap(hamle)
                
        # Son oyun için daha fazla hamle
        elif i == 2:
            # Çoğu taşı değiş
            test_hamleler = [
                (12, 28), (52, 36), (6, 21), (57, 42),
                (5, 26), (61, 25), (3, 39), (59, 31),
                (21, 36), (51, 36), (26, 35), (42, 36),
                (1, 18), (62, 45), (2, 38), (58, 23),
                (0, 1), (56, 57), (11, 19), (50, 42),
                (19, 27), (42, 34), (27, 35), (49, 41)
            ]
            for hamle in test_hamleler:
                try:
                    tahta.hamle_yap(hamle)
                except:
                    pass
        
        # Farklı derinlikler test et
        for derinlik in [3, 4, 5]:
            arama = Arama(derinlik=derinlik, tt_boyut_mb=128)
            
            start_time = time.time()
            en_iyi_hamle = arama.en_iyi_hamle_bul(tahta, zaman_limiti=5.0)
            elapsed_time = time.time() - start_time
            
            stats = arama.get_istatistikler()
            
            print(f"\nDerinlik {derinlik}:")
            print(f"  Süre: {elapsed_time:.2f} saniye")
            print(f"  Düğüm sayısı: {stats['dugum_sayisi']:,}")
            print(f"  Düğüm/saniye: {int(stats['dugum_sayisi']/elapsed_time):,}")
            print(f"  TT Hit: {stats['tt_hit']:,}")
            print(f"  Prune: {stats['prune_sayisi']:,}")
            
            tt_stats = stats['tt_istatistikler']
            print(f"  TT Doluluk: {tt_stats['doluluk_yuzde']:.1f}%")
            print(f"  TT Hit Oranı: {tt_stats['hit_orani']:.1f}%")
            
            if en_iyi_hamle:
                print(f"  En iyi hamle: {en_iyi_hamle}")

def test_hamle_uretme():
    """Hamle üretme hızını test et"""
    print("\n\nHamle Üretme Performans Testi")
    print("="*50)
    
    tahta = Tahta()
    legal_bulucu = LegalHamleBulucu()
    
    # 1000 kez hamle üret
    start_time = time.time()
    toplam_hamle = 0
    
    for _ in range(1000):
        hamleler = legal_bulucu.legal_hamleleri_bul(tahta)
        toplam_hamle += len(hamleler)
        
    elapsed_time = time.time() - start_time
    
    print(f"1000 pozisyon için hamle üretme:")
    print(f"  Süre: {elapsed_time:.3f} saniye")
    print(f"  Pozisyon/saniye: {int(1000/elapsed_time):,}")
    print(f"  Ortalama hamle sayısı: {toplam_hamle/1000:.1f}")

if __name__ == "__main__":
    test_performans()
    test_hamle_uretme()
    print("\n\nTest tamamlandı!")