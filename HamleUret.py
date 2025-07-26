"""
Pseudo-legal hamle üretici. Her taş türü için optimize edilmiş hamle üretimi.
Bitboard tabanlı hız optimizasyonları ile.
"""

from dataclasses import dataclass
from typing import Optional

# Bit işlemleri için yardımcı fonksiyonlar
def bit_sayisi(x):
    """Bit sayısını hesapla"""
    count = 0
    while x:
        x &= x - 1
        count += 1
    return count

@dataclass
class Hamle:
    """Hamle veri yapısı"""
    kaynak: int
    hedef: int
    tas: str
    tur: str = 'normal'  # normal, alma, terfi, terfi_alma, kisa_rok, uzun_rok, en_passant, iki_kare
    terfi_tasi: Optional[str] = None
    skor: int = 0  # Move ordering için

    def __eq__(self, other):
        if isinstance(other, tuple):
            # Tuple ile karşılaştırma (geriye uyumluluk)
            if len(other) >= 2:
                return self.kaynak == other[0] and self.hedef == other[1]
            return False
        return (self.kaynak == other.kaynak and 
                self.hedef == other.hedef and 
                self.terfi_tasi == other.terfi_tasi)
    
    def __hash__(self):
        return hash((self.kaynak, self.hedef, self.terfi_tasi))
    
    def to_tuple(self):
        """Geriye uyumluluk için tuple'a çevir"""
        if self.terfi_tasi:
            return (self.kaynak, self.hedef, self.tas, self.tur, self.terfi_tasi)
        return (self.kaynak, self.hedef, self.tas, self.tur)


