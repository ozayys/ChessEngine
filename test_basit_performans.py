#!/usr/bin/env python3
"""
Basit performans testi
"""

import time
import cProfile
import pstats
from Tahta import Tahta
from Arama import Arama

def test_performans():
    """Basit performans testi"""
    print("=== BASİT PERFORMANS TESTİ ===\n")
    
    # Başlangıç pozisyonu
    tahta = Tahta()
    tahta.fen_yukle("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    # Derinlik 3 ile test
    arama = Arama(3)
    
    # Profiling başlat
    profiler = cProfile.Profile()
    profiler.enable()
    
    baslangic = time.time()
    hamle = arama.en_iyi_hamle_bul(tahta, zaman_limiti=30)
    sure = time.time() - baslangic
    
    # Profiling durdur
    profiler.disable()
    
    print(f"\nToplam süre: {sure:.2f}s")
    print(f"Düğüm sayısı: {arama.dugum_sayisi:,}")
    print(f"NPS: {int(arama.dugum_sayisi/sure):,}")
    
    # En yavaş fonksiyonları göster
    print("\n=== EN YAVAŞ 20 FONKSİYON ===")
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

if __name__ == "__main__":
    test_performans()