#!/usr/bin/env python3
"""
Basit TT testi
"""

from Tahta import Tahta
from Arama import Arama

def test_tt_simple():
    """Basit TT testi"""
    print("=== BASİT TT TESTİ ===\n")
    
    # Basit pozisyon
    tahta = Tahta()
    tahta.fen_yukle("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    
    print(f"Başlangıç hash: {tahta.zobrist_hash:016X}")
    print(f"Beyaz sıra: {tahta.beyaz_sira}")
    
    # Arama yap
    arama = Arama(4)
    hamle = arama.en_iyi_hamle_bul(tahta, zaman_limiti=5)
    
    print(f"\nTT boyutu: {arama.transposition_table.boyut}")
    print(f"TT hit: {arama.transposition_table.hit}")
    print(f"TT miss: {arama.transposition_table.miss}")
    
    # Manuel TT test
    print("\n--- Manuel TT Testi ---")
    
    # Aynı pozisyonu TT'ye kaydet
    test_hash = 0x123456789ABCDEF0
    arama.transposition_table.kaydet(test_hash, 5, 100, 'EXACT', None, 1)
    
    # Aynı hash'i ara
    entry = arama.transposition_table.ara(test_hash)
    if entry:
        print(f"TT'de bulundu! Skor: {entry['skor']}, Derinlik: {entry['derinlik']}")
    else:
        print("TT'de bulunamadı!")
    
    # Farklı hash ara
    entry2 = arama.transposition_table.ara(0x0FEDCBA987654321)
    if entry2:
        print("Farklı hash bulundu - HATA!")
    else:
        print("Farklı hash bulunamadı - DOĞRU")

if __name__ == "__main__":
    test_tt_simple()