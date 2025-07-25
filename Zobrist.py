"""
Zobrist hashing implementasyonu. Tahta pozisyonlarını hash'lemek için kullanılır.
Transposition table için gerekli.
"""

import random


class ZobristHash:
    def __init__(self):
        # Random number generator with fixed seed for reproducibility
        random.seed(42)
        
        # Pre-compute zobrist keys
        self.tas_anahtarlari = {}
        self.rok_anahtarlari = {}
        self.en_passant_anahtarlari = {}
        self.sira_anahtari = 0
        
        self._anahtarlari_olustur()
        
    def _anahtarlari_olustur(self):
        """Zobrist anahtarlarını oluştur"""
        # Her kare ve taş türü için benzersiz 64-bit anahtar
        taslar = [
            ('beyaz', 'piyon'), ('beyaz', 'at'), ('beyaz', 'fil'),
            ('beyaz', 'kale'), ('beyaz', 'vezir'), ('beyaz', 'sah'),
            ('siyah', 'piyon'), ('siyah', 'at'), ('siyah', 'fil'),
            ('siyah', 'kale'), ('siyah', 'vezir'), ('siyah', 'sah')
        ]
        
        for kare in range(64):
            for renk, tur in taslar:
                self.tas_anahtarlari[(kare, renk, tur)] = random.getrandbits(64)
                
        # Rok hakları için anahtarlar
        self.rok_anahtarlari['beyaz_kisa'] = random.getrandbits(64)
        self.rok_anahtarlari['beyaz_uzun'] = random.getrandbits(64)
        self.rok_anahtarlari['siyah_kisa'] = random.getrandbits(64)
        self.rok_anahtarlari['siyah_uzun'] = random.getrandbits(64)
        
        # En passant sütunları için
        for sutun in range(8):
            self.en_passant_anahtarlari[sutun] = random.getrandbits(64)
            
        # Sıra değişimi için
        self.sira_anahtari = random.getrandbits(64)
        
    def hash_hesapla(self, tahta):
        """Tahtanın mevcut pozisyonunun hash'ini hesapla"""
        hash_degeri = 0
        
        # Taşları hash'e ekle
        for kare in range(64):
            tas = tahta.tas_turu_al(kare)
            if tas:
                renk, tur = tas
                hash_degeri ^= self.tas_anahtarlari[(kare, renk, tur)]
                
        # Rok haklarını ekle
        if tahta.beyaz_kisa_rok:
            hash_degeri ^= self.rok_anahtarlari['beyaz_kisa']
        if tahta.beyaz_uzun_rok:
            hash_degeri ^= self.rok_anahtarlari['beyaz_uzun']
        if tahta.siyah_kisa_rok:
            hash_degeri ^= self.rok_anahtarlari['siyah_kisa']
        if tahta.siyah_uzun_rok:
            hash_degeri ^= self.rok_anahtarlari['siyah_uzun']
            
        # En passant
        if tahta.en_passant_kare != -1:
            sutun = tahta.en_passant_kare % 8
            hash_degeri ^= self.en_passant_anahtarlari[sutun]
            
        # Sıra
        if not tahta.beyaz_sira:
            hash_degeri ^= self.sira_anahtari
            
        return hash_degeri
        
    def hamle_hash_guncelle(self, hash_degeri, tahta, hamle):
        """Hamle sonrası hash'i incremental olarak güncelle (hızlı)"""
        kaynak, hedef = hamle[:2]
        
        # Kaynak karedeki taşı kaldır
        tas = tahta.tas_turu_al(kaynak)
        if tas:
            renk, tur = tas
            hash_degeri ^= self.tas_anahtarlari[(kaynak, renk, tur)]
            
        # Hedef karedeki taşı kaldır (varsa)
        hedef_tas = tahta.tas_turu_al(hedef)
        if hedef_tas:
            renk2, tur2 = hedef_tas
            hash_degeri ^= self.tas_anahtarlari[(hedef, renk2, tur2)]
            
        # Taşı hedef kareye ekle
        if tas:
            # Terfi durumu
            if len(hamle) > 2 and hamle[2]:
                terfi_turu = hamle[2]
                hash_degeri ^= self.tas_anahtarlari[(hedef, renk, terfi_turu)]
            else:
                hash_degeri ^= self.tas_anahtarlari[(hedef, renk, tur)]
                
        # Sıra değişimi
        hash_degeri ^= self.sira_anahtari
        
        return hash_degeri

    def hash_dogrula(self, tahta, beklenen_hash):
        """Hash doğruluğunu kontrol et (debug amaçlı)"""
        hesaplanan_hash = self.hash_hesapla(tahta)
        return hesaplanan_hash == beklenen_hash

    def hash_string(self, hash_degeri):
        """Hash değerini string olarak döndür (debug amaçlı)"""
        return f"0x{hash_degeri:016X}"


class TranspositionTable:
    """Zobrist hash tabanlı pozisyon saklama tablosu"""

    def __init__(self, boyut_mb=64):
        """Transposition table başlat"""
        # MB cinsinden boyutu entry sayısına çevir
        # Her entry: hash