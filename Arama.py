"""
MiniMax ve Alpha-Beta Pruning algoritmaları.
Transposition table, move ordering, iterative deepening ile optimize edilmiş.
"""

from HamleUret import HamleUretici
from Degerlendirme import Degerlendirici
from LegalHamle import LegalHamleBulucu
from TranspositionTable import TranspositionTable
from MoveOrdering import MoveOrdering
import time


class Arama:
    def __init__(self, derinlik=4, tt_boyut_mb=128):
        self.derinlik = derinlik
        self.hamle_uretici = HamleUretici()
        self.degerlendirme = Degerlendirici()
        self.legal_bulucu = LegalHamleBulucu()
        
        # Optimizasyon sistemleri
        self.tt = TranspositionTable(tt_boyut_mb)
        self.move_ordering = MoveOrdering()
        
        # İstatistikler
        self.dugum_sayisi = 0
        self.max_derinlik = 0
        self.tt_hit = 0
        self.prune_sayisi = 0
        
        # Zaman yönetimi
        self.arama_baslangic = 0
        self.zaman_limiti = 0

    def derinlik_degistir(self, yeni_derinlik):
        """Arama derinliğini değiştir"""
        self.derinlik = yeni_derinlik

    def en_iyi_hamle_bul(self, tahta, zaman_limiti=None):
        """Iterative deepening ile en iyi hamleyi bul"""
        self.dugum_sayisi = 0
        self.max_derinlik = 0
        self.tt_hit = 0
        self.prune_sayisi = 0
        self.arama_baslangic = time.time()
        self.zaman_limiti = zaman_limiti or float('inf')
        
        en_iyi_hamle = None
        en_iyi_skor = float('-inf') if tahta.beyaz_sira else float('inf')
        
        try:
            # Legal hamleleri al
            hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)
            
            if not hamleler:
                return None
                
            # Iterative deepening
            for d in range(1, self.derinlik + 1):
                # Zaman kontrolü
                if time.time() - self.arama_baslangic > self.zaman_limiti * 0.4:
                    break
                    
                iterasyon_en_iyi = None
                iterasyon_skor = float('-inf') if tahta.beyaz_sira else float('inf')
                
                # Önceki iterasyondan en iyi hamleyi kullan
                if en_iyi_hamle:
                    hamleler = self.move_ordering.hamleleri_sirala(tahta, hamleler, en_iyi_hamle)
                else:
                    hamleler = self.move_ordering.hamleleri_sirala(tahta, hamleler)
                
                for hamle in hamleler:
                    # Zaman kontrolü
                    if time.time() - self.arama_baslangic > self.zaman_limiti:
                        return en_iyi_hamle or hamleler[0]
                        
                    tahta_kopyasi = tahta.kopyala()
                    
                    if not tahta_kopyasi.hamle_yap(hamle):
                        continue
                        
                    if tahta.beyaz_sira:  # Beyaz oynuyor
                        skor = self.alpha_beta(tahta_kopyasi, d - 1, float('-inf'), float('inf'), False, 0)
                        if skor > iterasyon_skor:
                            iterasyon_skor = skor
                            iterasyon_en_iyi = hamle
                    else:  # Siyah oynuyor
                        skor = self.alpha_beta(tahta_kopyasi, d - 1, float('-inf'), float('inf'), True, 0)
                        if skor < iterasyon_skor:
                            iterasyon_skor = skor
                            iterasyon_en_iyi = hamle
                            
                # Bu derinlikteki sonuç daha iyiyse güncelle
                if iterasyon_en_iyi:
                    en_iyi_hamle = iterasyon_en_iyi
                    en_iyi_skor = iterasyon_skor
                    
        except Exception as e:
            print(f"Arama hatası: {e}")
            
        return en_iyi_hamle

    def alpha_beta(self, tahta, derinlik, alpha, beta, maksimize_ediyor, ply):
        """Optimize edilmiş Alpha-Beta pruning"""
        self.dugum_sayisi += 1
        alfa_orijinal = alpha
        
        # Transposition table kontrolü
        tt_skor, tt_hamle = self.tt.ara(tahta.hash, derinlik, alpha, beta)
        if tt_skor is not None:
            self.tt_hit += 1
            return tt_skor
            
        # Oyun sonu kontrolü
        if tahta.mat_mi():
            skor = -self.degerlendirme.mat_skoru(ply) if maksimize_ediyor else self.degerlendirme.mat_skoru(ply)
            return skor
            
        if tahta.pat_mi():
            return 0
            
        # Terminal düğüm
        if derinlik == 0:
            return self.quiescence(tahta, alpha, beta, maksimize_ediyor, 0)
            
        # Legal hamleleri al
        hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)
        
        if not hamleler:
            return self.degerlendirme.degerlendir(tahta)
            
        # Hamleleri sırala
        hamleler = self.move_ordering.hamleleri_sirala(tahta, hamleler, tt_hamle, ply)
        
        en_iyi_hamle = None
        
        if maksimize_ediyor:
            max_eval = float('-inf')
            
            for i, hamle in enumerate(hamleler):
                tahta_kopyasi = tahta.kopyala()
                tahta_kopyasi.hamle_yap(hamle)
                
                # Late Move Reduction (LMR)
                azaltma = 0
                if i >= 4 and derinlik >= 3 and not self._kritik_hamle_mi(tahta, hamle):
                    azaltma = 1
                    
                eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1 - azaltma, alpha, beta, False, ply + 1)
                
                # Azaltılmış aramayla iyi sonuç aldıysak tam derinlikte tekrar ara
                if azaltma > 0 and eval_skor > alpha:
                    eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1, alpha, beta, False, ply + 1)
                    
                if eval_skor > max_eval:
                    max_eval = eval_skor
                    en_iyi_hamle = hamle
                    
                alpha = max(alpha, eval_skor)
                
                if beta <= alpha:
                    self.prune_sayisi += 1
                    self.move_ordering.killer_hamle_ekle(hamle, ply)
                    self.move_ordering.history_guncelle(hamle, derinlik, True)
                    break
                    
            sonuc = max_eval
            
        else:
            min_eval = float('inf')
            
            for i, hamle in enumerate(hamleler):
                tahta_kopyasi = tahta.kopyala()
                tahta_kopyasi.hamle_yap(hamle)
                
                # Late Move Reduction (LMR)
                azaltma = 0
                if i >= 4 and derinlik >= 3 and not self._kritik_hamle_mi(tahta, hamle):
                    azaltma = 1
                    
                eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1 - azaltma, alpha, beta, True, ply + 1)
                
                # Azaltılmış aramayla iyi sonuç aldıysak tam derinlikte tekrar ara
                if azaltma > 0 and eval_skor < beta:
                    eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1, alpha, beta, True, ply + 1)
                    
                if eval_skor < min_eval:
                    min_eval = eval_skor
                    en_iyi_hamle = hamle
                    
                beta = min(beta, eval_skor)
                
                if beta <= alpha:
                    self.prune_sayisi += 1
                    self.move_ordering.killer_hamle_ekle(hamle, ply)
                    self.move_ordering.history_guncelle(hamle, derinlik, True)
                    break
                    
            sonuc = min_eval
            
        # Transposition table'a kaydet
        tt_flag = self.tt.EXACT
        if sonuc <= alfa_orijinal:
            tt_flag = self.tt.ALPHA
        elif sonuc >= beta:
            tt_flag = self.tt.BETA
            
        self.tt.kaydet(tahta.hash, derinlik, sonuc, tt_flag, en_iyi_hamle)
        
        return sonuc
        
    def quiescence(self, tahta, alpha, beta, maksimize_ediyor, derinlik):
        """Quiescence search - sadece alma hamlelerini değerlendir"""
        # Derinlik limiti
        if derinlik < -5:
            return self.degerlendirme.degerlendir(tahta)
            
        # Stand pat
        stand_pat = self.degerlendirme.degerlendir(tahta)
        
        if maksimize_ediyor:
            if stand_pat >= beta:
                return beta
            if alpha < stand_pat:
                alpha = stand_pat
                
            # Sadece alma hamlelerini değerlendir
            hamleler = self._alma_hamlelerini_al(tahta)
            hamleler = self.move_ordering.hamleleri_sirala(tahta, hamleler)
            
            for hamle in hamleler:
                tahta_kopyasi = tahta.kopyala()
                tahta_kopyasi.hamle_yap(hamle)
                
                skor = self.quiescence(tahta_kopyasi, alpha, beta, False, derinlik - 1)
                
                if skor >= beta:
                    return beta
                if skor > alpha:
                    alpha = skor
                    
            return alpha
            
        else:
            if stand_pat <= alpha:
                return alpha
            if beta > stand_pat:
                beta = stand_pat
                
            # Sadece alma hamlelerini değerlendir
            hamleler = self._alma_hamlelerini_al(tahta)
            hamleler = self.move_ordering.hamleleri_sirala(tahta, hamleler)
            
            for hamle in hamleler:
                tahta_kopyasi = tahta.kopyala()
                tahta_kopyasi.hamle_yap(hamle)
                
                skor = self.quiescence(tahta_kopyasi, alpha, beta, True, derinlik - 1)
                
                if skor <= alpha:
                    return alpha
                if skor < beta:
                    beta = skor
                    
            return beta
            
    def _alma_hamlelerini_al(self, tahta):
        """Sadece alma hamlelerini döndür"""
        tum_hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)
        alma_hamleleri = []
        
        for hamle in tum_hamleler:
            hedef = hamle[1]
            if tahta.bit_kontrol_et(hedef):
                alma_hamleleri.append(hamle)
                
        return alma_hamleleri
        
    def _kritik_hamle_mi(self, tahta, hamle):
        """Hamle kritik mi (alma, şah, terfi)"""
        hedef = hamle[1]
        
        # Alma hamlesi
        if tahta.bit_kontrol_et(hedef):
            return True
            
        # Terfi
        if len(hamle) > 2 and hamle[2]:
            return True
            
        # TODO: Şah kontrolü eklenebilir
        
        return False

    def get_istatistikler(self):
        """Arama istatistiklerini döndür"""
        return {
            'dugum_sayisi': self.dugum_sayisi,
            'max_derinlik': self.max_derinlik,
            'derinlik': self.derinlik,
            'tt_hit': self.tt_hit,
            'prune_sayisi': self.prune_sayisi,
            'tt_istatistikler': self.tt.istatistikler()
        }