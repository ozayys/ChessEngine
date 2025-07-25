"""
Move Ordering - Hamleleri sıralama sistemi.
İyi hamleleri önce değerlendirerek alpha-beta pruning'i daha etkili yapar.
"""


class MoveOrdering:
    """Hamle sıralama ve history heuristic"""
    
    def __init__(self):
        # Killer moves - her derinlik için 2 killer hamle
        self.killer_moves = [[None, None] for _ in range(32)]
        
        # History heuristic - hamlelerin geçmiş başarıları
        self.history_table = [[0] * 64 for _ in range(64)]
        
        # MVV-LVA (Most Valuable Victim - Least Valuable Attacker) değerleri
        self.tas_degerleri = {
            'piyon': 1, 'at': 3, 'fil': 3, 'kale': 5, 'vezir': 9, 'sah': 100
        }
        
    def hamleleri_sirala(self, tahta, hamleler, tt_hamle=None, derinlik=0):
        """Hamleleri önem sırasına göre sırala"""
        skorlu_hamleler = []
        
        for hamle in hamleler:
            skor = 0
            
            # 1. Transposition table'dan gelen hamle en yüksek öncelik
            if tt_hamle and hamle == tt_hamle:
                skor = 1000000
                
            # 2. Terfi hamleleri
            elif len(hamle) > 2 and hamle[2]:  # Terfi
                terfi_turu = hamle[2]
                if terfi_turu == 'vezir':
                    skor = 900000
                else:
                    skor = 800000
                    
            # 3. Alma hamleleri (MVV-LVA)
            else:
                kaynak, hedef = hamle[0], hamle[1]
                hedef_tas = tahta.tas_turu_al(hedef)
                
                if hedef_tas:
                    # MVV-LVA skorlaması
                    hedef_renk, hedef_tur = hedef_tas
                    kaynak_tas = tahta.tas_turu_al(kaynak)
                    if kaynak_tas:
                        kaynak_renk, kaynak_tur = kaynak_tas
                        kurban_degeri = self.tas_degerleri.get(hedef_tur, 0)
                        saldiran_degeri = self.tas_degerleri.get(kaynak_tur, 0)
                        # En değerli kurban - En az değerli saldıran
                        skor = 10000 * kurban_degeri - saldiran_degeri
                        
                # 4. Killer moves
                elif self._killer_hamle_mi(hamle, derinlik):
                    skor = 9000
                    
                # 5. History heuristic
                else:
                    skor = self.history_table[kaynak][hedef]
                    
            skorlu_hamleler.append((skor, hamle))
            
        # Skora göre sırala (büyükten küçüğe)
        skorlu_hamleler.sort(key=lambda x: x[0], reverse=True)
        
        return [hamle for _, hamle in skorlu_hamleler]
        
    def killer_hamle_ekle(self, hamle, derinlik):
        """Killer hamle ekle"""
        # Alma hamlesi değilse killer olarak sakla
        if derinlik < len(self.killer_moves):
            # Zaten varsa ekleme
            if hamle != self.killer_moves[derinlik][0]:
                # İkinci killer'ı birinciye kaydır
                self.killer_moves[derinlik][1] = self.killer_moves[derinlik][0]
                self.killer_moves[derinlik][0] = hamle
                
    def _killer_hamle_mi(self, hamle, derinlik):
        """Hamle killer hamle mi kontrol et"""
        if derinlik < len(self.killer_moves):
            return (hamle == self.killer_moves[derinlik][0] or 
                   hamle == self.killer_moves[derinlik][1])
        return False
        
    def history_guncelle(self, hamle, derinlik, beta_cutoff=False):
        """History tablosunu güncelle"""
        kaynak, hedef = hamle[0], hamle[1]
        
        # Beta cutoff yapan hamleler daha değerli
        bonus = derinlik * derinlik
        if beta_cutoff:
            bonus *= 2
            
        self.history_table[kaynak][hedef] += bonus
        
        # Overflow kontrolü
        if self.history_table[kaynak][hedef] > 100000:
            # Tüm değerleri yarıya indir
            for i in range(64):
                for j in range(64):
                    self.history_table[i][j] //= 2
                    
    def temizle(self):
        """Killer ve history tablolarını temizle"""
        self.killer_moves = [[None, None] for _ in range(32)]
        self.history_table = [[0] * 64 for _ in range(64)]