class HamleUretici:
    # Sınıf değişkenleri - bir kez hesaplanır
    _maskeler_hazir = False
    at_hamle_maskeleri = None
    sah_hamle_maskeleri = None
    beyaz_piyon_saldiri = None
    siyah_piyon_saldiri = None
    merkez_kareler = None
    genis_merkez = None
    
    # Taş değerleri (MVV-LVA için)
    tas_degerleri = {
        'piyon': 100,
        'at': 320,
        'fil': 330,
        'kale': 500,
        'vezir': 900,
        'sah': 20000
    }
    
    def __init__(self):
        self.hamleler = []
        if not HamleUretici._maskeler_hazir:
            HamleUretici._onceden_hesapla_sinif()

    @classmethod
    def _onceden_hesapla_sinif(cls):
        """Sık kullanılan maskeleri ve tabloları önceden hesapla - sınıf seviyesinde"""
        if cls._maskeler_hazir:
            return
            
        # At hamleleri için ön hesaplama
        cls.at_hamle_maskeleri = [0] * 64
        for kare in range(64):
            satir, sutun = divmod(kare, 8)
            mask = 0
            for ds, dt in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                yeni_satir, yeni_sutun = satir + ds, sutun + dt
                if 0 <= yeni_satir < 8 and 0 <= yeni_sutun < 8:
                    mask |= 1 << (yeni_satir * 8 + yeni_sutun)
            cls.at_hamle_maskeleri[kare] = mask

        # Şah hamleleri için ön hesaplama
        cls.sah_hamle_maskeleri = [0] * 64
        for kare in range(64):
            satir, sutun = divmod(kare, 8)
            mask = 0
            for ds in [-1, 0, 1]:
                for dt in [-1, 0, 1]:
                    if ds == 0 and dt == 0:
                        continue
                    yeni_satir, yeni_sutun = satir + ds, sutun + dt
                    if 0 <= yeni_satir < 8 and 0 <= yeni_sutun < 8:
                        mask |= 1 << (yeni_satir * 8 + yeni_sutun)
            cls.sah_hamle_maskeleri[kare] = mask

        # Piyon saldırı maskeleri
        cls.beyaz_piyon_saldiri = [0] * 64
        cls.siyah_piyon_saldiri = [0] * 64

        for kare in range(64):
            satir, sutun = divmod(kare, 8)

            # Beyaz piyon saldırıları
            mask = 0
            if satir < 7:
                if sutun > 0: mask |= 1 << ((satir + 1) * 8 + sutun - 1)
                if sutun < 7: mask |= 1 << ((satir + 1) * 8 + sutun + 1)
            cls.beyaz_piyon_saldiri[kare] = mask

            # Siyah piyon saldırıları
            mask = 0
            if satir > 0:
                if sutun > 0: mask |= 1 << ((satir - 1) * 8 + sutun - 1)
                if sutun < 7: mask |= 1 << ((satir - 1) * 8 + sutun + 1)
            cls.siyah_piyon_saldiri[kare] = mask
        
        # Merkez kareleri (move ordering için)
        cls.merkez_kareler = set([27, 28, 35, 36])  # d4, e4, d5, e5
        cls.genis_merkez = set([18, 19, 20, 21, 26, 27, 28, 29, 34, 35, 36, 37, 42, 43, 44, 45])
        
        # İşaret et
        cls._maskeler_hazir = True

    def _hamle_skoru_hesapla(self, hamle, tahta):
        """Hamle için skor hesapla (move ordering için)"""
        skor = 0
        
        # Terfi hamleleri en yüksek öncelik
        if hamle.tur in ['terfi', 'terfi_alma']:
            if hamle.terfi_tasi == 'vezir':
                skor += 9000
            elif hamle.terfi_tasi == 'kale':
                skor += 5000
            elif hamle.terfi_tasi == 'fil':
                skor += 3300
            else:  # at
                skor += 3200
        
        # Alma hamleleri - MVV-LVA
        if hamle.tur in ['alma', 'terfi_alma', 'en_passant']:
            hedef_tas = tahta.tas_turu_al(hamle.hedef)
            if hedef_tas:
                victim_value = self.tas_degerleri.get(hedef_tas[1], 0)
                attacker_value = self.tas_degerleri.get(hamle.tas, 0)
                skor += 1000 + (victim_value * 10) - attacker_value
        
        # Merkeze doğru hamleler
        if hamle.hedef in self.merkez_kareler:
            skor += 50
        elif hamle.hedef in self.genis_merkez:
            skor += 25
        
        # Tehdit edilen taşları uzaklaştırma
        if self.saldiri_altinda_mi(tahta, hamle.kaynak, tahta.beyaz_sira):
            skor += 20
        
        return skor

    def tum_hamleleri_uret(self, tahta):
        """Mevcut pozisyon için tüm pseudo-legal hamleleri üret"""
        self.hamleler = []
        renk = 'beyaz' if tahta.beyaz_sira else 'siyah'
        
        # Şah kontrolü - şah çekilmişse özel durum
        sah_tehdidinde = tahta.sah_tehdit_altinda_mi(renk)

        if renk == 'beyaz':
            self._piyon_hamleleri_uret(tahta, True)
            self._at_hamleleri_uret(tahta, True)
            self._fil_hamleleri_uret(tahta, True)
            self._kale_hamleleri_uret(tahta, True)
            self._vezir_hamleleri_uret(tahta, True)
            self._sah_hamleleri_uret(tahta, True)
        else:
            self._piyon_hamleleri_uret(tahta, False)
            self._at_hamleleri_uret(tahta, False)
            self._fil_hamleleri_uret(tahta, False)
            self._kale_hamleleri_uret(tahta, False)
            self._vezir_hamleleri_uret(tahta, False)
            self._sah_hamleleri_uret(tahta, False)
        
        # Hamleleri skorla ve tuple'a çevir (geriye uyumluluk için)
        hamleler_tuple = []
        for hamle in self.hamleler:
            hamle.skor = self._hamle_skoru_hesapla(hamle, tahta)
            hamleler_tuple.append(hamle.to_tuple())
        
        return hamleler_tuple

    def saldiri_altinda_mi(self, tahta, kare, beyaz_saldiri):
        """Belirtilen kare saldırı altında mı kontrol et"""
        if beyaz_saldiri:
            # Beyaz taşlar tarafından saldırı kontrolü
            # Piyon saldırıları
            if self.siyah_piyon_saldiri[kare] & tahta.beyaz_piyon:
                return True

            # At saldırıları
            if self.at_hamle_maskeleri[kare] & tahta.beyaz_at:
                return True

            # Şah saldırıları
            if self.sah_hamle_maskeleri[kare] & tahta.beyaz_sah:
                return True

            # Çizgisel saldırılar (kale, vezir)
            if self._cizgisel_saldiri_kontrol(tahta, kare, tahta.beyaz_kale | tahta.beyaz_vezir):
                return True

            # Çapraz saldırılar (fil, vezir)
            if self._capraz_saldiri_kontrol(tahta, kare, tahta.beyaz_fil | tahta.beyaz_vezir):
                return True

        else:
            # Siyah taşlar tarafından saldırı kontrolü
            # Piyon saldırıları
            if self.beyaz_piyon_saldiri[kare] & tahta.siyah_piyon:
                return True

            # At saldırıları
            if self.at_hamle_maskeleri[kare] & tahta.siyah_at:
                return True

            # Şah saldırıları
            if self.sah_hamle_maskeleri[kare] & tahta.siyah_sah:
                return True

            # Çizgisel saldırılar (kale, vezir)
            if self._cizgisel_saldiri_kontrol(tahta, kare, tahta.siyah_kale | tahta.siyah_vezir):
                return True

            # Çapraz saldırılar (fil, vezir)
            if self._capraz_saldiri_kontrol(tahta, kare, tahta.siyah_fil | tahta.siyah_vezir):
                return True

        return False

    def _cizgisel_saldiri_kontrol(self, tahta, kare, saldirgan_taslar):
        """Çizgisel (kale/vezir) saldırı kontrolü"""
        if saldirgan_taslar == 0:
            return False

        kare_satir = kare // 8
        kare_sutun = kare % 8

        # Dört doğrusal yön
        for yon in [1, -1, 8, -8]:
            hedef = kare + yon
            onceki_satir = kare_satir
            onceki_sutun = kare_sutun

            while 0 <= hedef < 64:
                hedef_satir = hedef // 8
                hedef_sutun = hedef % 8
                
                # Yatay hareket kontrolü
                if yon == 1:  # Sağa
                    if hedef_satir != kare_satir or hedef_sutun <= kare_sutun:
                        break
                elif yon == -1:  # Sola
                    if hedef_satir != kare_satir or hedef_sutun >= kare_sutun:
                        break
                elif yon == 8:  # Yukarı
                    if hedef_sutun != kare_sutun or hedef_satir <= kare_satir:
                        break
                elif yon == -8:  # Aşağı
                    if hedef_sutun != kare_sutun or hedef_satir >= kare_satir:
                        break

                # Taş kontrolü
                if tahta.tum_taslar & (1 << hedef):
                    if saldirgan_taslar & (1 << hedef):
                        return True
                    break

                hedef += yon

        return False

    def _capraz_saldiri_kontrol(self, tahta, kare, saldirgan_taslar):
        """Çapraz (fil/vezir) saldırı kontrolü"""
        if saldirgan_taslar == 0:
            return False

        kare_satir = kare // 8
        kare_sutun = kare % 8

        # Dört çapraz yön: sağ-yukarı(9), sol-yukarı(7), sağ-aşağı(-7), sol-aşağı(-9)
        yonler = [
            (1, 1, 9),    # sağ-yukarı
            (-1, 1, 7),   # sol-yukarı
            (1, -1, -7),  # sağ-aşağı
            (-1, -1, -9)  # sol-aşağı
        ]
        
        for sutun_yon, satir_yon, adim in yonler:
            hedef = kare + adim
            hedef_satir = kare_satir + satir_yon
            hedef_sutun = kare_sutun + sutun_yon

            while 0 <= hedef_satir < 8 and 0 <= hedef_sutun < 8:
                # Taş kontrolü
                if tahta.tum_taslar & (1 << hedef):
                    if saldirgan_taslar & (1 << hedef):
                        return True
                    break

                hedef += adim
                hedef_satir += satir_yon
                hedef_sutun += sutun_yon

        return False

    def _piyon_hamleleri_uret(self, tahta, beyaz):
        """Piyon hamleleri üret"""
        if beyaz:
            piyonlar = tahta.beyaz_piyon
            dusman_taslar = tahta.siyah_taslar
            yon = 8  # İleri yön
            baslangic_satiri = 1
            terfi_satiri = 7
        else:
            piyonlar = tahta.siyah_piyon
            dusman_taslar = tahta.beyaz_taslar
            yon = -8  # İleri yön
            baslangic_satiri = 6
            terfi_satiri = 0

        tum_taslar = tahta.tum_taslar

        while piyonlar:
            kaynak = tahta.en_dusuk_bit_al(piyonlar)
            piyonlar = tahta.en_dusuk_bit_kaldir(piyonlar)

            satir = kaynak // 8

            # İleri hareket
            hedef = kaynak + yon
            if 0 <= hedef < 64 and not (tum_taslar & (1 << hedef)):
                if satir + (1 if beyaz else -1) == terfi_satiri:
                    # Terfi hamleleri
                    for terfi_tasi in ['vezir', 'kale', 'fil', 'at']:
                        self.hamleler.append(Hamle(kaynak, hedef, 'piyon', 'terfi', terfi_tasi))
                else:
                    self.hamleler.append(Hamle(kaynak, hedef, 'piyon', 'normal'))

                # İki kare ileri (başlangıç pozisyonundan)
                if satir == baslangic_satiri:
                    hedef2 = kaynak + 2 * yon
                    if 0 <= hedef2 < 64 and not (tum_taslar & (1 << hedef2)):
                        self.hamleler.append(Hamle(kaynak, hedef2, 'piyon', 'iki_kare'))

            # Çapraz saldırılar
            saldiri_maskeleri = self.beyaz_piyon_saldiri if beyaz else self.siyah_piyon_saldiri
            saldirilar = saldiri_maskeleri[kaynak] & dusman_taslar

            while saldirilar:
                hedef = tahta.en_dusuk_bit_al(saldirilar)
                saldirilar = tahta.en_dusuk_bit_kaldir(saldirilar)

                if satir + (1 if beyaz else -1) == terfi_satiri:
                    # Terfi ile alma
                    for terfi_tasi in ['vezir', 'kale', 'fil', 'at']:
                        self.hamleler.append(Hamle(kaynak, hedef, 'piyon', 'terfi_alma', terfi_tasi))
                else:
                    self.hamleler.append(Hamle(kaynak, hedef, 'piyon', 'alma'))

            # En passant
            if tahta.en_passant_kare is not None and tahta.en_passant_kare != -1:
                if saldiri_maskeleri[kaynak] & (1 << tahta.en_passant_kare):
                    self.hamleler.append(Hamle(kaynak, tahta.en_passant_kare, 'piyon', 'en_passant'))

    def _at_hamleleri_uret(self, tahta, beyaz):
        """At hamleleri üret"""
        atlar = tahta.beyaz_at if beyaz else tahta.siyah_at
        kendi_taslar = tahta.beyaz_taslar if beyaz else tahta.siyah_taslar

        while atlar:
            kaynak = tahta.en_dusuk_bit_al(atlar)
            atlar = tahta.en_dusuk_bit_kaldir(atlar)

            hedefler = self.at_hamle_maskeleri[kaynak] & ~kendi_taslar

            while hedefler:
                hedef = tahta.en_dusuk_bit_al(hedefler)
                hedefler = tahta.en_dusuk_bit_kaldir(hedefler)

                hamle_turu = 'alma' if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef) else 'normal'
                self.hamleler.append(Hamle(kaynak, hedef, 'at', hamle_turu))

    def _fil_hamleleri_uret(self, tahta, beyaz):
        """Fil hamleleri üret"""
        filler = tahta.beyaz_fil if beyaz else tahta.siyah_fil
        kendi_taslar = tahta.beyaz_taslar if beyaz else tahta.siyah_taslar

        while filler:
            kaynak = tahta.en_dusuk_bit_al(filler)
            filler = tahta.en_dusuk_bit_kaldir(filler)

            # Dört çapraz yön
            for yon in [7, 9, -7, -9]:
                hedef = kaynak + yon

                while 0 <= hedef < 64:
                    # Sınır kontrolü
                    if abs((hedef % 8) - (kaynak % 8)) != abs((hedef // 8) - (kaynak // 8)):
                        break

                    if kendi_taslar & (1 << hedef):
                        break

                    hamle_turu = 'alma' if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef) else 'normal'
                    self.hamleler.append(Hamle(kaynak, hedef, 'fil', hamle_turu))

                    if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef):  # Düşman taşına çarptı
                        break

                    hedef += yon

    def _kale_hamleleri_uret(self, tahta, beyaz):
        """Kale hamleleri üret"""
        kaleler = tahta.beyaz_kale if beyaz else tahta.siyah_kale
        kendi_taslar = tahta.beyaz_taslar if beyaz else tahta.siyah_taslar

        while kaleler:
            kaynak = tahta.en_dusuk_bit_al(kaleler)
            kaleler = tahta.en_dusuk_bit_kaldir(kaleler)

            # Dört doğrusal yön
            for yon in [1, -1, 8, -8]:
                hedef = kaynak + yon

                while 0 <= hedef < 64:
                    # Yatay hareket sınır kontrolü
                    if yon in [1, -1] and (hedef // 8) != (kaynak // 8):
                        break

                    if kendi_taslar & (1 << hedef):
                        break

                    hamle_turu = 'alma' if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef) else 'normal'
                    self.hamleler.append(Hamle(kaynak, hedef, 'kale', hamle_turu))

                    if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef):  # Düşman taşına çarptı
                        break

                    hedef += yon

    def _vezir_hamleleri_uret(self, tahta, beyaz):
        """Vezir hamleleri üret (kale + fil hareketi)"""
        vezirler = tahta.beyaz_vezir if beyaz else tahta.siyah_vezir
        kendi_taslar = tahta.beyaz_taslar if beyaz else tahta.siyah_taslar

        while vezirler:
            kaynak = tahta.en_dusuk_bit_al(vezirler)
            vezirler = tahta.en_dusuk_bit_kaldir(vezirler)

            # Sekiz yön (4 doğrusal + 4 çapraz)
            for yon in [1, -1, 8, -8, 7, 9, -7, -9]:
                hedef = kaynak + yon

                while 0 <= hedef < 64:
                    # Sınır kontrolleri
                    if yon in [1, -1] and (hedef // 8) != (kaynak // 8):
                        break
                    if yon in [7, 9, -7, -9]:
                        if abs((hedef % 8) - (kaynak % 8)) != abs((hedef // 8) - (kaynak // 8)):
                            break

                    if kendi_taslar & (1 << hedef):
                        break

                    hamle_turu = 'alma' if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef) else 'normal'
                    self.hamleler.append(Hamle(kaynak, hedef, 'vezir', hamle_turu))

                    if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef):  # Düşman taşına çarptı
                        break

                    hedef += yon

    def _sah_hamleleri_uret(self, tahta, beyaz):
        """Şah hamleleri üret"""
        sah = tahta.beyaz_sah if beyaz else tahta.siyah_sah
        kendi_taslar = tahta.beyaz_taslar if beyaz else tahta.siyah_taslar

        if sah == 0:
            return

        kaynak = tahta.en_dusuk_bit_al(sah)
        hedefler = self.sah_hamle_maskeleri[kaynak] & ~kendi_taslar

        while hedefler:
            hedef = tahta.en_dusuk_bit_al(hedefler)
            hedefler = tahta.en_dusuk_bit_kaldir(hedefler)

            hamle_turu = 'alma' if (tahta.beyaz_taslar | tahta.siyah_taslar) & (1 << hedef) else 'normal'
            self.hamleler.append(Hamle(kaynak, hedef, 'sah', hamle_turu))

        # Rok hamleleri
        self._rok_hamleleri_uret(tahta, beyaz)

    def _rok_hamleleri_uret(self, tahta, beyaz):
        """Rok hamleleri üret"""
        if beyaz:
            # Beyaz şah e1'de mi kontrol et
            if tahta.beyaz_sah != (1 << 4):  # e1
                return
                
            if tahta.beyaz_kisa_rok:
                # Kısa rok: e1-g1
                if not ((tahta.tum_taslar & 0x60)):  # f1 ve g1 boş
                    # Şah ve geçiş kareleri saldırı altında olmamalı
                    if not self.saldiri_altinda_mi(tahta, 4, False) and \
                       not self.saldiri_altinda_mi(tahta, 5, False) and \
                       not self.saldiri_altinda_mi(tahta, 6, False):
                        self.hamleler.append(Hamle(4, 6, 'sah', 'kisa_rok'))

            if tahta.beyaz_uzun_rok:
                # Uzun rok: e1-c1
                if not ((tahta.tum_taslar & 0x0E)):  # b1, c1, d1 boş
                    # Şah ve geçiş kareleri saldırı altında olmamalı
                    if not self.saldiri_altinda_mi(tahta, 4, False) and \
                       not self.saldiri_altinda_mi(tahta, 3, False) and \
                       not self.saldiri_altinda_mi(tahta, 2, False):
                        self.hamleler.append(Hamle(4, 2, 'sah', 'uzun_rok'))
        else:
            # Siyah şah e8'de mi kontrol et
            if tahta.siyah_sah != (1 << 60):  # e8
                return
                
            if tahta.siyah_kisa_rok:
                # Kısa rok: e8-g8
                if not ((tahta.tum_taslar & 0x6000000000000000)):  # f8 ve g8 boş
                    # Şah ve geçiş kareleri saldırı altında olmamalı
                    if not self.saldiri_altinda_mi(tahta, 60, True) and \
                       not self.saldiri_altinda_mi(tahta, 61, True) and \
                       not self.saldiri_altinda_mi(tahta, 62, True):
                        self.hamleler.append(Hamle(60, 62, 'sah', 'kisa_rok'))

            if tahta.siyah_uzun_rok:
                # Uzun rok: e8-c8
                if not ((tahta.tum_taslar & 0x0E00000000000000)):  # b8, c8, d8 boş
                    # Şah ve geçiş kareleri saldırı altında olmamalı
                    if not self.saldiri_altinda_mi(tahta, 60, True) and \
                       not self.saldiri_altinda_mi(tahta, 59, True) and \
                       not self.saldiri_altinda_mi(tahta, 58, True):
                        self.hamleler.append(Hamle(60, 58, 'sah', 'uzun_rok'))

    def piyon_yapisi_analizi(self, tahta, beyaz):
        """Piyon yapısı analizi - detaylı bilgi döndürür"""
        analiz = {
            'gecer_piyonlar': [],
            'izole_piyonlar': [],
            'cift_piyonlar': [],
            'geri_kalmis_piyonlar': [],
            'piyon_zincirleri': [],
            'piyon_adalari': 0
        }
        
        piyonlar = tahta.beyaz_piyon if beyaz else tahta.siyah_piyon
        dusman_piyonlar = tahta.siyah_piyon if beyaz else tahta.beyaz_piyon
        
        # Her piyon için analiz
        temp_piyonlar = piyonlar
        while temp_piyonlar:
            kare = self._en_dusuk_bit_al(temp_piyonlar)
            temp_piyonlar = self._en_dusuk_bit_kaldir(temp_piyonlar)
            
            satir, sutun = divmod(kare, 8)
            
            # Geçer piyon kontrolü
            if self._gecer_piyon_mu(kare, beyaz, dusman_piyonlar):
                analiz['gecer_piyonlar'].append(kare)
            
            # İzole piyon kontrolü
            if self._izole_piyon_mu(kare, sutun, piyonlar):
                analiz['izole_piyonlar'].append(kare)
            
            # Geri kalmış piyon kontrolü
            if self._geri_kalmis_piyon_mu(kare, satir, sutun, beyaz, piyonlar):
                analiz['geri_kalmis_piyonlar'].append(kare)
        
        # Çift piyon kontrolü
        analiz['cift_piyonlar'] = self._cift_piyonlari_bul(piyonlar)
        
        # Piyon adaları sayısı
        analiz['piyon_adalari'] = self._piyon_adalari_say(piyonlar)
        
        return analiz
    
    def _gecer_piyon_mu(self, kare, beyaz, dusman_piyonlar):
        """Verilen piyon geçer piyon mu kontrol et"""
        satir, sutun = divmod(kare, 8)
        
        # Beyaz için ilerisi, siyah için gerisi kontrol edilmeli
        if beyaz:
            # Önündeki karelerde düşman piyonu var mı?
            for kontrol_satir in range(satir + 1, 8):
                # Aynı sütun
                if dusman_piyonlar & (1 << (kontrol_satir * 8 + sutun)):
                    return False
                # Sol komşu sütun
                if sutun > 0 and dusman_piyonlar & (1 << (kontrol_satir * 8 + sutun - 1)):
                    return False
                # Sağ komşu sütun
                if sutun < 7 and dusman_piyonlar & (1 << (kontrol_satir * 8 + sutun + 1)):
                    return False
        else:
            # Siyah için
            for kontrol_satir in range(0, satir):
                # Aynı sütun
                if dusman_piyonlar & (1 << (kontrol_satir * 8 + sutun)):
                    return False
                # Sol komşu sütun
                if sutun > 0 and dusman_piyonlar & (1 << (kontrol_satir * 8 + sutun - 1)):
                    return False
                # Sağ komşu sütun
                if sutun < 7 and dusman_piyonlar & (1 << (kontrol_satir * 8 + sutun + 1)):
                    return False
        
        return True
    
    def _izole_piyon_mu(self, kare, sutun, piyonlar):
        """Verilen piyon izole mi kontrol et"""
        # Sol ve sağ sütunlardaki piyon var mı?
        sol_sutun_mask = 0x0101010101010101 << (sutun - 1) if sutun > 0 else 0
        sag_sutun_mask = 0x0101010101010101 << (sutun + 1) if sutun < 7 else 0
        
        komsu_mask = sol_sutun_mask | sag_sutun_mask
        return (piyonlar & komsu_mask) == 0
    
    def _geri_kalmis_piyon_mu(self, kare, satir, sutun, beyaz, piyonlar):
        """Verilen piyon geri kalmış mı kontrol et"""
        # Komşu sütunlardaki piyonlar bu piyondan ilerde mi?
        sol_sutun = sutun - 1 if sutun > 0 else -1
        sag_sutun = sutun + 1 if sutun < 7 else -1
        
        geri_kalmis = True
        
        if beyaz:
            # Beyaz için komşu piyonlar daha ileride mi?
            if sol_sutun >= 0:
                sol_mask = 0x0101010101010101 << sol_sutun
                sol_piyonlar = piyonlar & sol_mask
                while sol_piyonlar:
                    piyon_kare = self._en_dusuk_bit_al(sol_piyonlar)
                    sol_piyonlar = self._en_dusuk_bit_kaldir(sol_piyonlar)
                    if piyon_kare // 8 <= satir:
                        geri_kalmis = False
                        break
            
            if geri_kalmis and sag_sutun <= 7:
                sag_mask = 0x0101010101010101 << sag_sutun
                sag_piyonlar = piyonlar & sag_mask
                while sag_piyonlar:
                    piyon_kare = self._en_dusuk_bit_al(sag_piyonlar)
                    sag_piyonlar = self._en_dusuk_bit_kaldir(sag_piyonlar)
                    if piyon_kare // 8 <= satir:
                        geri_kalmis = False
                        break
        else:
            # Siyah için komşu piyonlar daha geride mi?
            if sol_sutun >= 0:
                sol_mask = 0x0101010101010101 << sol_sutun
                sol_piyonlar = piyonlar & sol_mask
                while sol_piyonlar:
                    piyon_kare = self._en_dusuk_bit_al(sol_piyonlar)
                    sol_piyonlar = self._en_dusuk_bit_kaldir(sol_piyonlar)
                    if piyon_kare // 8 >= satir:
                        geri_kalmis = False
                        break
            
            if geri_kalmis and sag_sutun <= 7:
                sag_mask = 0x0101010101010101 << sag_sutun
                sag_piyonlar = piyonlar & sag_mask
                while sag_piyonlar:
                    piyon_kare = self._en_dusuk_bit_al(sag_piyonlar)
                    sag_piyonlar = self._en_dusuk_bit_kaldir(sag_piyonlar)
                    if piyon_kare // 8 >= satir:
                        geri_kalmis = False
                        break
        
        return geri_kalmis
    
    def _cift_piyonlari_bul(self, piyonlar):
        """Çift piyonları bul ve listele"""
        cift_piyonlar = []
        
        for sutun in range(8):
            sutun_mask = 0x0101010101010101 << sutun
            sutun_piyonlari = piyonlar & sutun_mask
            
            piyon_sayisi = bit_sayisi(sutun_piyonlari)
            if piyon_sayisi > 1:
                # Bu sütundaki tüm piyonları çift piyon olarak işaretle
                temp = sutun_piyonlari
                while temp:
                    kare = self._en_dusuk_bit_al(temp)
                    temp = self._en_dusuk_bit_kaldir(temp)
                    cift_piyonlar.append(kare)
        
        return cift_piyonlar
    
    def _piyon_adalari_say(self, piyonlar):
        """Piyon adalarının sayısını hesapla"""
        adalalar = 0
        onceki_sutunda_piyon_var = False
        
        for sutun in range(8):
            sutun_mask = 0x0101010101010101 << sutun
            sutunda_piyon_var = bool(piyonlar & sutun_mask)
            
            if sutunda_piyon_var and not onceki_sutunda_piyon_var:
                adalalar += 1
            
            onceki_sutunda_piyon_var = sutunda_piyon_var
        
        return adalalar
    
    def _rok_mumkun_mu(self, tahta, beyaz, kisa_rok):
        """Rok hamlesinin mümkün olup olmadığını kontrol et"""
        if beyaz:
            sah_kare = 4  # e1
            if tahta.beyaz_sah != (1 << sah_kare):
                return False
            
            if kisa_rok:
                if not tahta.beyaz_kisa_rok:
                    return False
                # f1 ve g1 boş mu?
                if tahta.tum_taslar & 0x60:
                    return False
                # e1, f1, g1 saldırı altında mı?
                return (not self.saldiri_altinda_mi(tahta, 4, False) and
                        not self.saldiri_altinda_mi(tahta, 5, False) and
                        not self.saldiri_altinda_mi(tahta, 6, False))
            else:
                if not tahta.beyaz_uzun_rok:
                    return False
                # b1, c1, d1 boş mu?
                if tahta.tum_taslar & 0x0E:
                    return False
                # e1, d1, c1 saldırı altında mı?
                return (not self.saldiri_altinda_mi(tahta, 4, False) and
                        not self.saldiri_altinda_mi(tahta, 3, False) and
                        not self.saldiri_altinda_mi(tahta, 2, False))
        else:
            sah_kare = 60  # e8
            if tahta.siyah_sah != (1 << sah_kare):
                return False
            
            if kisa_rok:
                if not tahta.siyah_kisa_rok:
                    return False
                # f8 ve g8 boş mu?
                if tahta.tum_taslar & 0x6000000000000000:
                    return False
                # e8, f8, g8 saldırı altında mı?
                return (not self.saldiri_altinda_mi(tahta, 60, True) and
                        not self.saldiri_altinda_mi(tahta, 61, True) and
                        not self.saldiri_altinda_mi(tahta, 62, True))
            else:
                if not tahta.siyah_uzun_rok:
                    return False
                # b8, c8, d8 boş mu?
                if tahta.tum_taslar & 0x0E00000000000000:
                    return False
                # e8, d8, c8 saldırı altında mı?
                return (not self.saldiri_altinda_mi(tahta, 60, True) and
                        not self.saldiri_altinda_mi(tahta, 59, True) and
                        not self.saldiri_altinda_mi(tahta, 58, True))
    
    def _en_dusuk_bit_al(self, bb):
        """En düşük biti al (LSB)"""
        if bb == 0:
            return -1
        return (bb & -bb).bit_length() - 1
    
    def _en_dusuk_bit_kaldir(self, bb):
        """En düşük biti kaldır"""
        return bb & (bb - 1)