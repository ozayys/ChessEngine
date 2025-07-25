"""
Pozisyon değerlendirme modülü. Taş değerleri, pozisyonel faktörler ve
piece-square table tabanlı değerlendirme sistemi.
"""


class Degerlendirici:
    def __init__(self):
        # Temel taş değerleri (centipawn cinsinden)
        self.tas_degerleri = {
            'piyon': 100,
            'at': 320,
            'fil': 330,
            'kale': 500,
            'vezir': 900,
            'sah': 0  # Şah değeri sonsuz olarak kabul edilir
        }

        # Piece-Square Tables (PST) - açılış/orta oyun için
        self._pst_tablolarini_olustur()

        # Oyun fazı tespiti için malzeme değerleri
        self.faz_malzeme_degerleri = {
            'piyon': 0, 'at': 1, 'fil': 1, 'kale': 2, 'vezir': 4
        }

        # Maksimum malzeme skoru (açılış pozisyonu)
        self.max_malzeme_skoru = 78  # 16*0 + 4*1 + 4*1 + 4*2 + 2*4

    def degerlendir(self, tahta):
        """Arama modülü tarafından çağrılan ana değerlendirme fonksiyonu"""
        # Arama algoritması için: mevcut sıradaki oyuncunun perspektifinden
        skor = self.pozisyon_degerlendir(tahta)
        return skor if tahta.beyaz_sira else -skor

    def _pst_tablolarini_olustur(self):
        """Piece-Square Table tablolarını oluştur"""

        # Piyon PST (beyaz perspektifinden)
        self.piyon_pst = [
            0, 0, 0, 0, 0, 0, 0, 0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5, 5, 10, 25, 25, 10, 5, 5,
            0, 0, 0, 20, 20, 0, 0, 0,
            5, -5, -10, 0, 0, -10, -5, 5,
            5, 10, 10, -20, -20, 10, 10, 5,
            0, 0, 0, 0, 0, 0, 0, 0
        ]

        # At PST
        self.at_pst = [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20, 0, 0, 0, 0, -20, -40,
            -30, 0, 10, 15, 15, 10, 0, -30,
            -30, 5, 15, 20, 20, 15, 5, -30,
            -30, 0, 15, 20, 20, 15, 0, -30,
            -30, 5, 10, 15, 15, 10, 5, -30,
            -40, -20, 0, 5, 5, 0, -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50
        ]

        # Fil PST
        self.fil_pst = [
            -20, -10, -10, -10, -10, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 5, 10, 10, 5, 0, -10,
            -10, 5, 5, 10, 10, 5, 5, -10,
            -10, 0, 10, 10, 10, 10, 0, -10,
            -10, 10, 10, 10, 10, 10, 10, -10,
            -10, 5, 0, 0, 0, 0, 5, -10,
            -20, -10, -10, -10, -10, -10, -10, -20
        ]

        # Kale PST
        self.kale_pst = [
            0, 0, 0, 0, 0, 0, 0, 0,
            5, 10, 10, 10, 10, 10, 10, 5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            0, 0, 0, 5, 5, 0, 0, 0
        ]

        # Vezir PST
        self.vezir_pst = [
            -20, -10, -10, -5, -5, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 5, 5, 5, 5, 0, -10,
            -5, 0, 5, 5, 5, 5, 0, -5,
            0, 0, 5, 5, 5, 5, 0, -5,
            -10, 5, 5, 5, 5, 5, 0, -10,
            -10, 0, 5, 0, 0, 0, 0, -10,
            -20, -10, -10, -5, -5, -10, -10, -20
        ]

        # Şah PST (açılış/orta oyun)
        self.sah_acilis_pst = [
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -10, -20, -20, -20, -20, -20, -20, -10,
            20, 20, 0, 0, 0, 0, 20, 20,
            20, 30, 10, 0, 0, 10, 30, 20
        ]

        # Şah PST (son oyun)
        self.sah_son_pst = [
            -50, -40, -30, -20, -20, -30, -40, -50,
            -30, -20, -10, 0, 0, -10, -20, -30,
            -30, -10, 20, 30, 30, 20, -10, -30,
            -30, -10, 30, 40, 40, 30, -10, -30,
            -30, -10, 30, 40, 40, 30, -10, -30,
            -30, -10, 20, 30, 30, 20, -10, -30,
            -30, -30, 0, 0, 0, 0, -30, -30,
            -50, -30, -30, -30, -30, -30, -30, -50
        ]

        # PST lookup dictionary
        self.pst_tablosu = {
            'piyon': self.piyon_pst,
            'at': self.at_pst,
            'fil': self.fil_pst,
            'kale': self.kale_pst,
            'vezir': self.vezir_pst,
            'sah': self.sah_acilis_pst  # Varsayılan olarak açılış PST
        }

    def pozisyon_degerlendir(self, tahta):
        """Ana değerlendirme fonksiyonu"""
        skor = 0

        # Malzeme ve pozisyonel değerlendirme
        skor += self.malzeme_dengesi_hesapla(tahta)
        skor += self.pozisyonel_deger_hesapla(tahta)

        # Mobilite değerlendirmesi
        try:
            skor += self.mobilite_hesapla(tahta)
        except:
            # Mobilite hesaplaması başarısız olursa pas geç
            pass

        # Şah güvenliği
        try:
            skor += self.sah_guvenlik_hesapla(tahta)
        except:
            # Şah güvenliği hesaplaması başarısız olursa pas geç
            pass

        # Piyon yapısı
        try:
            skor += self.piyon_yapisi_hesapla(tahta)
        except:
            # Piyon yapısı hesaplaması başarısız olursa pas geç
            pass

        # Her zaman beyaz perspektifinden döndür (pozitif = beyaz iyi, negatif = siyah iyi)
        return skor

    def malzeme_dengesi_hesapla(self, tahta):
        """Malzeme dengesini hesapla"""
        beyaz_malzeme = 0
        siyah_malzeme = 0

        try:
            # Bitboard'ları kullanarak hızlı hesaplama
            beyaz_malzeme += tahta.bit_sayisi(tahta.beyaz_piyon) * self.tas_degerleri['piyon']
            beyaz_malzeme += tahta.bit_sayisi(tahta.beyaz_at) * self.tas_degerleri['at']
            beyaz_malzeme += tahta.bit_sayisi(tahta.beyaz_fil) * self.tas_degerleri['fil']
            beyaz_malzeme += tahta.bit_sayisi(tahta.beyaz_kale) * self.tas_degerleri['kale']
            beyaz_malzeme += tahta.bit_sayisi(tahta.beyaz_vezir) * self.tas_degerleri['vezir']

            siyah_malzeme += tahta.bit_sayisi(tahta.siyah_piyon) * self.tas_degerleri['piyon']
            siyah_malzeme += tahta.bit_sayisi(tahta.siyah_at) * self.tas_degerleri['at']
            siyah_malzeme += tahta.bit_sayisi(tahta.siyah_fil) * self.tas_degerleri['fil']
            siyah_malzeme += tahta.bit_sayisi(tahta.siyah_kale) * self.tas_degerleri['kale']
            siyah_malzeme += tahta.bit_sayisi(tahta.siyah_vezir) * self.tas_degerleri['vezir']
        except:
            # Bitboard metodları yoksa basit malzeme sayımı yap
            for kare in range(64):
                tas_info = tahta.karedeki_tas(kare)
                if tas_info:
                    renk, tas_turu = tas_info
                    if tas_turu in self.tas_degerleri:
                        if renk == 'beyaz':
                            beyaz_malzeme += self.tas_degerleri[tas_turu]
                        else:
                            siyah_malzeme += self.tas_degerleri[tas_turu]

        return beyaz_malzeme - siyah_malzeme

    def pozisyonel_deger_hesapla(self, tahta):
        """Piece-Square Table kullanarak pozisyonel değer hesapla"""
        skor = 0

        try:
            oyun_fazi = self.oyun_fazi_hesapla(tahta)
        except:
            oyun_fazi = 0.5  # Varsayılan orta oyun

        # Tüm taşlar için PST değerlerini hesapla
        for kare in range(64):
            try:
                tas_bilgisi = tahta.karedeki_tas(kare)
                if tas_bilgisi:
                    renk, tur = tas_bilgisi
                    pst_degeri = self.pst_deger_al(tur, kare, renk, oyun_fazi)

                    if renk == 'beyaz':
                        skor += pst_degeri
                    else:
                        skor -= pst_degeri
            except:
                continue

        return skor

    def pst_deger_al(self, tas_turu, kare, renk, oyun_fazi):
        """Belirtilen taş ve kare için PST değeri al"""
        if tas_turu == 'sah':
            # Şah için oyun fazına göre PST seç
            if oyun_fazi > 0.5:  # Son oyun
                pst = self.sah_son_pst
            else:  # Açılış/orta oyun
                pst = self.sah_acilis_pst
        else:
            pst = self.pst_tablosu.get(tas_turu, [0] * 64)

        # Siyah taşlar için kareyi çevir (flip)
        if renk == 'siyah':
            kare = 63 - kare

        return pst[kare] if kare < len(pst) else 0

    def oyun_fazi_hesapla(self, tahta):
        """Oyun fazını hesapla (0=açılış, 1=son oyun)"""
        try:
            mevcut_malzeme = 0

            # Piyon hariç malzeme sayısını hesapla
            mevcut_malzeme += tahta.bit_sayisi(tahta.beyaz_at) * self.faz_malzeme_degerleri['at']
            mevcut_malzeme += tahta.bit_sayisi(tahta.beyaz_fil) * self.faz_malzeme_degerleri['fil']
            mevcut_malzeme += tahta.bit_sayisi(tahta.beyaz_kale) * self.faz_malzeme_degerleri['kale']
            mevcut_malzeme += tahta.bit_sayisi(tahta.beyaz_vezir) * self.faz_malzeme_degerleri['vezir']

            mevcut_malzeme += tahta.bit_sayisi(tahta.siyah_at) * self.faz_malzeme_degerleri['at']
            mevcut_malzeme += tahta.bit_sayisi(tahta.siyah_fil) * self.faz_malzeme_degerleri['fil']
            mevcut_malzeme += tahta.bit_sayisi(tahta.siyah_kale) * self.faz_malzeme_degerleri['kale']
            mevcut_malzeme += tahta.bit_sayisi(tahta.siyah_vezir) * self.faz_malzeme_degerleri['vezir']

            # Oyun fazı oranını hesapla
            faz_orani = 1.0 - (mevcut_malzeme / self.max_malzeme_skoru)
            return max(0.0, min(1.0, faz_orani))
        except:
            return 0.5  # Varsayılan orta oyun

    def mobilite_hesapla(self, tahta):
        """Taş mobilitesini hesapla"""
        # Basit mobilite hesaplama - geliştirilmesi gerekebilir
        try:
            from HamleUret import HamleUretici
            hamle_uretici = HamleUretici()

            # Mevcut sırayı kaydet
            orijinal_sira = tahta.beyaz_sira

            # Beyaz hamleleri
            tahta.beyaz_sira = True
            beyaz_hamleler = len(hamle_uretici.tum_hamleleri_uret(tahta))

            # Siyah hamleleri
            tahta.beyaz_sira = False
            siyah_hamleler = len(hamle_uretici.tum_hamleleri_uret(tahta))

            # Sırayı geri yükle
            tahta.beyaz_sira = orijinal_sira

            mobilite_fark = (beyaz_hamleler - siyah_hamleler) * 5
            return mobilite_fark
        except:
            return 0

    def sah_guvenlik_hesapla(self, tahta):
        """Şah güvenliğini hesapla"""
        try:
            skor = 0

            # Basit şah güvenliği - rokun yapılıp yapılmadığı
            if hasattr(tahta, 'beyaz_kisa_rok') and not tahta.beyaz_kisa_rok and not tahta.beyaz_uzun_rok:
                # Beyaz rok yapmış (veya hakkını kaybetmiş)
                skor += 50

            if hasattr(tahta, 'siyah_kisa_rok') and not tahta.siyah_kisa_rok and not tahta.siyah_uzun_rok:
                # Siyah rok yapmış (veya hakkını kaybetmiş)
                skor -= 50

            return skor
        except:
            return 0

    def piyon_yapisi_hesapla(self, tahta):
        """Piyon yapısını değerlendir"""
        try:
            skor = 0

            # Çiftlenmiş piyonları penalize et
            skor -= self.ciftlenmis_piyon_penaltisi(tahta, True) * 50  # Beyaz
            skor += self.ciftlenmis_piyon_penaltisi(tahta, False) * 50  # Siyah

            # İzole piyonları penalize et
            skor -= self.izole_piyon_penaltisi(tahta, True) * 20  # Beyaz
            skor += self.izole_piyon_penaltisi(tahta, False) * 20  # Siyah

            # Geçer piyonları ödüllendir
            skor += self.gecer_piyon_bonusu(tahta, True) * 20  # Beyaz
            skor -= self.gecer_piyon_bonusu(tahta, False) * 20  # Siyah

            return skor
        except:
            return 0

    def ciftlenmis_piyon_penaltisi(self, tahta, beyaz):
        """Çiftlenmiş piyon sayısını hesapla"""
        try:
            piyonlar = tahta.beyaz_piyon if beyaz else tahta.siyah_piyon
            ciftlenmis_sayisi = 0

            for sutun in range(8):
                sutun_maski = 0x0101010101010101 << sutun
                sutun_piyonlari = piyonlar & sutun_maski
                piyon_sayisi = tahta.bit_sayisi(sutun_piyonlari)

                if piyon_sayisi > 1:
                    ciftlenmis_sayisi += piyon_sayisi - 1

            return ciftlenmis_sayisi
        except:
            return 0

    def izole_piyon_penaltisi(self, tahta, beyaz):
        """İzole piyon sayısını hesapla"""
        try:
            piyonlar = tahta.beyaz_piyon if beyaz else tahta.siyah_piyon
            izole_sayisi = 0

            for sutun in range(8):
                sutun_maski = 0x0101010101010101 << sutun
                sutun_piyonlari = piyonlar & sutun_maski

                if sutun_piyonlari != 0:
                    # Komşu sütunlarda piyon var mı kontrol et
                    komsu_var = False

                    if sutun > 0:  # Sol komşu
                        sol_maski = 0x0101010101010101 << (sutun - 1)
                        if piyonlar & sol_maski:
                            komsu_var = True

                    if sutun < 7:  # Sağ komşu
                        sag_maski = 0x0101010101010101 << (sutun + 1)
                        if piyonlar & sag_maski:
                            komsu_var = True

                    if not komsu_var:
                        izole_sayisi += 1

            return izole_sayisi
        except:
            return 0

    def gecer_piyon_bonusu(self, tahta, beyaz):
        """Geçer piyon sayısını hesapla"""
        # Basitleştirilmiş geçer piyon tespiti
        # Gerçek implementasyon daha karmaşık olmalı
        return 0  # Şimdilik implementasyon yok

    def mat_skoru(self, derinlik):
        """Mat skorunu hesapla"""
        return 30000 - derinlik

    def skor_mat_mi(self, skor):
        """Skor mat skoru mu kontrol et"""
        return abs(skor) > 25000