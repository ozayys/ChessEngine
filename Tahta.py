"""
Bitboard tabanlı satranç tahtası implementasyonu.
64-bit integer ile her taş türü ve rengi için ayrı bitboard.
"""


class Tahta:
    def __init__(self):
        # Bitboard tanımları - her taş türü için ayrı 64-bit integer
        self.beyaz_piyon = 0x000000000000FF00
        self.beyaz_kale = 0x0000000000000081
        self.beyaz_at = 0x0000000000000042
        self.beyaz_fil = 0x0000000000000024
        self.beyaz_vezir = 0x0000000000000008
        self.beyaz_sah = 0x0000000000000010

        self.siyah_piyon = 0x00FF000000000000
        self.siyah_kale = 0x8100000000000000
        self.siyah_at = 0x4200000000000000
        self.siyah_fil = 0x2400000000000000
        self.siyah_vezir = 0x0800000000000000
        self.siyah_sah = 0x1000000000000000

        # Hamle hakları ve durumlar
        self.beyaz_sira = True
        self.beyaz_kisa_rok = True
        self.beyaz_uzun_rok = True
        self.siyah_kisa_rok = True
        self.siyah_uzun_rok = True
        self.en_passant_kare = -1
        self.yarim_hamle_sayici = 0
        self.hamle_sayisi = 1

        # Precalculated masks ve tablolar
        self._maskeleri_hazirla()

    def _maskeleri_hazirla(self):
        """Sık kullanılan bit maskelerini önceden hesapla"""
        # Satır ve sütun maskeleri
        self.satir_maskeleri = [0xFF << (8 * i) for i in range(8)]
        self.sutun_maskeleri = [0x0101010101010101 << i for i in range(8)]

        # Köşegen maskeleri
        self.ana_kosegen = 0x8040201008040201
        self.yan_kosegen = 0x0102040810204080

        # Kare bit maskeleri
        self.kare_maskeleri = [1 << i for i in range(64)]

    @property
    def beyaz_taslar(self):
        """Tüm beyaz taşların birleşik bitboard'u"""
        return (self.beyaz_piyon | self.beyaz_kale | self.beyaz_at |
                self.beyaz_fil | self.beyaz_vezir | self.beyaz_sah)

    @property
    def siyah_taslar(self):
        """Tüm siyah taşların birleşik bitboard'u"""
        return (self.siyah_piyon | self.siyah_kale | self.siyah_at |
                self.siyah_fil | self.siyah_vezir | self.siyah_sah)

    @property
    def tum_taslar(self):
        """Tüm taşların birleşik bitboard'u"""
        return self.beyaz_taslar | self.siyah_taslar

    def bit_kontrol_et(self, kare):
        """Belirtilen karede taş var mı kontrol et"""
        return (self.tum_taslar & self.kare_maskeleri[kare]) != 0

    def tas_turu_al(self, kare):
        """Belirtilen karedeki taşın türünü ve rengini döndür"""
        if not self.bit_kontrol_et(kare):
            return None

        mask = self.kare_maskeleri[kare]

        # Beyaz taşlar
        if self.beyaz_piyon & mask: return ('beyaz', 'piyon')
        if self.beyaz_kale & mask: return ('beyaz', 'kale')
        if self.beyaz_at & mask: return ('beyaz', 'at')
        if self.beyaz_fil & mask: return ('beyaz', 'fil')
        if self.beyaz_vezir & mask: return ('beyaz', 'vezir')
        if self.beyaz_sah & mask: return ('beyaz', 'sah')

        # Siyah taşlar
        if self.siyah_piyon & mask: return ('siyah', 'piyon')
        if self.siyah_kale & mask: return ('siyah', 'kale')
        if self.siyah_at & mask: return ('siyah', 'at')
        if self.siyah_fil & mask: return ('siyah', 'fil')
        if self.siyah_vezir & mask: return ('siyah', 'vezir')
        if self.siyah_sah & mask: return ('siyah', 'sah')

        return None

    def karedeki_tas(self, kare):
        """Alias - GUI uyumluluğu için"""
        return self.tas_turu_al(kare)

    def tas_ekle(self, kare, renk, tur):
        """Belirtilen kareye taş ekle"""
        mask = self.kare_maskeleri[kare]

        if renk == 'beyaz':
            if tur == 'piyon':
                self.beyaz_piyon |= mask
            elif tur == 'kale':
                self.beyaz_kale |= mask
            elif tur == 'at':
                self.beyaz_at |= mask
            elif tur == 'fil':
                self.beyaz_fil |= mask
            elif tur == 'vezir':
                self.beyaz_vezir |= mask
            elif tur == 'sah':
                self.beyaz_sah |= mask
        else:
            if tur == 'piyon':
                self.siyah_piyon |= mask
            elif tur == 'kale':
                self.siyah_kale |= mask
            elif tur == 'at':
                self.siyah_at |= mask
            elif tur == 'fil':
                self.siyah_fil |= mask
            elif tur == 'vezir':
                self.siyah_vezir |= mask
            elif tur == 'sah':
                self.siyah_sah |= mask

    def tas_kaldir(self, kare):
        """Belirtilen kareden taşı kaldır"""
        mask = ~self.kare_maskeleri[kare]

        self.beyaz_piyon &= mask
        self.beyaz_kale &= mask
        self.beyaz_at &= mask
        self.beyaz_fil &= mask
        self.beyaz_vezir &= mask
        self.beyaz_sah &= mask

        self.siyah_piyon &= mask
        self.siyah_kale &= mask
        self.siyah_at &= mask
        self.siyah_fil &= mask
        self.siyah_vezir &= mask
        self.siyah_sah &= mask

    def hamle_yap(self, hamle):
        """Hamleyi tahtaya uygula - tuple formatında"""
        try:
            if not hamle or len(hamle) < 2:
                print(f"DEBUG: Geçersiz hamle formatı: {hamle}")
                return False

            kaynak = hamle[0]
            hedef = hamle[1]
            ozel_hamle = hamle[3] if len(hamle) > 3 else None

            # Kare sınırları kontrolü
            if not (0 <= kaynak <= 63) or not (0 <= hedef <= 63):
                print(f"DEBUG: Geçersiz kare: kaynak={kaynak}, hedef={hedef}")
                return False

            # Kaynak karedeki taşı al
            tas_bilgisi = self.tas_turu_al(kaynak)
            if not tas_bilgisi:
                print(f"DEBUG: Kaynak karede taş yok: {kaynak}")
                return False

            renk, tur = tas_bilgisi

            # Doğru renk kontrolü
            if (renk == 'beyaz') != self.beyaz_sira:
                print(f"DEBUG: Yanlış renk: {renk}, sıra: {'beyaz' if self.beyaz_sira else 'siyah'}")
                return False

            # Hedef karedeki taşı kaldır (eğer varsa)
            self.tas_kaldir(hedef)

            # Kaynak karedeki taşı kaldır
            self.tas_kaldir(kaynak)

            # Özel hamle durumları
            if ozel_hamle == 'kisa_rok':
                if renk == 'beyaz':
                    self.tas_kaldir(7)  # h1
                    self.tas_ekle(5, 'beyaz', 'kale')  # f1
                    self.tas_ekle(6, 'beyaz', 'sah')  # g1
                else:
                    self.tas_kaldir(63)  # h8
                    self.tas_ekle(61, 'siyah', 'kale')  # f8
                    self.tas_ekle(62, 'siyah', 'sah')  # g8

            elif ozel_hamle == 'uzun_rok':
                if renk == 'beyaz':
                    self.tas_kaldir(0)  # a1
                    self.tas_ekle(3, 'beyaz', 'kale')  # d1
                    self.tas_ekle(2, 'beyaz', 'sah')  # c1
                else:
                    self.tas_kaldir(56)  # a8
                    self.tas_ekle(59, 'siyah', 'kale')  # d8
                    self.tas_ekle(58, 'siyah', 'sah')  # c8

            elif ozel_hamle == 'en_passant':
                # Alınan piyonu kaldır
                alinen_piyon_kare = hedef + (-8 if renk == 'beyaz' else 8)
                self.tas_kaldir(alinen_piyon_kare)
                self.tas_ekle(hedef, renk, tur)

            elif ozel_hamle in ['terfi', 'terfi_alma']:
                # Piyon terfisi
                terfi_tasi = hamle[4] if len(hamle) > 4 else 'vezir'
                self.tas_ekle(hedef, renk, terfi_tasi)

            elif ozel_hamle == 'iki_kare':
                # İki kare piyon hamlesi
                self.en_passant_kare = (kaynak + hedef) // 2
                self.tas_ekle(hedef, renk, tur)

            else:
                # Normal hamle
                self.tas_ekle(hedef, renk, tur)

            # Rok haklarını güncelle
            self._rok_haklarini_guncelle(kaynak, hedef, renk, tur)

            # En passant karesi sıfırla (iki kare piyon hamlesi dışında)
            if ozel_hamle != 'iki_kare':
                self.en_passant_kare = -1

            # Sırayı değiştir
            self.beyaz_sira = not self.beyaz_sira

            # Hamle sayısını artır
            if not self.beyaz_sira:  # Siyah oynadıysa
                self.hamle_sayisi += 1

            return True

        except Exception as e:
            print(f"DEBUG: Hamle yapma hatası: {e}, hamle: {hamle}")
            import traceback
            traceback.print_exc()
            return False

    def _rok_haklarini_guncelle(self, kaynak, hedef, renk, tur):
        """Rok haklarını güncelle"""
        if tur == 'sah':
            if renk == 'beyaz':
                self.beyaz_kisa_rok = False
                self.beyaz_uzun_rok = False
            else:
                self.siyah_kisa_rok = False
                self.siyah_uzun_rok = False

        elif tur == 'kale':
            if renk == 'beyaz':
                if kaynak == 0:  # a1
                    self.beyaz_uzun_rok = False
                elif kaynak == 7:  # h1
                    self.beyaz_kisa_rok = False
            else:
                if kaynak == 56:  # a8
                    self.siyah_uzun_rok = False
                elif kaynak == 63:  # h8
                    self.siyah_kisa_rok = False

        # Hedef karedeki kale yakalandıysa rok haklarını kaldır
        if hedef == 0:  # a1
            self.beyaz_uzun_rok = False
        elif hedef == 7:  # h1
            self.beyaz_kisa_rok = False
        elif hedef == 56:  # a8
            self.siyah_uzun_rok = False
        elif hedef == 63:  # h8
            self.siyah_kisa_rok = False

    def kopyala(self):
        """Tahtanın derin kopyasını oluştur"""
        yeni_tahta = Tahta()
        yeni_tahta.beyaz_piyon = self.beyaz_piyon
        yeni_tahta.beyaz_kale = self.beyaz_kale
        yeni_tahta.beyaz_at = self.beyaz_at
        yeni_tahta.beyaz_fil = self.beyaz_fil
        yeni_tahta.beyaz_vezir = self.beyaz_vezir
        yeni_tahta.beyaz_sah = self.beyaz_sah

        yeni_tahta.siyah_piyon = self.siyah_piyon
        yeni_tahta.siyah_kale = self.siyah_kale
        yeni_tahta.siyah_at = self.siyah_at
        yeni_tahta.siyah_fil = self.siyah_fil
        yeni_tahta.siyah_vezir = self.siyah_vezir
        yeni_tahta.siyah_sah = self.siyah_sah

        yeni_tahta.beyaz_sira = self.beyaz_sira
        yeni_tahta.beyaz_kisa_rok = self.beyaz_kisa_rok
        yeni_tahta.beyaz_uzun_rok = self.beyaz_uzun_rok
        yeni_tahta.siyah_kisa_rok = self.siyah_kisa_rok
        yeni_tahta.siyah_uzun_rok = self.siyah_uzun_rok
        yeni_tahta.en_passant_kare = self.en_passant_kare
        yeni_tahta.yarim_hamle_sayici = self.yarim_hamle_sayici
        yeni_tahta.hamle_sayisi = self.hamle_sayisi

        return yeni_tahta

    def bit_sayisi(self, bitboard):
        """Bitboard'daki set bit sayısını döndür (popcount)"""
        return bin(bitboard).count('1')

    def en_dusuk_bit_al(self, bitboard):
        """En düşük set bit'in pozisyonunu al"""
        if bitboard == 0:
            return -1
        return (bitboard & -bitboard).bit_length() - 1

    def en_dusuk_bit_kaldir(self, bitboard):
        """En düşük set bit'i kaldır"""
        return bitboard & (bitboard - 1)

    def yazdir(self):
        """Tahtayı konsola yazdır (debug amaçlı)"""
        print("  a b c d e f g h")
        for satir in range(7, -1, -1):
            print(f"{satir + 1} ", end="")
            for sutun in range(8):
                kare = satir * 8 + sutun
                tas_bilgisi = self.tas_turu_al(kare)

                if tas_bilgisi:
                    renk, tur = tas_bilgisi
                    sembol = self._tas_sembolu_al(renk, tur)
                    print(f"{sembol} ", end="")
                else:
                    print(". ", end="")
            print(f" {satir + 1}")
        print("  a b c d e f g h")
        print(f"Sıra: {'Beyaz' if self.beyaz_sira else 'Siyah'}")

    def _tas_sembolu_al(self, renk, tur):
        """Taş sembolü döndür"""
        semboller = {
            ('beyaz', 'piyon'): '♙', ('beyaz', 'kale'): '♖', ('beyaz', 'at'): '♘',
            ('beyaz', 'fil'): '♗', ('beyaz', 'vezir'): '♕', ('beyaz', 'sah'): '♔',
            ('siyah', 'piyon'): '♟', ('siyah', 'kale'): '♜', ('siyah', 'at'): '♞',
            ('siyah', 'fil'): '♝', ('siyah', 'vezir'): '♛', ('siyah', 'sah'): '♚'
        }
        return semboller.get((renk, tur), '?')

    def sah_tehdit_altinda_mi(self, renk):
        """Belirtilen rengin şahı tehdit altında mı kontrol et"""
        from HamleUret import HamleUretici
        hamle_uretici = HamleUretici()
        
        # Şahın pozisyonunu bul
        sah_bitboard = self.beyaz_sah if renk == 'beyaz' else self.siyah_sah
        if sah_bitboard == 0:
            return False
        
        sah_pozisyonu = self.en_dusuk_bit_al(sah_bitboard)
        
        # Karşı tarafın saldırı kontrolü
        return hamle_uretici.saldiri_altinda_mi(self, sah_pozisyonu, renk == 'siyah')

    def legal_hamle_var_mi(self):
        """Mevcut oyuncunun legal hamlesi var mı kontrol et"""
        from LegalHamle import LegalHamleBulucu
        legal_bulucu = LegalHamleBulucu()
        legal_hamleler = legal_bulucu.legal_hamleleri_bul(self)
        return len(legal_hamleler) > 0

    def mat_mi(self):
        """Mat durumu kontrolü"""
        # Önce şah tehdidinde mi kontrol et (hızlı kontrol)
        renk = 'beyaz' if self.beyaz_sira else 'siyah'
        sah_tehdidinde = self.sah_tehdit_altinda_mi(renk)
        
        # Şah tehdidinde değilse mat olamaz
        if not sah_tehdidinde:
            return False
        
        # Şah tehdidindeyse legal hamle var mı kontrol et
        return not self.legal_hamle_var_mi()

    def pat_mi(self):
        """Pat durumu kontrolü"""
        # Önce şah tehdidinde mi kontrol et (hızlı kontrol)
        renk = 'beyaz' if self.beyaz_sira else 'siyah'
        sah_tehdidinde = self.sah_tehdit_altinda_mi(renk)
        
        # Şah tehdidindeyse pat olamaz
        if sah_tehdidinde:
            return False
        
        # Şah tehdidinde değilse legal hamle var mı kontrol et
        return not self.legal_hamle_var_mi()

    def oyun_bitti_mi(self):
        """Oyun bitmiş mi kontrol et (mat veya pat)"""
        # Önce legal hamle var mı kontrol et (tek kontrol)
        if self.legal_hamle_var_mi():
            return False
        
        # Legal hamle yoksa mat mı pat mı kontrol et
        return True

    def oyun_sonu_durumu(self):
        """Oyun sonu durumunu döndür"""
        # Önce legal hamle var mı kontrol et
        if self.legal_hamle_var_mi():
            return (None, None)
        
        # Legal hamle yoksa mat veya pat durumu
        renk = 'beyaz' if self.beyaz_sira else 'siyah'
        if self.sah_tehdit_altinda_mi(renk):
            # Mat - karşı taraf kazandı
            kazanan = 'siyah' if self.beyaz_sira else 'beyaz'
            return ('mat', kazanan)
        else:
            # Pat
            return ('pat', None)