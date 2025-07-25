"""
MiniMax ve Alpha-Beta Pruning algoritmaları.
Derinlik bazlı arama.
Gelecekte iterative deepening ve zaman kontrolü eklenecek.
"""

from HamleUret import HamleUretici
from Degerlendirme import Degerlendirici
import copy


class Arama:
    def __init__(self, derinlik=6):
        self.derinlik = derinlik
        self.hamle_uretici = HamleUretici()
        self.degerlendirme = Degerlendirici()
        self.dugum_sayisi = 0
        self.max_derinlik = 0

    def derinlik_degistir(self, yeni_derinlik):
        """Arama derinliğini değiştir"""
        self.derinlik = yeni_derinlik

    def en_iyi_hamle_bul(self, tahta):
        """Alpha-Beta pruning ile en iyi hamleyi bul"""
        self.dugum_sayisi = 0
        self.max_derinlik = 0

        en_iyi_hamle = None
        en_iyi_skor = float('-inf') if tahta.beyaz_sira else float('inf')

        try:
            hamleler = self.hamle_uretici.tum_hamleleri_uret(tahta)

            # Hamle yoksa None döndür
            if not hamleler:
                return None

            # Hamleleri sırala (basit sıralama - alma hamleleri önce)
            hamleler = self._hamleleri_sirala(tahta, hamleler)

            for i, hamle in enumerate(hamleler):
                try:
                    # Hamleyi yap
                    tahta_kopyasi = tahta.kopyala()  # deepcopy yerine kendi kopyala metodunu kullan
                    
                    if not tahta_kopyasi.hamle_yap(hamle):
                        continue  # Geçersiz hamle, atla

                    if tahta.beyaz_sira:  # Beyaz oynuyor (maksimize)
                        skor = self.alpha_beta(tahta_kopyasi, self.derinlik - 1, float('-inf'), float('inf'), False)
                        if skor > en_iyi_skor:
                            en_iyi_skor = skor
                            en_iyi_hamle = hamle
                    else:  # Siyah oynuyor (minimize)
                        skor = self.alpha_beta(tahta_kopyasi, self.derinlik - 1, float('-inf'), float('inf'), True)
                        if skor < en_iyi_skor:
                            en_iyi_skor = skor
                            en_iyi_hamle = hamle

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Arama genel hatası: {e}")

        return en_iyi_hamle

    def _hamleleri_sirala(self, tahta, hamleler):
        """Hamleleri sırala (alma hamleleri önce)"""
        alma_hamleler = []
        normal_hamleler = []
        
        for hamle in hamleler:
            hedef_kare = hamle[1]
            if tahta.bit_kontrol_et(hedef_kare):  # Hedef karede taş var
                alma_hamleler.append(hamle)
            else:
                normal_hamleler.append(hamle)
        
        return alma_hamleler + normal_hamleler

    def alpha_beta(self, tahta, derinlik, alpha, beta, maksimize_ediyor):
        """Alpha-Beta pruning algoritması"""
        self.dugum_sayisi += 1
        self.max_derinlik = max(self.max_derinlik, self.derinlik - derinlik)

        # Terminal düğüm kontrolü
        if derinlik == 0:
            return self.degerlendirme.degerlendir(tahta)

        hamleler = self.hamle_uretici.tum_hamleleri_uret(tahta)

        # Hamle yoksa (pat/mat durumu)
        if not hamleler:
            # Şah durumu kontrolü yapılmalı - basit bir yaklaşım
            return self.degerlendirme.degerlendir(tahta)

        if maksimize_ediyor:
            max_eval = float('-inf')
            for hamle in hamleler:
                tahta_kopyasi = copy.deepcopy(tahta)
                tahta_kopyasi.hamle_yap(hamle)

                eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_skor)
                alpha = max(alpha, eval_skor)

                if beta <= alpha:
                    break  # Beta cutoff

            return max_eval
        else:
            min_eval = float('inf')
            for hamle in hamleler:
                tahta_kopyasi = copy.deepcopy(tahta)
                tahta_kopyasi.hamle_yap(hamle)

                eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_skor)
                beta = min(beta, eval_skor)

                if beta <= alpha:
                    break  # Alpha cutoff

            return min_eval

    def minimax(self, tahta, derinlik, maksimize_ediyor):
        """Basit MiniMax algoritması (Alpha-Beta olmadan)"""
        self.dugum_sayisi += 1

        # Terminal düğüm kontrolü
        if derinlik == 0:
            return self.degerlendirme.degerlendir(tahta)

        hamleler = self.hamle_uretici.tum_hamleleri_uret(tahta)

        # Hamle yoksa
        if not hamleler:
            return self.degerlendirme.degerlendir(tahta)

        if maksimize_ediyor:
            max_eval = float('-inf')
            for hamle in hamleler:
                tahta_kopyasi = copy.deepcopy(tahta)
                tahta_kopyasi.hamle_yap(hamle)

                eval_skor = self.minimax(tahta_kopyasi, derinlik - 1, False)
                max_eval = max(max_eval, eval_skor)

            return max_eval
        else:
            min_eval = float('inf')
            for hamle in hamleler:
                tahta_kopyasi = copy.deepcopy(tahta)
                tahta_kopyasi.hamle_yap(hamle)

                eval_skor = self.minimax(tahta_kopyasi, derinlik - 1, True)
                min_eval = min(min_eval, eval_skor)

            return min_eval

    def get_istatistikler(self):
        """Arama istatistiklerini döndür"""
        return {
            'dugum_sayisi': self.dugum_sayisi,
            'max_derinlik': self.max_derinlik,
            'derinlik': self.derinlik
        }