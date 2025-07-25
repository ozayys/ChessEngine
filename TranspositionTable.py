"""
Transposition Table - Pozisyon değerlendirmelerini cache'leyen yapı.
Aynı pozisyonların tekrar hesaplanmasını önler.
"""


class TranspositionEntry:
    """Transposition table girişi"""
    def __init__(self, hash_key, derinlik, skor, flag, en_iyi_hamle=None):
        self.hash_key = hash_key
        self.derinlik = derinlik
        self.skor = skor
        self.flag = flag  # EXACT, ALPHA, BETA
        self.en_iyi_hamle = en_iyi_hamle
        
        
class TranspositionTable:
    """Hash tabanlı pozisyon cache'i"""
    
    # Flag sabitleri
    EXACT = 0
    ALPHA = 1  # Üst sınır
    BETA = 2   # Alt sınır
    
    def __init__(self, boyut_mb=128):
        """
        boyut_mb: Tablo boyutu megabayt cinsinden
        """
        # Her giriş yaklaşık 32 byte
        self.giri_sayisi = (boyut_mb * 1024 * 1024) // 32
        self.tablo = [None] * self.giri_sayisi
        self.kullanim = 0
        self.hit = 0
        self.toplam_sorgu = 0
        
    def temizle(self):
        """Tabloyu temizle"""
        self.tablo = [None] * self.giri_sayisi
        self.kullanim = 0
        self.hit = 0
        self.toplam_sorgu = 0
        
    def kaydet(self, hash_key, derinlik, skor, flag, en_iyi_hamle=None):
        """Pozisyonu tabloya kaydet"""
        index = hash_key % self.giri_sayisi
        
        # Mevcut girişi kontrol et
        mevcut = self.tablo[index]
        
        # Yeni giriş veya daha derin analiz ise güncelle
        if mevcut is None:
            self.kullanim += 1
        elif mevcut.derinlik <= derinlik:
            # Daha derin veya eşit derinlikte analiz - güncelle
            pass
        else:
            # Mevcut giriş daha derin - güncelleme
            return
            
        self.tablo[index] = TranspositionEntry(hash_key, derinlik, skor, flag, en_iyi_hamle)
        
    def ara(self, hash_key, derinlik, alpha, beta):
        """Pozisyonu tabloda ara"""
        self.toplam_sorgu += 1
        index = hash_key % self.giri_sayisi
        entry = self.tablo[index]
        
        if entry is None or entry.hash_key != hash_key:
            return None, None
            
        # Derinlik yeterli değilse kullanma
        if entry.derinlik < derinlik:
            # Ama en iyi hamleyi döndür (move ordering için)
            return None, entry.en_iyi_hamle
            
        self.hit += 1
        
        # Flag'e göre değer döndür
        if entry.flag == self.EXACT:
            return entry.skor, entry.en_iyi_hamle
        elif entry.flag == self.ALPHA and entry.skor <= alpha:
            return alpha, entry.en_iyi_hamle
        elif entry.flag == self.BETA and entry.skor >= beta:
            return beta, entry.en_iyi_hamle
            
        return None, entry.en_iyi_hamle
        
    def en_iyi_hamle_al(self, hash_key):
        """Sadece en iyi hamleyi al (PV - Principal Variation için)"""
        index = hash_key % self.giri_sayisi
        entry = self.tablo[index]
        
        if entry and entry.hash_key == hash_key:
            return entry.en_iyi_hamle
        return None
        
    def istatistikler(self):
        """Tablo istatistiklerini döndür"""
        doluluk = (self.kullanim / self.giri_sayisi) * 100 if self.giri_sayisi > 0 else 0
        hit_orani = (self.hit / self.toplam_sorgu) * 100 if self.toplam_sorgu > 0 else 0
        
        return {
            'boyut': self.giri_sayisi,
            'kullanim': self.kullanim,
            'doluluk_yuzde': doluluk,
            'hit': self.hit,
            'toplam_sorgu': self.toplam_sorgu,
            'hit_orani': hit_orani
        }