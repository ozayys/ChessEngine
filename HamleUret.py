"""
Pseudo-legal hamle üretici. Her taş türü için optimize edilmiş hamle üretimi.
Bitboard tabanlı hız optimizasyonları ile.
"""

class HamleUretici:
    def __init__(self):
        self.hamleler = []
        self._onceden_hesapla()

    def _onceden_hesapla(self):
        """Sık kullanılan maskeleri ve tabloları önceden hesapla"""
        # At hamleleri için ön hesaplama
        self.at_hamle_maskeleri = [0] * 64
        for kare in range(64):
            satir, sutun = divmod(kare, 8)
            mask = 0
            for ds, dt in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                yeni_satir, yeni_sutun = satir + ds, sutun + dt
                if 0 <= yeni_satir < 8 and 0 <= yeni_sutun < 8:
                    mask |= 1 << (yeni_satir * 8 + yeni_sutun)
            self.at_hamle_maskeleri[kare] = mask

        # Şah hamleleri için ön hesaplama
        self.sah_hamle_maskeleri = [0] * 64
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
            self.sah_hamle_maskeleri[kare] = mask

        # Piyon saldırı maskeleri
        self.beyaz_piyon_saldiri = [0] * 64
        self.siyah_piyon_saldiri = [0] * 64

        for kare in range(64):
            satir, sutun = divmod(kare, 8)

            # Beyaz piyon saldırıları
            mask = 0
            if satir < 7:
                if sutun > 0: mask |= 1 << ((satir + 1) * 8 + sutun - 1)
                if sutun < 7: mask |= 1 << ((satir + 1) * 8 + sutun + 1)
            self.beyaz_piyon_saldiri[kare] = mask

            # Siyah piyon saldırıları
            mask = 0
            if satir > 0:
                if sutun > 0: mask |= 1 << ((satir - 1) * 8 + sutun - 1)
                if sutun < 7: mask |= 1 << ((satir - 1) * 8 + sutun + 1)
            self.siyah_piyon_saldiri[kare] = mask
            
        # Sliding piece maskeleri (kale ve fil için)
        self._sliding_maskeleri_olustur()
        
    def _sliding_maskeleri_olustur(self):
        """Kale ve fil için satır/sütun/köşegen maskeleri"""
        self.satir_maske = [0] * 64
        self.sutun_maske = [0] * 64
        self.ana_kosegen_maske = [0] * 64
        self.yan_kosegen_maske = [0] * 64
        
        for kare in range(64):
            satir, sutun = divmod(kare, 8)
            
            # Satır maskesi
            for s in range(8):
                self.satir_maske[kare] |= 1 << (satir * 8 + s)
                
            # Sütun maskesi
            for r in range(8):
                self.sutun_maske[kare] |= 1 << (r * 8 + sutun)
                
            # Ana köşegen maskesi
            r, s = satir, sutun
            while r >= 0 and s >= 0:
                self.ana_kosegen_maske[kare] |= 1 << (r * 8 + s)
                r -= 1
                s -= 1
            r, s = satir + 1, sutun + 1
            while r < 8 and s < 8:
                self.ana_kosegen_maske[kare] |= 1 << (r * 8 + s)
                r += 1
                s += 1
                
            # Yan köşegen maskesi
            r, s = satir, sutun
            while r >= 0 and s < 8:
                self.yan_kosegen_maske[kare] |= 1 << (r * 8 + s)
                r -= 1
                s += 1
            r, s = satir + 1, sutun - 1
            while r < 8 and s >= 0:
                self.yan_kosegen_maske[kare] |= 1 << (r * 8 + s)
                r += 1
                s -= 1

    def tum_hamleleri_uret(self, tahta):
        """Mevcut pozisyon için tüm pseudo-legal hamleleri üret"""
        self.hamleler = []
        renk = 'beyaz' if tahta.beyaz_sira else 'siyah'
        
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

        return self.hamleler

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

        # Dört doğrusal yön
        for yon in [1, -1, 8, -8]:
            hedef = kare + yon

            while 0 <= hedef < 64:
                # Yatay hareket sınır kontrolü
                if yon in [1, -1]:
                    if (hedef // 8) != (kare // 8):
                        break

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

        # Dört çapraz yön
        for yon in [7, 9, -7, -9]:
            hedef = kare + yon

            while 0 <= hedef < 64:
                # Çapraz sınır kontrolü
                if abs((hedef % 8) - (kare % 8)) != abs((hedef // 8) - (kare // 8)):
                    break

                if tahta.tum_taslar & (1 << hedef):
                    if saldirgan_taslar & (1 << hedef):
                        return True
                    break

                hedef += yon

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
                        self.hamleler.append((kaynak, hedef, 'piyon', 'terfi', terfi_tasi))
                else:
                    self.hamleler.append((kaynak, hedef, 'piyon', 'normal'))

                # İki kare ileri (başlangıç pozisyonundan)
                if satir == baslangic_satiri:
                    hedef2 = kaynak + 2 * yon
                    if 0 <= hedef2 < 64 and not (tum_taslar & (1 << hedef2)):
                        self.hamleler.append((kaynak, hedef2, 'piyon', 'iki_kare'))

            # Çapraz saldırılar
            saldiri_maskeleri = self.beyaz_piyon_saldiri if beyaz else self.siyah_piyon_saldiri
            saldirilar = saldiri_maskeleri[kaynak] & dusman_taslar

            while saldirilar:
                hedef = tahta.en_dusuk_bit_al(saldirilar)
                saldirilar = tahta.en_dusuk_bit_kaldir(saldirilar)

                if satir + (1 if beyaz else -1) == terfi_satiri:
                    # Terfi ile alma
                    for terfi_tasi in ['vezir', 'kale', 'fil', 'at']:
                        self.hamleler.append((kaynak, hedef, 'piyon', 'terfi_alma', terfi_tasi))
                else:
                    self.hamleler.append((kaynak, hedef, 'piyon', 'alma'))

            # En passant
            if tahta.en_passant_kare != -1:
                if saldiri_maskeleri[kaynak] & (1 << tahta.en_passant_kare):
                    self.hamleler.append((kaynak, tahta.en_passant_kare, 'piyon', 'en_passant'))

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
                self.hamleler.append((kaynak, hedef, 'at', hamle_turu))

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
                    self.hamleler.append((kaynak, hedef, 'fil', hamle_turu))

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
                    self.hamleler.append((kaynak, hedef, 'kale', hamle_turu))

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
                    self.hamleler.append((kaynak, hedef, 'vezir', hamle_turu))

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
            self.hamleler.append((kaynak, hedef, 'sah', hamle_turu))

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
                        self.hamleler.append((4, 6, 'sah', 'kisa_rok'))

            if tahta.beyaz_uzun_rok:
                # Uzun rok: e1-c1
                if not ((tahta.tum_taslar & 0x0E)):  # b1, c1, d1 boş
                    # Şah ve geçiş kareleri saldırı altında olmamalı
                    if not self.saldiri_altinda_mi(tahta, 4, False) and \
                       not self.saldiri_altinda_mi(tahta, 3, False) and \
                       not self.saldiri_altinda_mi(tahta, 2, False):
                        self.hamleler.append((4, 2, 'sah', 'uzun_rok'))
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
                        self.hamleler.append((60, 62, 'sah', 'kisa_rok'))

            if tahta.siyah_uzun_rok:
                # Uzun rok: e8-c8
                if not ((tahta.tum_taslar & 0x0E00000000000000)):  # b8, c8, d8 boş
                    # Şah ve geçiş kareleri saldırı altında olmamalı
                    if not self.saldiri_altinda_mi(tahta, 60, True) and \
                       not self.saldiri_altinda_mi(tahta, 59, True) and \
                       not self.saldiri_altinda_mi(tahta, 58, True):
                        self.hamleler.append((60, 58, 'sah', 'uzun_rok'))

    def kareye_saldirilar(self, tahta, kare, saldiran_renk):
        """Belirtilen kareye hangi taşların saldırdığını bul"""
        saldiran_taslar = []
        
        if saldiran_renk == 'beyaz':
            # Beyaz piyon saldırıları
            piyon_saldiri_kaynaklari = []
            satir, sutun = divmod(kare, 8)
            if satir > 0:  # Beyaz piyonlar yukarıdan saldırır
                if sutun > 0 and tahta.beyaz_piyon & (1 << ((satir-1)*8 + sutun-1)):
                    piyon_saldiri_kaynaklari.append((satir-1)*8 + sutun-1)
                if sutun < 7 and tahta.beyaz_piyon & (1 << ((satir-1)*8 + sutun+1)):
                    piyon_saldiri_kaynaklari.append((satir-1)*8 + sutun+1)
            saldiran_taslar.extend([('piyon', k) for k in piyon_saldiri_kaynaklari])
            
            # Beyaz at saldırıları
            at_kaynaklari = []
            muhtemel_atlar = self.at_hamle_maskeleri[kare] & tahta.beyaz_at
            while muhtemel_atlar:
                kaynak = (muhtemel_atlar & -muhtemel_atlar).bit_length() - 1
                at_kaynaklari.append(kaynak)
                muhtemel_atlar &= muhtemel_atlar - 1
            saldiran_taslar.extend([('at', k) for k in at_kaynaklari])
            
            # Beyaz fil saldırıları
            fil_kaynaklari = self._kosegen_saldiri_kaynaklari(tahta, kare, tahta.beyaz_fil)
            saldiran_taslar.extend([('fil', k) for k in fil_kaynaklari])
            
            # Beyaz kale saldırıları
            kale_kaynaklari = self._duz_saldiri_kaynaklari(tahta, kare, tahta.beyaz_kale)
            saldiran_taslar.extend([('kale', k) for k in kale_kaynaklari])
            
            # Beyaz vezir saldırıları
            vezir_kaynaklari = self._kosegen_saldiri_kaynaklari(tahta, kare, tahta.beyaz_vezir)
            vezir_kaynaklari.extend(self._duz_saldiri_kaynaklari(tahta, kare, tahta.beyaz_vezir))
            saldiran_taslar.extend([('vezir', k) for k in vezir_kaynaklari])
            
            # Beyaz şah saldırıları
            sah_kaynaklari = []
            muhtemel_sah = self.sah_hamle_maskeleri[kare] & tahta.beyaz_sah
            if muhtemel_sah:
                kaynak = (muhtemel_sah & -muhtemel_sah).bit_length() - 1
                sah_kaynaklari.append(kaynak)
            saldiran_taslar.extend([('sah', k) for k in sah_kaynaklari])
            
        else:  # Siyah saldırıları
            # Siyah piyon saldırıları
            piyon_saldiri_kaynaklari = []
            satir, sutun = divmod(kare, 8)
            if satir < 7:  # Siyah piyonlar aşağıdan saldırır
                if sutun > 0 and tahta.siyah_piyon & (1 << ((satir+1)*8 + sutun-1)):
                    piyon_saldiri_kaynaklari.append((satir+1)*8 + sutun-1)
                if sutun < 7 and tahta.siyah_piyon & (1 << ((satir+1)*8 + sutun+1)):
                    piyon_saldiri_kaynaklari.append((satir+1)*8 + sutun+1)
            saldiran_taslar.extend([('piyon', k) for k in piyon_saldiri_kaynaklari])
            
            # Siyah at saldırıları
            at_kaynaklari = []
            muhtemel_atlar = self.at_hamle_maskeleri[kare] & tahta.siyah_at
            while muhtemel_atlar:
                kaynak = (muhtemel_atlar & -muhtemel_atlar).bit_length() - 1
                at_kaynaklari.append(kaynak)
                muhtemel_atlar &= muhtemel_atlar - 1
            saldiran_taslar.extend([('at', k) for k in at_kaynaklari])
            
            # Siyah fil saldırıları
            fil_kaynaklari = self._kosegen_saldiri_kaynaklari(tahta, kare, tahta.siyah_fil)
            saldiran_taslar.extend([('fil', k) for k in fil_kaynaklari])
            
            # Siyah kale saldırıları
            kale_kaynaklari = self._duz_saldiri_kaynaklari(tahta, kare, tahta.siyah_kale)
            saldiran_taslar.extend([('kale', k) for k in kale_kaynaklari])
            
            # Siyah vezir saldırıları
            vezir_kaynaklari = self._kosegen_saldiri_kaynaklari(tahta, kare, tahta.siyah_vezir)
            vezir_kaynaklari.extend(self._duz_saldiri_kaynaklari(tahta, kare, tahta.siyah_vezir))
            saldiran_taslar.extend([('vezir', k) for k in vezir_kaynaklari])
            
            # Siyah şah saldırıları
            sah_kaynaklari = []
            muhtemel_sah = self.sah_hamle_maskeleri[kare] & tahta.siyah_sah
            if muhtemel_sah:
                kaynak = (muhtemel_sah & -muhtemel_sah).bit_length() - 1
                sah_kaynaklari.append(kaynak)
            saldiran_taslar.extend([('sah', k) for k in sah_kaynaklari])
            
        return saldiran_taslar
        
    def _kosegen_saldiri_kaynaklari(self, tahta, hedef, tas_bitboard):
        """Köşegen saldırı yapan taşların kaynaklarını bul"""
        kaynak_kareler = []
        tum_taslar = tahta.tum_taslar
        
        # 4 köşegen yön kontrol et
        yonler = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        hedef_satir, hedef_sutun = divmod(hedef, 8)
        
        for dy, dx in yonler:
            satir, sutun = hedef_satir + dy, hedef_sutun + dx
            
            while 0 <= satir < 8 and 0 <= sutun < 8:
                kare = satir * 8 + sutun
                
                if tum_taslar & (1 << kare):
                    if tas_bitboard & (1 << kare):
                        kaynak_kareler.append(kare)
                    break
                    
                satir += dy
                sutun += dx
                
        return kaynak_kareler
        
    def _duz_saldiri_kaynaklari(self, tahta, hedef, tas_bitboard):
        """Düz çizgide saldırı yapan taşların kaynaklarını bul"""
        kaynak_kareler = []
        tum_taslar = tahta.tum_taslar
        
        # 4 düz yön kontrol et
        yonler = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        hedef_satir, hedef_sutun = divmod(hedef, 8)
        
        for dy, dx in yonler:
            satir, sutun = hedef_satir + dy, hedef_sutun + dx
            
            while 0 <= satir < 8 and 0 <= sutun < 8:
                kare = satir * 8 + sutun
                
                if tum_taslar & (1 << kare):
                    if tas_bitboard & (1 << kare):
                        kaynak_kareler.append(kare)
                    break
                    
                satir += dy
                sutun += dx
                
        return kaynak_kareler