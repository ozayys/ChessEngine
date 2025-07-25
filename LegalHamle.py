"""
Legal hamle bulucu. Pseudo-legal hamleleri alır ve legal olanları filtreler.
Şah kontrolü ve geçici hamle uygulama sistemi.
"""

from HamleUret import HamleUretici


class LegalHamleBulucu:
    def __init__(self):
        self.hamle_uretici = HamleUretici()
        self.legal_hamleler = []

    def legal_hamleleri_bul(self, tahta):
        """Mevcut pozisyon için tüm legal hamleleri bul"""
        self.legal_hamleler = []
        pseudo_legal_hamleler = self.hamle_uretici.tum_hamleleri_uret(tahta)

        for hamle in pseudo_legal_hamleler:
            if self.hamle_legal_mi(tahta, hamle):
                self.legal_hamleler.append(hamle)

        return self.legal_hamleler

    def hamle_legal_mi(self, tahta, hamle):
        """Belirtilen hamle legal mi kontrol et"""
        # Geçici hamle uygula
        onceki_durum = self.hamle_uygula_gecici(tahta, hamle)

        # Şah tehdidinde mi kontrol et
        legal = not self.sah_tehdidinde_mi(tahta, not tahta.beyaz_sira)

        # Hamleyi geri al
        self.hamle_geri_al(tahta, hamle, onceki_durum)

        return legal

    def hamle_uygula_gecici(self, tahta, hamle):
        """Hamleyi geçici olarak uygula ve önceki durumu kaydet"""
        kaynak, hedef = hamle[0], hamle[1]
        hamle_turu = hamle[3] if len(hamle) > 3 else 'normal'

        # Önceki durumu kaydet
        onceki_durum = {
            'hedef_tas': tahta.tas_turu_al(hedef),
            'kaynak_tas': tahta.tas_turu_al(kaynak),
            'beyaz_sira': tahta.beyaz_sira,
            'en_passant_kare': tahta.en_passant_kare,
            'beyaz_kisa_rok': tahta.beyaz_kisa_rok,
            'beyaz_uzun_rok': tahta.beyaz_uzun_rok,
            'siyah_kisa_rok': tahta.siyah_kisa_rok,
            'siyah_uzun_rok': tahta.siyah_uzun_rok,
            'hamle_turu': hamle_turu,
            'yarim_hamle_sayici': tahta.yarim_hamle_sayici,
            'hamle_sayisi': tahta.hamle_sayisi
        }

        # Özel hamle durumları için ek bilgiler
        if hamle_turu == 'en_passant':
            onceki_durum['en_passant_hedef'] = tahta.en_passant_kare + (-8 if tahta.beyaz_sira else 8)
            onceki_durum['alinen_piyon'] = tahta.tas_turu_al(onceki_durum['en_passant_hedef'])

        # Hamleyi uygula
        self._hamle_isle(tahta, hamle)

        return onceki_durum

    def hamle_geri_al(self, tahta, hamle, onceki_durum):
        """Geçici hamleyi geri al"""
        kaynak, hedef = hamle[0], hamle[1]
        hamle_turu = onceki_durum['hamle_turu']

        # Durumları geri yükle
        tahta.beyaz_sira = onceki_durum['beyaz_sira']
        tahta.en_passant_kare = onceki_durum['en_passant_kare']
        tahta.beyaz_kisa_rok = onceki_durum['beyaz_kisa_rok']
        tahta.beyaz_uzun_rok = onceki_durum['beyaz_uzun_rok']
        tahta.siyah_kisa_rok = onceki_durum['siyah_kisa_rok']
        tahta.siyah_uzun_rok = onceki_durum['siyah_uzun_rok']
        tahta.yarim_hamle_sayici = onceki_durum['yarim_hamle_sayici']
        tahta.hamle_sayisi = onceki_durum['hamle_sayisi']

        # Taşları geri yerleştir
        tahta.tas_kaldir(hedef)
        if onceki_durum['kaynak_tas']:
            renk, tur = onceki_durum['kaynak_tas']
            tahta.tas_ekle(kaynak, renk, tur)

        if onceki_durum['hedef_tas']:
            renk, tur = onceki_durum['hedef_tas']
            tahta.tas_ekle(hedef, renk, tur)

        # Özel hamle geri alma işlemleri
        if hamle_turu == 'kisa_rok':
            if onceki_durum['beyaz_sira']:  # Beyaz rok
                tahta.tas_kaldir(5)  # f1'deki kaleyi kaldır
                tahta.tas_ekle(7, 'beyaz', 'kale')  # h1'e geri koy
            else:  # Siyah rok
                tahta.tas_kaldir(61)  # f8'deki kaleyi kaldır
                tahta.tas_ekle(63, 'siyah', 'kale')  # h8'e geri koy

        elif hamle_turu == 'uzun_rok':
            if onceki_durum['beyaz_sira']:  # Beyaz rok
                tahta.tas_kaldir(3)  # d1'deki kaleyi kaldır
                tahta.tas_ekle(0, 'beyaz', 'kale')  # a1'e geri koy
            else:  # Siyah rok
                tahta.tas_kaldir(59)  # d8'deki kaleyi kaldır
                tahta.tas_ekle(56, 'siyah', 'kale')  # a8'e geri koy

        elif hamle_turu == 'en_passant':
            # Alınan piyonu geri koy
            if onceki_durum['alinen_piyon']:
                renk, tur = onceki_durum['alinen_piyon']
                tahta.tas_ekle(onceki_durum['en_passant_hedef'], renk, tur)

    def _hamle_isle(self, tahta, hamle):
        """Hamleyi işle (özel hamle türlerine göre)"""
        kaynak, hedef = hamle[0], hamle[1]
        tas_turu = hamle[2]
        hamle_turu = hamle[3] if len(hamle) > 3 else 'normal'

        # Kaynak taşın bilgisini al
        tas_bilgisi = tahta.tas_turu_al(kaynak)
        if not tas_bilgisi:
            return False

        renk, tur = tas_bilgisi

        # Rok haklarını güncelle
        self._rok_haklarini_guncelle(tahta, kaynak, hedef, renk, tur)

        # En passant karesi güncelleme
        tahta.en_passant_kare = -1

        if hamle_turu == 'iki_kare':
            # İki kare piyon hamlesi - en passant karesi belirle
            tahta.en_passant_kare = (kaynak + hedef) // 2

        elif hamle_turu == 'en_passant':
            # En passant alma - alınan piyonu kaldır
            alinen_piyon_kare = hedef + (-8 if renk == 'beyaz' else 8)
            tahta.tas_kaldir(alinen_piyon_kare)

        elif hamle_turu == 'kisa_rok':
            # Kısa rok - kaleyi de hareket ettir
            if renk == 'beyaz':
                tahta.tas_kaldir(7)  # h1
                tahta.tas_ekle(5, 'beyaz', 'kale')  # f1
            else:
                tahta.tas_kaldir(63)  # h8
                tahta.tas_ekle(61, 'siyah', 'kale')  # f8

        elif hamle_turu == 'uzun_rok':
            # Uzun rok - kaleyi de hareket ettir
            if renk == 'beyaz':
                tahta.tas_kaldir(0)  # a1
                tahta.tas_ekle(3, 'beyaz', 'kale')  # d1
            else:
                tahta.tas_kaldir(56)  # a8
                tahta.tas_ekle(59, 'siyah', 'kale')  # d8

        elif hamle_turu in ['terfi', 'terfi_alma']:
            # Piyon terfisi
            terfi_tasi = hamle[4] if len(hamle) > 4 else 'vezir'
            tahta.tas_kaldir(hedef)  # Hedef karedeki taşı kaldır
            tahta.tas_kaldir(kaynak)  # Kaynak karedeki piyonu kaldır
            tahta.tas_ekle(hedef, renk, terfi_tasi)  # Terfi olan taşı yerleştir
            tahta.beyaz_sira = not tahta.beyaz_sira
            return True

        # Normal hamle işlemi
        tahta.tas_kaldir(hedef)  # Hedef karedeki taşı kaldır (varsa)
        tahta.tas_kaldir(kaynak)  # Kaynak karedeki taşı kaldır
        tahta.tas_ekle(hedef, renk, tur)  # Taşı hedef kareye yerleştir

        # Sırayı değiştir
        tahta.beyaz_sira = not tahta.beyaz_sira

        return True

    def _rok_haklarini_guncelle(self, tahta, kaynak, hedef, renk, tur):
        """Rok haklarını güncelle"""
        if tur == 'sah':
            if renk == 'beyaz':
                tahta.beyaz_kisa_rok = False
                tahta.beyaz_uzun_rok = False
            else:
                tahta.siyah_kisa_rok = False
                tahta.siyah_uzun_rok = False

        elif tur == 'kale':
            if renk == 'beyaz':
                if kaynak == 0:  # a1
                    tahta.beyaz_uzun_rok = False
                elif kaynak == 7:  # h1
                    tahta.beyaz_kisa_rok = False
            else:
                if kaynak == 56:  # a8
                    tahta.siyah_uzun_rok = False
                elif kaynak == 63:  # h8
                    tahta.siyah_kisa_rok = False

        # Hedef karedeki kale yakalandıysa rok haklarını kaldır
        if hedef == 0:  # a1
            tahta.beyaz_uzun_rok = False
        elif hedef == 7:  # h1
            tahta.beyaz_kisa_rok = False
        elif hedef == 56:  # a8
            tahta.siyah_uzun_rok = False
        elif hedef == 63:  # h8
            tahta.siyah_kisa_rok = False

    def sah_tehdidinde_mi(self, tahta, beyaz):
        """Belirtilen rengin şahı tehdit altında mı"""
        # Şahın pozisyonunu bul
        sah_bitboard = tahta.beyaz_sah if beyaz else tahta.siyah_sah
        if sah_bitboard == 0:
            return False  # Şah bulunamadı

        sah_pozisyonu = tahta.en_dusuk_bit_al(sah_bitboard)

        # Karşı tarafın saldırı kontrolü
        return self.hamle_uretici.saldiri_altinda_mi(tahta, sah_pozisyonu, not beyaz)

    def mat_mi(self, tahta):
        """Mat durumu kontrolü"""
        legal_hamleler = self.legal_hamleleri_bul(tahta)
        sah_tehdidinde = self.sah_tehdidinde_mi(tahta, tahta.beyaz_sira)

        return len(legal_hamleler) == 0 and sah_tehdidinde

    def pat_mi(self, tahta):
        """Pat durumu kontrolü"""
        legal_hamleler = self.legal_hamleleri_bul(tahta)
        sah_tehdidinde = self.sah_tehdidinde_mi(tahta, tahta.beyaz_sira)

        return len(legal_hamleler) == 0 and not sah_tehdidinde

    def oyun_bitti_mi(self, tahta):
        """Oyun bitmiş mi kontrol et"""
        return self.mat_mi(tahta) or self.pat_mi(tahta)

    def hamle_sayisi(self, tahta):
        """Mevcut pozisyondaki legal hamle sayısı"""
        return len(self.legal_hamleleri_bul(tahta))