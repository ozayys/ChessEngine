#!/usr/bin/env python3
"""
Satranç motoru optimizasyon testleri
"""

import time
from Tahta import Tahta
from Arama import Arama
from HamleUret import HamleUretici
from Degerlendirme import Degerlendirici

def test_performans():
    """Performans testi"""
    print("=== PERFORMANS TESTİ ===\n")
    
    # Test pozisyonları
    test_pozisyonlari = [
        # Başlangıç pozisyonu
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        # Orta oyun pozisyonu
        "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        # Kompleks pozisyon
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N2N2/PPP2PPP/R1BQKB1R w KQ - 0 7",
        # Son oyun pozisyonu
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
    ]
    
    for i, fen in enumerate(test_pozisyonlari):
        print(f"\nTest {i+1}: {fen}")
        tahta = Tahta()
        tahta.fen_yukle(fen)
        
        # Farklı derinliklerde test
        for derinlik in [3, 4]:
            arama = Arama(derinlik)
            
            baslangic = time.time()
            hamle = arama.en_iyi_hamle_bul(tahta, zaman_limiti=10)
            sure = time.time() - baslangic
            
            if arama.dugum_sayisi > 0:
                nps = int(arama.dugum_sayisi / sure)
                print(f"  Derinlik {derinlik}: {arama.dugum_sayisi:,} düğüm, {sure:.2f}s, {nps:,} NPS")

def test_tt_hit_orani():
    """Transposition Table hit oranı testi"""
    print("\n=== TRANSPOSITION TABLE TESTİ ===\n")
    
    tahta = Tahta()
    tahta.fen_yukle("r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    
    arama = Arama(5)
    arama.en_iyi_hamle_bul(tahta, zaman_limiti=5)
    
    # TT istatistikleri otomatik olarak yazdırılacak

def test_aspiration_window():
    """Aspiration window testi"""
    print("\n=== ASPIRATION WINDOW TESTİ ===\n")
    
    tahta = Tahta()
    tahta.fen_yukle("r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N2N2/PPP2PPP/R1BQKB1R w KQ - 0 7")
    
    arama = Arama(6)
    arama.en_iyi_hamle_bul(tahta, zaman_limiti=10)
    
    print(f"Aspiration window fail sayısı: {arama._aspiration_fail_count}")

def test_move_ordering():
    """Move ordering testi"""
    print("\n=== MOVE ORDERING TESTİ ===\n")
    
    tahta = Tahta()
    tahta.fen_yukle("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    
    hamle_uretici = HamleUretici()
    hamleler = hamle_uretici.tum_hamleleri_uret(tahta)
    
    print(f"Toplam hamle sayısı: {len(hamleler)}")
    print("İlk 10 hamle:")
    for i, hamle in enumerate(hamleler[:10]):
        print(f"  {i+1}. {hamle}")

def test_pawn_structure():
    """Piyon yapısı analizi testi"""
    print("\n=== PİYON YAPISI ANALİZİ TESTİ ===\n")
    
    # Test pozisyonu: izole, çift ve geçer piyonlar içeren
    tahta = Tahta()
    tahta.fen_yukle("r1bqkb1r/pp1ppppp/5n2/2pP4/2P5/8/PP2PPPP/RNBQKBNR w KQkq c6 0 4")
    
    hamle_uretici = HamleUretici()
    
    # Beyaz piyon analizi
    beyaz_analiz = hamle_uretici.piyon_yapisi_analizi(tahta, True)
    print("Beyaz piyon analizi:")
    print(f"  Geçer piyonlar: {beyaz_analiz['gecer_piyonlar']}")
    print(f"  İzole piyonlar: {beyaz_analiz['izole_piyonlar']}")
    print(f"  Çift piyonlar: {beyaz_analiz['cift_piyonlar']}")
    print(f"  Piyon adaları: {beyaz_analiz['piyon_adalari']}")
    
    # Siyah piyon analizi
    siyah_analiz = hamle_uretici.piyon_yapisi_analizi(tahta, False)
    print("\nSiyah piyon analizi:")
    print(f"  Geçer piyonlar: {siyah_analiz['gecer_piyonlar']}")
    print(f"  İzole piyonlar: {siyah_analiz['izole_piyonlar']}")
    print(f"  Çift piyonlar: {siyah_analiz['cift_piyonlar']}")
    print(f"  Piyon adaları: {siyah_analiz['piyon_adalari']}")

def test_evaluation_speed():
    """Değerlendirme fonksiyonu hız testi"""
    print("\n=== DEĞERLENDİRME HIZI TESTİ ===\n")
    
    tahta = Tahta()
    tahta.fen_yukle("r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    
    degerlendirici = Degerlendirici()
    
    # 100,000 değerlendirme
    baslangic = time.time()
    for _ in range(100000):
        skor = degerlendirici.pozisyon_degerlendir(tahta)
    sure = time.time() - baslangic
    
    print(f"100,000 değerlendirme: {sure:.2f}s")
    print(f"Değerlendirme/saniye: {int(100000/sure):,}")

def test_zobrist_consistency():
    """Zobrist hash tutarlılık testi"""
    print("\n=== ZOBRIST HASH TUTARLILIK TESTİ ===\n")
    
    tahta = Tahta()
    tahta.fen_yukle("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    # İlk hash
    ilk_hash = tahta.zobrist_hash
    print(f"Başlangıç hash: {ilk_hash:016X}")
    
    # e2-e4 hamlesini yap
    tahta.hamle_yap((12, 28, 'piyon', 'iki_kare'))
    ikinci_hash = tahta.zobrist_hash
    print(f"e2-e4 sonrası hash: {ikinci_hash:016X}")
    
    # Hash doğrula
    if tahta.hash_dogrula():
        print("Hash doğrulaması: BAŞARILI")
    else:
        print("Hash doğrulaması: BAŞARISIZ")
    
    # Hamleyi geri al
    tahta.hamle_geri_al()
    son_hash = tahta.zobrist_hash
    print(f"Geri alma sonrası hash: {son_hash:016X}")
    
    if ilk_hash == son_hash:
        print("Hash tutarlılığı: BAŞARILI")
    else:
        print("Hash tutarlılığı: BAŞARISIZ")

if __name__ == "__main__":
    print("SATRANÇ MOTORU OPTİMİZASYON TESTLERİ")
    print("=" * 50)
    
    test_performans()
    test_tt_hit_orani()
    test_aspiration_window()
    test_move_ordering()
    test_pawn_structure()
    test_evaluation_speed()
    test_zobrist_consistency()
    
    print("\n" + "=" * 50)
    print("Testler tamamlandı!")