#!/usr/bin/env python3
"""Test script to verify depth change functionality"""

from Arama import Arama
from Tahta import Tahta
import time

def test_depth_change():
    print("=== Testing Depth Change Functionality ===\n")
    
    # Create a board
    tahta = Tahta()
    
    # Create search engine with initial depth 3
    arama = Arama(derinlik=3)
    print(f"Initial depth: {arama.derinlik}")
    
    # Change depth to 5
    arama.derinlik_degistir(5)
    print(f"After change: {arama.derinlik}")
    
    # Test with different depths and time limits
    test_configs = [
        (3, 2.0),   # Depth 3, 2 seconds - should complete
        (5, 3.0),   # Depth 5, 3 seconds - might partially complete
        (7, 10.0),  # Depth 7, 10 seconds - should get deeper
    ]
    
    for depth, time_limit in test_configs:
        print(f"\n--- Testing depth {depth} with {time_limit}s time limit ---")
        arama.derinlik_degistir(depth)
        
        start = time.time()
        best_move = arama.en_iyi_hamle_bul(tahta, zaman_limiti=time_limit)
        elapsed = time.time() - start
        
        if best_move:
            print(f"Best move found: {best_move[0]} -> {best_move[1]}")
            print(f"Time elapsed: {elapsed:.2f}s")
        else:
            print("No move found!")
            
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_depth_change()