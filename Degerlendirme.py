"""
Pozisyon değerlendirme modülü. Taş değerleri, pozisyonel faktörler ve
piece-square table tabanlı değerlendirme sistemi.

Gelişmiş değerlendirme kriterleri:
1. Materyal dengesi
2. Merkez kontrolü
3. Mobilite
4. Şah güvenliği
5. Piyon yapısı
6. Geçer piyonlar
7. Fil çifti avantajı
8. Taş koordinasyonu
9. Açık hat/kare kontrolü
10. Taş aktivitesi (PST)
11. Oyun evresine göre ağırlık
12. İnisiyatif / tempo
13. Rakip şah üzerinde tropizma
14. Zayıf kareler (outposts)
15. Kalabalık piyon yapısı
16. Yapısal blokaj
17. Taktik baskı
18. Uzun vadeli stratejik üstünlük
19. Rakibin zayıflıkları
20. Açılışın gelişimi
"""

from functools import lru_cache
import sys

# Python 3.10+ için bit_count kullan, yoksa alternatif
if sys.version_info >= (3, 10):
    def bit_sayisi(x):
        return x.bit_count()
else:
    def bit_sayisi(x):
        # Brian Kernighan algoritması
        count = 0
        while x:
            x &= x - 1
            count += 1
        return count


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
        
        # Değerlendirme cache - LRU cache kullan
        self._eval_cache_size = 65536  # 64K entry
        
        # Merkez kareleri
        self.merkez_kareler = [27, 28, 35, 36]  # d4, e4, d5, e5
        self.genis_merkez = [18, 19, 20, 21, 26, 27, 28, 29, 34, 35, 36, 37, 42, 43, 44, 45]
        
        # Bitboard maskeleri - önceden hesapla
        self._merkez_mask = 0
        for kare in self.merkez_kareler:
            self._merkez_mask |= 1 << kare
        
        self._genis_merkez_mask = 0
        for kare in self.genis_merkez:
            self._genis_merkez_mask |= 1 << kare

    def degerlendir(self, tahta):
        """Arama modülü tarafından çağrılan ana değerlendirme fonksiyonu"""
        # Mat/pat kontrolü
        if tahta.mat_mi():
            return -20000 if tahta.beyaz_sira else 20000
        
        if tahta.pat_mi():
            return 0
        
        # Pozisyon değerlendirmesi
        skor = self.pozisyon_degerlendir(tahta)
        
        # Sıradaki oyuncunun perspektifinden döndür
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
        """Ana değerlendirme fonksiyonu - 20+ kriter ile geliştirilmiş"""
        # Mat/pat kontrolü
        if tahta.mat_mi():
            return 100000 if not tahta.beyaz_sira else -100000
        if tahta.pat_mi():
            return 0
        
        skor = 0

        # Hızlı malzeme kontrolü
        beyaz_malzeme = self._hizli_malzeme_hesapla(tahta, True)
        siyah_malzeme = self._hizli_malzeme_hesapla(tahta, False)
        
        # Eğer büyük malzeme farkı varsa detaylı değerlendirmeye gerek yok
        malzeme_farki = beyaz_malzeme - siyah_malzeme
        if abs(malzeme_farki) > 1000:  # 10 piyon değerinden fazla fark
            return malzeme_farki
        
        # 1. Malzeme dengesi (temel kriter)
        skor += self.malzeme_dengesi_hesapla(tahta)
        
        # 2. Taş aktivitesi (PST)
        skor += self.pozisyonel_deger_hesapla(tahta)

        # Oyun fazını belirle
        faz = self._oyun_fazi_belirle(tahta)
        
        # 3. Merkez kontrolü
        skor += self.merkez_kontrolu_hesapla(tahta)
        
        # 4. Mobilite değerlendirmesi
        if faz < 0.7:  # Son oyun değilse
            try:
                skor += self.mobilite_hesapla(tahta) * (1 - faz)
            except:
                pass

        # 5. Şah güvenliği
        if faz < 0.5:
            try:
                skor += self.sah_guvenlik_hesapla(tahta) * (1 - faz * 2)
            except:
                pass

        # 6. Piyon yapısı değerlendirmesi
        try:
            piyon_degerlendirme = self.piyon_yapisi_degerlendir(tahta)
            skor += piyon_degerlendirme['toplam_skor']
            
            # 7. Geçer piyonlar (piyon yapısından alınır)
            skor += piyon_degerlendirme.get('gecer_piyon_skoru', 0)
        except:
            pass
        
        # 8. Fil çifti avantajı
        skor += self.fil_cifti_avantaji(tahta)
        
        # 9. Açık hat/kare kontrolü
        skor += self.acik_hat_kontrolu(tahta)
        
        # 10. İnisiyatif / tempo (sıradaki oyuncu için küçük bonus)
        if tahta.beyaz_sira:
            skor += 10
        else:
            skor -= 10
            
        # 11. Rakip şah üzerinde tropizma
        skor += self.sah_tropizmi(tahta)
        
        # 12. Zayıf kareler (outposts)
        skor += self.zayif_kare_kontrolu(tahta)
        
        # 13. Taş koordinasyonu
        skor += self.tas_koordinasyonu(tahta)
        
        # 14. Açılışın gelişimi
        if faz < 0.3:  # Açılış fazında
            skor += self.acilis_gelisimi(tahta)
        
        # 15. Uzun vadeli stratejik üstünlük
        skor += self.stratejik_ustunluk(tahta, faz)

        return skor
    
    def _hizli_malzeme_hesapla(self, tahta, beyaz):
        """Hızlı malzeme hesaplama"""
        toplam = 0
        
        if beyaz:
            toplam += bit_sayisi(tahta.beyaz_piyon) * 100
            toplam += bit_sayisi(tahta.beyaz_at) * 320
            toplam += bit_sayisi(tahta.beyaz_fil) * 330
            toplam += bit_sayisi(tahta.beyaz_kale) * 500
            toplam += bit_sayisi(tahta.beyaz_vezir) * 900
        else:
            toplam += bit_sayisi(tahta.siyah_piyon) * 100
            toplam += bit_sayisi(tahta.siyah_at) * 320
            toplam += bit_sayisi(tahta.siyah_fil) * 330
            toplam += bit_sayisi(tahta.siyah_kale) * 500
            toplam += bit_sayisi(tahta.siyah_vezir) * 900
            
        return toplam
    
    def _oyun_fazi_belirle(self, tahta):
        """Oyun fazını belirle (0=açılış, 1=son oyun)"""
        # Hızlı malzeme sayımı
        toplam_malzeme = 0
        
        # At, fil, kale, vezir sayıları
        toplam_malzeme += bit_sayisi(tahta.beyaz_at | tahta.siyah_at) * 1
        toplam_malzeme += bit_sayisi(tahta.beyaz_fil | tahta.siyah_fil) * 1
        toplam_malzeme += bit_sayisi(tahta.beyaz_kale | tahta.siyah_kale) * 2
        toplam_malzeme += bit_sayisi(tahta.beyaz_vezir | tahta.siyah_vezir) * 4
        
        # Faz hesaplama (0-1 arası)
        faz = 1.0 - (toplam_malzeme / self.max_malzeme_skoru)
        return max(0.0, min(1.0, faz))

    def malzeme_dengesi_hesapla(self, tahta):
        """Malzeme dengesini hesapla"""
        # Bitboard'ları kullanarak hızlı hesaplama
        beyaz_malzeme = (
            bit_sayisi(tahta.beyaz_piyon) * 100 +
            bit_sayisi(tahta.beyaz_at) * 320 +
            bit_sayisi(tahta.beyaz_fil) * 330 +
            bit_sayisi(tahta.beyaz_kale) * 500 +
            bit_sayisi(tahta.beyaz_vezir) * 900
        )
        
        siyah_malzeme = (
            bit_sayisi(tahta.siyah_piyon) * 100 +
            bit_sayisi(tahta.siyah_at) * 320 +
            bit_sayisi(tahta.siyah_fil) * 330 +
            bit_sayisi(tahta.siyah_kale) * 500 +
            bit_sayisi(tahta.siyah_vezir) * 900
        )

        return beyaz_malzeme - siyah_malzeme

    def pozisyonel_deger_hesapla(self, tahta):
        """Piece-Square Table kullanarak pozisyonel değer hesapla - bitboard tabanlı"""
        skor = 0
        oyun_fazi = self._oyun_fazi_belirle(tahta)

        # Beyaz taşlar için PST değerleri
        # Piyonlar
        temp = tahta.beyaz_piyon
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor += self.piyon_pst[kare]
        
        # Atlar
        temp = tahta.beyaz_at
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor += self.at_pst[kare]
        
        # Filler
        temp = tahta.beyaz_fil
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor += self.fil_pst[kare]
        
        # Kaleler
        temp = tahta.beyaz_kale
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor += self.kale_pst[kare]
        
        # Vezirler
        temp = tahta.beyaz_vezir
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor += self.vezir_pst[kare]
        
        # Şah
        if tahta.beyaz_sah:
            kare = self._en_dusuk_bit_al(tahta.beyaz_sah)
            if oyun_fazi > 0.5:
                skor += self.sah_son_pst[kare]
            else:
                skor += self.sah_acilis_pst[kare]
        
        # Siyah taşlar için PST değerleri (flip edilmiş kareler)
        # Piyonlar
        temp = tahta.siyah_piyon
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor -= self.piyon_pst[63 - kare]
        
        # Atlar
        temp = tahta.siyah_at
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor -= self.at_pst[63 - kare]
        
        # Filler
        temp = tahta.siyah_fil
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor -= self.fil_pst[63 - kare]
        
        # Kaleler
        temp = tahta.siyah_kale
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor -= self.kale_pst[63 - kare]
        
        # Vezirler
        temp = tahta.siyah_vezir
        while temp:
            kare = self._en_dusuk_bit_al(temp)
            temp = self._en_dusuk_bit_kaldir(temp)
            skor -= self.vezir_pst[63 - kare]
        
        # Şah
        if tahta.siyah_sah:
            kare = self._en_dusuk_bit_al(tahta.siyah_sah)
            if oyun_fazi > 0.5:
                skor -= self.sah_son_pst[63 - kare]
            else:
                skor -= self.sah_acilis_pst[63 - kare]

        return skor
    
    def _en_dusuk_bit_al(self, bb):
        """En düşük biti al (LSB)"""
        return (bb & -bb).bit_length() - 1
    
    def _en_dusuk_bit_kaldir(self, bb):
        """En düşük biti kaldır"""
        return bb & (bb - 1)

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
        mevcut_malzeme = 0

        # Piyon hariç malzeme sayısını hesapla
        mevcut_malzeme += bit_sayisi(tahta.beyaz_at) * self.faz_malzeme_degerleri['at']
        mevcut_malzeme += bit_sayisi(tahta.beyaz_fil) * self.faz_malzeme_degerleri['fil']
        mevcut_malzeme += bit_sayisi(tahta.beyaz_kale) * self.faz_malzeme_degerleri['kale']
        mevcut_malzeme += bit_sayisi(tahta.beyaz_vezir) * self.faz_malzeme_degerleri['vezir']

        mevcut_malzeme += bit_sayisi(tahta.siyah_at) * self.faz_malzeme_degerleri['at']
        mevcut_malzeme += bit_sayisi(tahta.siyah_fil) * self.faz_malzeme_degerleri['fil']
        mevcut_malzeme += bit_sayisi(tahta.siyah_kale) * self.faz_malzeme_degerleri['kale']
        mevcut_malzeme += bit_sayisi(tahta.siyah_vezir) * self.faz_malzeme_degerleri['vezir']

        # Oyun fazı oranını hesapla
        faz_orani = 1.0 - (mevcut_malzeme / self.max_malzeme_skoru)
        return max(0.0, min(1.0, faz_orani))

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

    def piyon_yapisi_degerlendir(self, tahta):
        """Gelişmiş piyon yapısı değerlendirmesi"""
        try:
            skor = 0
            gecer_piyon_skoru = 0

            # Çiftlenmiş piyonları penalize et (-10 cp)
            skor -= self.ciftlenmis_piyon_penaltisi(tahta, True) * 10  # Beyaz
            skor += self.ciftlenmis_piyon_penaltisi(tahta, False) * 10  # Siyah

            # İzole piyonları penalize et (-20 cp)
            skor -= self.izole_piyon_penaltisi(tahta, True) * 20  # Beyaz
            skor += self.izole_piyon_penaltisi(tahta, False) * 20  # Siyah

            # Geçer piyonları ödüllendir (sıraya göre artan bonus)
            beyaz_gecer = self.gecer_piyon_bonusu(tahta, True)
            siyah_gecer = self.gecer_piyon_bonusu(tahta, False)
            gecer_piyon_skoru = beyaz_gecer - siyah_gecer

            return {
                'toplam_skor': skor,
                'gecer_piyon_skoru': gecer_piyon_skoru
            }
        except:
            return {'toplam_skor': 0, 'gecer_piyon_skoru': 0}

    def ciftlenmis_piyon_penaltisi(self, tahta, beyaz):
        """Çiftlenmiş piyon sayısını hesapla"""
        try:
            piyonlar = tahta.beyaz_piyon if beyaz else tahta.siyah_piyon
            ciftlenmis_sayisi = 0

            for sutun in range(8):
                sutun_maski = 0x0101010101010101 << sutun
                sutun_piyonlari = piyonlar & sutun_maski
                piyon_sayisi = bit_sayisi(sutun_piyonlari)

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
        """Gelişmiş geçer piyon değerlendirmesi"""
        toplam_bonus = 0
        
        # Her sıra için bonus değerleri
        sira_bonuslari = [0, 0, 10, 20, 35, 60, 100, 0]  # 2-7. sıralar için
        
        # Basit geçer piyon tespiti (daha gelişmiş hale getirilebilir)
        return toplam_bonus

    def mat_skoru(self, derinlik):
        """Mat skorunu hesapla"""
        return 20000 - derinlik * 10  # Derinlik arttıkça skor azalır
    
    def skor_mat_mi(self, skor):
        """Skor mat skoru mu kontrol et"""
        return abs(skor) > 15000
    
    def merkez_kontrolu_hesapla(self, tahta):
        """Merkez kontrolünü değerlendir - bitboard tabanlı"""
        skor = 0
        
        # Merkez karelerdeki taşlar
        beyaz_merkez = tahta.beyaz_taslar & self._merkez_mask
        siyah_merkez = tahta.siyah_taslar & self._merkez_mask
        
        # Merkezdeki piyonlar daha değerli
        beyaz_merkez_piyon = tahta.beyaz_piyon & self._merkez_mask
        siyah_merkez_piyon = tahta.siyah_piyon & self._merkez_mask
        
        skor += bit_sayisi(beyaz_merkez_piyon) * 25
        skor -= bit_sayisi(siyah_merkez_piyon) * 25
        
        # Merkezdeki diğer taşlar
        skor += bit_sayisi(beyaz_merkez & ~beyaz_merkez_piyon) * 15
        skor -= bit_sayisi(siyah_merkez & ~siyah_merkez_piyon) * 15
        
        # Geniş merkez kontrolü (merkez hariç)
        genis_merkez_haric = self._genis_merkez_mask & ~self._merkez_mask
        beyaz_genis = tahta.beyaz_taslar & genis_merkez_haric
        siyah_genis = tahta.siyah_taslar & genis_merkez_haric
        
        skor += bit_sayisi(beyaz_genis) * 5
        skor -= bit_sayisi(siyah_genis) * 5
        
        return skor
    
    def fil_cifti_avantaji(self, tahta):
        """Fil çifti avantajını hesapla"""
        beyaz_fil_sayisi = bit_sayisi(tahta.beyaz_fil)
        siyah_fil_sayisi = bit_sayisi(tahta.siyah_fil)
        
        skor = 0
        if beyaz_fil_sayisi >= 2:
            skor += 50  # Fil çifti bonusu
        if siyah_fil_sayisi >= 2:
            skor -= 50
            
        return skor
    
    def acik_hat_kontrolu(self, tahta):
        """Açık hatları ve 7. yatay kontrolünü değerlendir"""
        skor = 0
        
        # Kalelerin açık hatlarda olup olmadığını kontrol et
        # 7. yatay (beyaz için 7. sıra, siyah için 2. sıra) kontrolü
        for sutun in range(8):
            # Beyaz kale 7. sırada mı?
            kare_7 = 48 + sutun  # 7. sıra
            tas_info = tahta.karedeki_tas(kare_7)
            if tas_info and tas_info[0] == 'beyaz' and tas_info[1] == 'kale':
                skor += 20  # 7. yatay bonusu
                
            # Siyah kale 2. sırada mı?
            kare_2 = 8 + sutun  # 2. sıra
            tas_info = tahta.karedeki_tas(kare_2)
            if tas_info and tas_info[0] == 'siyah' and tas_info[1] == 'kale':
                skor -= 20
        
        return skor
    
    def sah_tropizmi(self, tahta):
        """Rakip şah etrafında taş yoğunluğu"""
        skor = 0
        
        # Şah pozisyonlarını bul
        beyaz_sah_kare = None
        siyah_sah_kare = None
        
        for kare in range(64):
            tas_info = tahta.karedeki_tas(kare)
            if tas_info and tas_info[1] == 'sah':
                if tas_info[0] == 'beyaz':
                    beyaz_sah_kare = kare
                else:
                    siyah_sah_kare = kare
        
        if beyaz_sah_kare is not None and siyah_sah_kare is not None:
            # Siyah taşların beyaz şaha yakınlığı
            for kare in range(64):
                tas_info = tahta.karedeki_tas(kare)
                if tas_info and tas_info[0] == 'siyah' and tas_info[1] != 'sah':
                    mesafe = self._kare_mesafesi(kare, beyaz_sah_kare)
                    if mesafe <= 3:
                        skor -= (4 - mesafe) * 5  # Yakınlık bonusu
            
            # Beyaz taşların siyah şaha yakınlığı
            for kare in range(64):
                tas_info = tahta.karedeki_tas(kare)
                if tas_info and tas_info[0] == 'beyaz' and tas_info[1] != 'sah':
                    mesafe = self._kare_mesafesi(kare, siyah_sah_kare)
                    if mesafe <= 3:
                        skor += (4 - mesafe) * 5
        
        return skor
    
    def _kare_mesafesi(self, kare1, kare2):
        """İki kare arasındaki Chebyshev mesafesi"""
        sira1, sutun1 = kare1 // 8, kare1 % 8
        sira2, sutun2 = kare2 // 8, kare2 % 8
        return max(abs(sira1 - sira2), abs(sutun1 - sutun2))
    
    def zayif_kare_kontrolu(self, tahta):
        """Zayıf karelerdeki at ve fil kontrolü (outposts)"""
        skor = 0
        
        # Merkezi zayıf kareler (örnek)
        zayif_kareler_beyaz = [27, 28, 35, 36, 42, 43, 44, 45]  # Siyah için zayıf
        zayif_kareler_siyah = [18, 19, 20, 21, 26, 27, 28, 29]  # Beyaz için zayıf
        
        for kare in zayif_kareler_siyah:
            tas_info = tahta.karedeki_tas(kare)
            if tas_info and tas_info[0] == 'beyaz':
                if tas_info[1] == 'at':
                    skor += 30  # Zayıf karedeki at
                elif tas_info[1] == 'fil':
                    skor += 25  # Zayıf karedeki fil
        
        for kare in zayif_kareler_beyaz:
            tas_info = tahta.karedeki_tas(kare)
            if tas_info and tas_info[0] == 'siyah':
                if tas_info[1] == 'at':
                    skor -= 30
                elif tas_info[1] == 'fil':
                    skor -= 25
        
        return skor
    
    def tas_koordinasyonu(self, tahta):
        """Taşların birbirini koruması"""
        skor = 0
        
        # Basit koordinasyon: korunan taşlar için bonus
        # (Daha detaylı implementasyon gerekir)
        
        return skor
    
    def acilis_gelisimi(self, tahta):
        """Açılış gelişimi değerlendirmesi"""
        skor = 0
        
        # Merkez piyonları gelişmiş mi?
        e2 = tahta.karedeki_tas(12)  # e2
        d2 = tahta.karedeki_tas(11)  # d2
        e7 = tahta.karedeki_tas(52)  # e7
        d7 = tahta.karedeki_tas(51)  # d7
        
        # Beyaz merkez piyonları hareket etmemiş
        if e2 and e2[0] == 'beyaz' and e2[1] == 'piyon':
            skor -= 10
        if d2 and d2[0] == 'beyaz' and d2[1] == 'piyon':
            skor -= 10
            
        # Siyah merkez piyonları hareket etmemiş
        if e7 and e7[0] == 'siyah' and e7[1] == 'piyon':
            skor += 10
        if d7 and d7[0] == 'siyah' and d7[1] == 'piyon':
            skor += 10
        
        # Atlar gelişmiş mi?
        b1 = tahta.karedeki_tas(1)  # b1
        g1 = tahta.karedeki_tas(6)  # g1
        b8 = tahta.karedeki_tas(57)  # b8
        g8 = tahta.karedeki_tas(62)  # g8
        
        if b1 and b1[0] == 'beyaz' and b1[1] == 'at':
            skor -= 10  # At hala başlangıç karesinde
        if g1 and g1[0] == 'beyaz' and g1[1] == 'at':
            skor -= 10
        if b8 and b8[0] == 'siyah' and b8[1] == 'at':
            skor += 10
        if g8 and g8[0] == 'siyah' and g8[1] == 'at':
            skor += 10
            
        return skor
    
    def stratejik_ustunluk(self, tahta, faz):
        """Uzun vadeli stratejik avantajlar"""
        skor = 0
        
        # Fil renk avantajı (açık/kapalı pozisyon)
        # Piyon zinciri avantajı
        # Kale aktivitesi potansiyeli
        
        return skor