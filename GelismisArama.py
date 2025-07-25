"""
Gelişmiş Satranç Arama Motoru
Alpha-Beta Pruning + Null Move + LMR + PVS + Forward Pruning
"""

from HamleUret import HamleUretici
from Degerlendirme import Degerlendirici
from MatKontrol import MatPatKontrolcu
import time


class GelismisArama:
    def __init__(self, derinlik=6):
        self.derinlik = derinlik
        self.hamle_uretici = HamleUretici()
        self.degerlendirme = Degerlendirici()
        self.mat_kontrolcu = MatPatKontrolcu()
        
        # İstatistikler
        self.dugum_sayisi = 0
        self.kesme_sayisi = 0
        self.null_move_kesme = 0
        self.lmr_kesme = 0
        self.futility_kesme = 0
        
        # Arama parametreleri
        self.null_move_enabled = True
        self.lmr_enabled = True
        self.futility_enabled = True
        self.forward_pruning_enabled = True
        
        # History ve Killer moves
        self.history_table = {}
        self.killer_moves = [[] for _ in range(20)]  # Derinlik başına killer hamleler
        
        # PVS için
        self.pv_line = []
        
        # Arama limitleri
        self.max_time = None
        self.start_time = None
    
    def derinlik_degistir(self, yeni_derinlik):
        """Arama derinliğini değiştir"""
        self.derinlik = max(1, min(yeni_derinlik, 15))
    
    def en_iyi_hamle_bul(self, tahta, max_time=None):
        """Ana arama fonksiyonu"""
        self.start_time = time.time()
        self.max_time = max_time
        self._istatistikleri_sifirla()
        
        # Mat/Pat kontrolü
        if self.mat_kontrolcu.is_game_over(tahta):
            return None
        
        # Iterative Deepening
        en_iyi_hamle = None
        
        for current_depth in range(1, self.derinlik + 1):
            if self._zaman_asildi():
                break
                
            try:
                hamle = self._derinlik_araması(tahta, current_depth)
                if hamle:
                    en_iyi_hamle = hamle
                    print(f"Derinlik {current_depth}: {hamle}")
                    
            except TimeoutError:
                break
        
        self._istatistikleri_yazdir()
        return en_iyi_hamle
    
    def _derinlik_araması(self, tahta, derinlik):
        """Belirli derinlik için arama"""
        en_iyi_hamle = None
        en_iyi_skor = float('-inf') if tahta.beyaz_sira else float('inf')
        alpha = float('-inf')
        beta = float('inf')
        
        hamleler = self._hamleleri_sirala(tahta, self.hamle_uretici.tum_hamleleri_uret(tahta))
        
        for i, hamle in enumerate(hamleler):
            if self._zaman_asildi():
                raise TimeoutError()
            
            tahta_kopyasi = tahta.kopyala()
            if not tahta_kopyasi.hamle_yap(hamle):
                continue
            
            # PVS: İlk hamle tam derinlikte, diğerleri azaltılmış
            if i == 0:
                # Principal Variation
                skor = -self._alpha_beta_pvs(tahta_kopyasi, derinlik - 1, -beta, -alpha, False, 0)
            else:
                # Null Window Search
                skor = -self._alpha_beta_pvs(tahta_kopyasi, derinlik - 1, -alpha - 1, -alpha, False, 0)
                
                # Re-search if needed
                if alpha < skor < beta:
                    skor = -self._alpha_beta_pvs(tahta_kopyasi, derinlik - 1, -beta, -alpha, False, 0)
            
            if tahta.beyaz_sira:
                if skor > en_iyi_skor:
                    en_iyi_skor = skor
                    en_iyi_hamle = hamle
                    alpha = max(alpha, skor)
            else:
                if skor < en_iyi_skor:
                    en_iyi_skor = skor
                    en_iyi_hamle = hamle
                    beta = min(beta, skor)
            
            if beta <= alpha:
                self.kesme_sayisi += 1
                break
        
        return en_iyi_hamle
    
    def _alpha_beta_pvs(self, tahta, derinlik, alpha, beta, null_move_allowed, ply):
        """Principal Variation Search with Alpha-Beta"""
        self.dugum_sayisi += 1
        
        if self._zaman_asildi():
            raise TimeoutError()
        
        # Mat/Pat kontrolü
        mate_score = self.mat_kontrolcu.get_mate_score(tahta, ply)
        if mate_score is not None:
            return mate_score
        
        # Terminal node
        if derinlik <= 0:
            return self._quiescence_search(tahta, alpha, beta, 0)
        
        # Null Move Pruning
        if (self.null_move_enabled and null_move_allowed and derinlik >= 3 and 
            not self.mat_kontrolcu.sah_tehdidinde_mi(tahta, tahta.beyaz_sira)):
            
            tahta_null = tahta.kopyala()
            tahta_null.beyaz_sira = not tahta_null.beyaz_sira
            
            R = 3 if derinlik >= 6 else 2  # Reduction factor
            null_score = -self._alpha_beta_pvs(tahta_null, derinlik - 1 - R, -beta, -beta + 1, False, ply + 1)
            
            if null_score >= beta:
                self.null_move_kesme += 1
                return null_score
        
        hamleler = self._hamleleri_sirala(tahta, self.hamle_uretici.tum_hamleleri_uret(tahta))
        
        if not hamleler:
            # Mat veya pat
            return self.mat_kontrolcu.get_mate_score(tahta, ply) or 0
        
        en_iyi_skor = float('-inf')
        legal_hamle_sayisi = 0
        
        for i, hamle in enumerate(hamleler):
            tahta_kopyasi = tahta.kopyala()
            if not tahta_kopyasi.hamle_yap(hamle):
                continue
            
            legal_hamle_sayisi += 1
            
            # Forward Pruning - Promising olmayan hamleleri atla
            if self._forward_pruning_kontrolu(hamle, derinlik, i):
                continue
            
            # Late Move Reductions
            new_depth = derinlik - 1
            if (self.lmr_enabled and i >= 4 and derinlik >= 3 and 
                not self._onemli_hamle_mi(hamle) and legal_hamle_sayisi > 3):
                
                reduction = 1 if i < 8 else 2
                new_depth = max(0, derinlik - 1 - reduction)
                self.lmr_kesme += 1
            
            # Futility Pruning
            if (self.futility_enabled and derinlik <= 3 and 
                not self._onemli_hamle_mi(hamle)):
                
                futility_margin = 150 * derinlik
                if self.degerlendirme.degerlendir(tahta) + futility_margin <= alpha:
                    self.futility_kesme += 1
                    continue
            
            # PVS arama
            if i == 0:
                skor = -self._alpha_beta_pvs(tahta_kopyasi, new_depth, -beta, -alpha, True, ply + 1)
            else:
                # Null window search
                skor = -self._alpha_beta_pvs(tahta_kopyasi, new_depth, -alpha - 1, -alpha, True, ply + 1)
                
                # Re-search if needed
                if alpha < skor < beta and new_depth < derinlik - 1:
                    skor = -self._alpha_beta_pvs(tahta_kopyasi, derinlik - 1, -beta, -alpha, True, ply + 1)
            
            en_iyi_skor = max(en_iyi_skor, skor)
            alpha = max(alpha, skor)
            
            if beta <= alpha:
                # Killer move kaydet
                self._killer_move_kaydet(hamle, ply)
                self.kesme_sayisi += 1
                break
        
        return en_iyi_skor
    
    def _quiescence_search(self, tahta, alpha, beta, depth):
        """Quiescence search - sadece alma hamleleri"""
        self.dugum_sayisi += 1
        
        if depth > 4:  # Quiescence depth limit
            return self.degerlendirme.degerlendir(tahta)
        
        stand_pat = self.degerlendirme.degerlendir(tahta)
        
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
        
        # Sadece alma hamleleri
        captures = self._alma_hamleleri_bul(tahta)
        captures = sorted(captures, key=lambda x: self._hamle_degerlendir(x), reverse=True)
        
        for hamle in captures:
            # Delta pruning
            if self._delta_pruning_kontrolu(hamle, stand_pat, alpha):
                continue
                
            tahta_kopyasi = tahta.kopyala()
            if not tahta_kopyasi.hamle_yap(hamle):
                continue
            
            skor = -self._quiescence_search(tahta_kopyasi, -beta, -alpha, depth + 1)
            
            if skor >= beta:
                return beta
            if skor > alpha:
                alpha = skor
        
        return alpha
    
    def _hamleleri_sirala(self, tahta, hamleler):
        """Gelişmiş hamle sıralama"""
        def hamle_oncelik(hamle):
            puan = 0
            
            # 0. EN ÖNEMLİ: Mat veren hamleler (şah alma)
            hedef_kare = hamle[1]
            if tahta.bit_kontrol_et(hedef_kare):
                hedef_tas = tahta.tas_turu_al(hedef_kare)
                if hedef_tas and hedef_tas[1] == 'sah':
                    puan += 1000000  # ŞAH ALMA EN YÜKSEK ÖNCELİK!
                    return puan
            
            # Mat kontrolü - hamle sonrası mat oluyor mu?
            tahta_test = tahta.kopyala()
            if tahta_test.hamle_yap(hamle):
                if self.mat_kontrolcu.is_mate(tahta_test):
                    puan += 500000  # Mat pozisyonu ikinci öncelik
                    return puan
            
            # 1. Alma hamleleri (MVV-LVA)
            if tahta.bit_kontrol_et(hedef_kare):
                hedef_tas = tahta.tas_turu_al(hedef_kare)
                kaynak_tas = tahta.tas_turu_al(hamle[0])
                if hedef_tas and kaynak_tas:
                    puan += self._mvv_lva_skor(kaynak_tas[1], hedef_tas[1])
            
            # 2. Killer moves
            if hamle in self.killer_moves[min(len(self.killer_moves)-1, 10)]:
                puan += 1000
            
            # 3. History heuristic
            hamle_key = (hamle[0], hamle[1])
            puan += self.history_table.get(hamle_key, 0)
            
            # 4. Özel hamleler (rok, terfi vs.)
            if len(hamle) > 3 and hamle[3] in ['kisa_rok', 'uzun_rok', 'terfi']:
                puan += 500
            
            return puan
        
        return sorted(hamleler, key=hamle_oncelik, reverse=True)
    
    def _mvv_lva_skor(self, saldiran, hedef):
        """Most Valuable Victim - Least Valuable Attacker"""
        tas_degerleri = {'piyon': 1, 'at': 3, 'fil': 3, 'kale': 5, 'vezir': 9, 'sah': 0}
        return tas_degerleri.get(hedef, 0) * 10 - tas_degerleri.get(saldiran, 0)
    
    def _onemli_hamle_mi(self, hamle):
        """Hamlenin önemli olup olmadığını kontrol et"""
        # Alma hamleleri, şah veren hamleler, terfiler önemli
        return (len(hamle) > 3 and hamle[3] in ['alma', 'terfi', 'kisa_rok', 'uzun_rok'] or
                hamle[3] == 'sah')
    
    def _forward_pruning_kontrolu(self, hamle, derinlik, hamle_indeksi):
        """Forward pruning kontrolü"""
        if not self.forward_pruning_enabled:
            return False
        
        # Derinlik düşükse ve hamle çok geride ise atla
        if derinlik <= 2 and hamle_indeksi > 10:
            return True
        
        return False
    
    def _delta_pruning_kontrolu(self, hamle, stand_pat, alpha):
        """Delta pruning for quiescence"""
        # Eğer alma çok küçük bir kazanç sağlıyorsa atla
        hedef_deger = 100  # Varsayılan piyon değeri
        if stand_pat + hedef_deger + 200 < alpha:  # 200 = margin
            return True
        return False
    
    def _alma_hamleleri_bul(self, tahta):
        """Sadece alma hamleleri bul"""
        tum_hamleler = self.hamle_uretici.tum_hamleleri_uret(tahta)
        return [h for h in tum_hamleler if tahta.bit_kontrol_et(h[1])]
    
    def _hamle_degerlendir(self, hamle):
        """Hamlenin değerini tahmin et"""
        # Basit implementasyon
        return 0
    
    def _killer_move_kaydet(self, hamle, ply):
        """Killer move kaydet"""
        if ply < len(self.killer_moves):
            if hamle not in self.killer_moves[ply]:
                self.killer_moves[ply].insert(0, hamle)
                if len(self.killer_moves[ply]) > 2:
                    self.killer_moves[ply].pop()
    
    def _zaman_asildi(self):
        """Zaman sınırı aşıldı mı?"""
        if self.max_time is None:
            return False
        return time.time() - self.start_time > self.max_time
    
    def _istatistikleri_sifirla(self):
        """İstatistikleri sıfırla"""
        self.dugum_sayisi = 0
        self.kesme_sayisi = 0
        self.null_move_kesme = 0
        self.lmr_kesme = 0
        self.futility_kesme = 0
    
    def _istatistikleri_yazdir(self):
        """İstatistikleri yazdır"""
        print(f"Düğüm: {self.dugum_sayisi}, Kesme: {self.kesme_sayisi}")
        print(f"Null Move: {self.null_move_kesme}, LMR: {self.lmr_kesme}, Futility: {self.futility_kesme}")
    
    def get_istatistikler(self):
        """İstatistikleri döndür"""
        return {
            'dugum_sayisi': self.dugum_sayisi,
            'kesme_sayisi': self.kesme_sayisi,
            'null_move_kesme': self.null_move_kesme,
            'lmr_kesme': self.lmr_kesme,
            'futility_kesme': self.futility_kesme,
            'derinlik': self.derinlik
        }