#!/usr/bin/env python3
"""
Transposition Table debug testi
"""

from Tahta import Tahta
from Arama import Arama

def test_tt_debug():
    """TT hash tutarlılığını test et"""
    print("=== TT DEBUG TESTİ ===\n")
    
    tahta = Tahta()
    tahta.fen_yukle("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    # İlk hash
    ilk_hash = tahta.zobrist_hash
    print(f"Başlangıç hash: {ilk_hash:016X}")
    
    # e2-e4 hamlesini yap
    tahta.hamle_yap((12, 28, 'piyon', 'iki_kare'))
    ikinci_hash = tahta.zobrist_hash
    print(f"e2-e4 sonrası hash: {ikinci_hash:016X}")
    
    # d7-d5 hamlesini yap
    tahta.hamle_yap((51, 35, 'piyon', 'iki_kare'))
    ucuncu_hash = tahta.zobrist_hash
    print(f"d7-d5 sonrası hash: {ucuncu_hash:016X}")
    
    # Hamleleri geri al
    tahta.hamle_geri_al()
    print(f"d7-d5 geri alma sonrası hash: {tahta.zobrist_hash:016X}")
    print(f"İkinci hash ile aynı mı? {tahta.zobrist_hash == ikinci_hash}")
    
    tahta.hamle_geri_al()
    print(f"e2-e4 geri alma sonrası hash: {tahta.zobrist_hash:016X}")
    print(f"İlk hash ile aynı mı? {tahta.zobrist_hash == ilk_hash}")
    
    # Farklı sırada aynı pozisyona ulaşma
    print("\n--- Farklı yoldan aynı pozisyon ---")
    tahta2 = Tahta()
    tahta2.fen_yukle("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    # d2-d4
    tahta2.hamle_yap((11, 27, 'piyon', 'iki_kare'))
    print(f"d2-d4 sonrası: {tahta2.zobrist_hash:016X}")
    
    # d7-d5
    tahta2.hamle_yap((51, 35, 'piyon', 'iki_kare'))
    print(f"d7-d5 sonrası: {tahta2.zobrist_hash:016X}")
    
    # e2-e4
    tahta2.hamle_yap((12, 28, 'piyon', 'iki_kare'))
    final_hash = tahta2.zobrist_hash
    print(f"e2-e4 sonrası: {final_hash:016X}")
    
    # Aynı pozisyona farklı yoldan ulaştık mı kontrol et
    tahta3 = Tahta()
    tahta3.fen_yukle("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    tahta3.hamle_yap((12, 28, 'piyon', 'iki_kare'))
    tahta3.hamle_yap((51, 35, 'piyon', 'iki_kare'))
    tahta3.hamle_yap((11, 27, 'piyon', 'iki_kare'))
    
    print(f"\nFarklı sırada aynı hash mı? {tahta3.zobrist_hash == final_hash}")
    
    # TT test
    print("\n--- Basit TT Testi ---")
    arama = Arama(3)
    
    # Aynı pozisyonu birkaç kez değerlendir
    for i in range(5):
        skor = arama.alpha_beta(tahta, 2, float('-inf'), float('inf'), True)
        print(f"Deneme {i+1}: Skor = {skor}")
    
    # TT istatistikleri
    arama.transposition_table.istatistikleri_yazdir()

if __name__ == "__main__":
    test_tt_debug()