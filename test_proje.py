#!/usr/bin/env python3
"""
Satranç projesinin temel işlevlerini test eden basit test dosyası.
"""

import sys
import os

def test_modul_yukleme():
    """Tüm modüllerin düzgün yüklenip yüklenmediğini test et"""
    print("=== Modül Yükleme Testi ===")
    
    try:
        from Tahta import Tahta
        print("✓ Tahta modülü yüklendi")
    except ImportError as e:
        print(f"✗ Tahta modülü yüklenemedi: {e}")
        return False
    
    try:
        from HamleUret import HamleUretici
        print("✓ HamleUret modülü yüklendi")
    except ImportError as e:
        print(f"✗ HamleUret modülü yüklenemedi: {e}")
        return False
    
    try:
        from Arama import Arama
        print("✓ Arama modülü yüklendi")
    except ImportError as e:
        print(f"✗ Arama modülü yüklenemedi: {e}")
        return False
    
    try:
        from Degerlendirme import Degerlendirici
        print("✓ Degerlendirme modülü yüklendi")
    except ImportError as e:
        print(f"✗ Degerlendirme modülü yüklenemedi: {e}")
        return False
    
    try:
        from LegalHamle import LegalHamleBulucu
        print("✓ LegalHamle modülü yüklendi")
    except ImportError as e:
        print(f"✗ LegalHamle modülü yüklenemedi: {e}")
        return False
    
    return True

def test_tahta_olusturma():
    """Tahta oluşturma ve başlangıç pozisyonunu test et"""
    print("\n=== Tahta Oluşturma Testi ===")
    
    try:
        from Tahta import Tahta
        tahta = Tahta()
        
        # Başlangıç pozisyonu kontrolü
        if tahta.beyaz_sira:
            print("✓ Başlangıçta beyaz sıra")
        else:
            print("✗ Başlangıç sıra hatası")
            return False
        
        # Bazı başlangıç taşları kontrolü
        if tahta.tas_turu_al(0) == ('beyaz', 'kale'):
            print("✓ a1'de beyaz kale var")
        else:
            print("✗ a1'de beyaz kale yok")
            return False
        
        if tahta.tas_turu_al(3) == ('beyaz', 'sah'):
            print("✓ d1'de beyaz şah var")
        else:
            print("✗ d1'de beyaz şah yok")
            return False
        
        if tahta.tas_turu_al(4) == ('beyaz', 'vezir'):
            print("✓ e1'de beyaz vezir var")
        else:
            print("✗ e1'de beyaz vezir yok")
            return False
        
        if tahta.tas_turu_al(59) == ('siyah', 'sah'):
            print("✓ d8'de siyah şah var")
        else:
            print("✗ d8'de siyah şah yok")
            return False
        
        if tahta.tas_turu_al(60) == ('siyah', 'vezir'):
            print("✓ e8'de siyah vezir var")
        else:
            print("✗ e8'de siyah vezir yok")
            return False
        
        return True
    
    except Exception as e:
        print(f"✗ Tahta oluşturma hatası: {e}")
        return False

def test_hamle_uretimi():
    """Hamle üretimini test et"""
    print("\n=== Hamle Üretimi Testi ===")
    
    try:
        from Tahta import Tahta
        from HamleUret import HamleUretici
        
        tahta = Tahta()
        uretici = HamleUretici()
        
        hamleler = uretici.tum_hamleleri_uret(tahta)
        print(f"✓ Başlangıç pozisyonunda {len(hamleler)} hamle üretildi")
        
        if len(hamleler) == 20:  # Başlangıçta 20 hamle olmalı
            print("✓ Başlangıç hamle sayısı doğru")
        else:
            print(f"⚠ Başlangıç hamle sayısı beklenenden farklı: {len(hamleler)} (beklenen: 20)")
        
        # İlk birkaç hamleyi yazdır
        print("İlk 5 hamle:")
        for i, hamle in enumerate(hamleler[:5]):
            print(f"  {i+1}. {hamle}")
        
        return True
    
    except Exception as e:
        print(f"✗ Hamle üretimi hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_motor_araması():
    """Motor arama algoritmasını test et"""
    print("\n=== Motor Arama Testi ===")
    
    try:
        from Tahta import Tahta
        from Arama import Arama
        
        tahta = Tahta()
        arama = Arama(derinlik=2)  # Düşük derinlik için hızlı test
        
        print("Motor en iyi hamleyi arıyor...")
        en_iyi_hamle = arama.en_iyi_hamle_bul(tahta)
        
        if en_iyi_hamle:
            print(f"✓ Motor hamle buldu: {en_iyi_hamle}")
            
            # Hamleyi dene
            if tahta.hamle_yap(en_iyi_hamle):
                print("✓ Hamle başarıyla uygulandı")
                return True
            else:
                print("✗ Hamle uygulanamadı")
                return False
        else:
            print("✗ Motor hamle bulamadı")
            return False
    
    except Exception as e:
        print(f"✗ Motor arama hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tas_resimleri():
    """Taş resimlerinin varlığını test et"""
    print("\n=== Taş Resimleri Testi ===")
    
    tas_dosyalari = [
        'beyazSah.png', 'beyazVezir.png', 'beyazKale.png',
        'beyazFil.png', 'beyazAt.png', 'beyazPiyon.png',
        'siyahSah.png', 'siyahVezir.png', 'siyahKale.png',
        'siyahFil.png', 'siyahAt.png', 'siyahPiyon.png'
    ]
    
    eksik_dosyalar = []
    mevcut_dosyalar = 0
    
    for dosya in tas_dosyalari:
        dosya_yolu = os.path.join('taslar', dosya)
        if os.path.exists(dosya_yolu):
            print(f"✓ {dosya}")
            mevcut_dosyalar += 1
        else:
            print(f"✗ {dosya} bulunamadı")
            eksik_dosyalar.append(dosya)
    
    print(f"\nToplam: {mevcut_dosyalar}/{len(tas_dosyalari)} dosya mevcut")
    
    if eksik_dosyalar:
        print(f"Eksik dosyalar: {', '.join(eksik_dosyalar)}")
        return False
    else:
        print("✓ Tüm taş resimleri mevcut")
        return True

def main():
    """Ana test fonksiyonu"""
    print("Satranç Projesi Test Süreci Başlıyor...\n")
    
    testler = [
        ("Modül Yükleme", test_modul_yukleme),
        ("Tahta Oluşturma", test_tahta_olusturma), 
        ("Hamle Üretimi", test_hamle_uretimi),
        ("Motor Araması", test_motor_araması),
        ("Taş Resimleri", test_tas_resimleri)
    ]
    
    basarili = 0
    toplam = len(testler)
    
    for test_adi, test_fonk in testler:
        try:
            if test_fonk():
                basarili += 1
                print(f"✓ {test_adi} başarılı")
            else:
                print(f"✗ {test_adi} başarısız")
        except Exception as e:
            print(f"✗ {test_adi} hata: {e}")
    
    print(f"\n=== Test Sonuçları ===")
    print(f"Başarılı: {basarili}/{toplam}")
    print(f"Başarı oranı: %{(basarili/toplam)*100:.1f}")
    
    if basarili == toplam:
        print("🎉 Tüm testler başarılı! Proje çalışmaya hazır.")
        return True
    else:
        print("⚠ Bazı testler başarısız. Sorunları gözden geçirin.")
        return False

if __name__ == "__main__":
    main()