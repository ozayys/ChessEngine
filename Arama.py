"""
MiniMax ve Alpha-Beta Pruning algoritmaları.
Derinlik bazlı arama.
Gelecekte iterative deepening ve zaman kontrolü eklenecek.
"""

from HamleUret import HamleUretici
from Degerlendirme import Degerlendirici
import copy
from LegalHamle import LegalHamleBulucu


class Arama:
    def __init__(self, derinlik=6):
        self.derinlik = derinlik
        self.hamle_uretici = HamleUretici()
        self.degerlendirme = Degerlendirici()
        self.legal_bulucu = LegalHamleBulucu()  # LegalHamleBulucu örneği
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

        hamleler = self.hamle_uretici.tum_hamleleri_uret(tahta)

        # Hamle yoksa None döndür
        if not hamleler:
            return None

        for hamle in hamleler:
            # Hamleyi yap
            tahta_kopyasi = copy.deepcopy(tahta)
            tahta_kopyasi.hamle_yap(hamle)

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

        print(f"Arama tamamlandı: {self.dugum_sayisi} düğüm değerlendirildi, maksimum derinlik: {self.max_derinlik}")
        return en_iyi_hamle

    def alpha_beta(self, tahta, derinlik, alpha, beta, maksimize_ediyor):
        """Alpha-Beta pruning algoritması"""
        self.dugum_sayisi += 1
        self.max_derinlik = max(self.max_derinlik, self.derinlik - derinlik)

        # Terminal düğüm kontrolü (mat/pat)
        if self.legal_bulucu.mat_mi(tahta):
            # Mat olan taraf kaybetti, skor derinliğe göre mate-in-N
            if tahta.beyaz_sira:
                # Beyaz mat oldu, siyah kazandı
                return -self.degerlendirme.mat_skoru(self.derinlik - derinlik)
            else:
                # Siyah mat oldu, beyaz kazandı
                return self.degerlendirme.mat_skoru(self.derinlik - derinlik)
        if self.legal_bulucu.pat_mi(tahta):
            return 0  # Pat, beraberlik
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

        # Terminal düğüm kontrolü (mat/pat)
        if self.legal_bulucu.mat_mi(tahta):
            if tahta.beyaz_sira:
                return -self.degerlendirme.mat_skoru(self.derinlik - derinlik)
            else:
                return self.degerlendirme.mat_skoru(self.derinlik - derinlik)
        if self.legal_bulucu.pat_mi(tahta):
            return 0
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