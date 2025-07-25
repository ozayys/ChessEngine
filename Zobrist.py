"""
Zobrist hashing implementasyonu. Tahta pozisyonları için hızlı hash hesaplama.
Transposition table ve tekrar pozisyon tespiti için optimize edilmiş.
"""

import random

class ZobristHash:
    def __init__(self, seed=12345):
        """Zobrist hash tablosunu başlat"""
        random.seed(seed)  # Tekrarlanabilir rastgele sayılar için

        # Her taş türü ve pozisyon için rastgele 64-bit sayılar
        self.tas_hash_tablosu = {}
        self._hash_tablosunu_olustur()

        # Özel durumlar için hash değerleri
        self.beyaz_sira_hash = self._rastgele_64bit()
        self.rok_hash = {
            'beyaz_kisa': self._rastgele_64bit(),
            'beyaz_uzun': self._rastgele_64bit(),
            'siyah_kisa': self._rastgele_64bit(),
            'siyah_uzun': self._rastgele_64bit()
        }

        # En passant için hash değerleri (her sütun için)
        self.en_passant_hash = [self._rastgele_64bit() for _ in range(8)]

    def _rastgele_64bit(self):
        """64-bit rastgele sayı üret"""
        return random.getrandbits(64)

    def _hash_tablosunu_olustur(self):
        """Tüm taş türleri ve pozisyonlar için hash tablosunu oluştur"""
        tas_turleri = [
            ('beyaz', 'piyon'), ('beyaz', 'kale'), ('beyaz', 'at'),
            ('beyaz', 'fil'), ('beyaz', 'vezir'), ('beyaz', 'sah'),
            ('siyah', 'piyon'), ('siyah', 'kale'), ('siyah', 'at'),
            ('siyah', 'fil'), ('siyah', 'vezir'), ('siyah', 'sah')
        ]

        for renk, tur in tas_turleri:
            self.tas_hash_tablosu[(renk, tur)] = [self._rastgele_64bit() for _ in range(64)]

    def pozisyon_hash_hesapla(self, tahta):
        """Tahta pozisyonu için tam hash hesapla"""
        hash_degeri = 0

        # Tüm taşlar için hash hesapla
        for kare in range(64):
            tas_bilgisi = tahta.tas_turu_al(kare)
            if tas_bilgisi:
                renk, tur = tas_bilgisi
                hash_degeri ^= self.tas_hash_tablosu[(renk, tur)][kare]

        # Sıra hash'i
        if tahta.beyaz_sira:
            hash_degeri ^= self.beyaz_sira_hash

        # Rok hakları hash'i
        if tahta.beyaz_kisa_rok:
            hash_degeri ^= self.rok_hash['beyaz_kisa']
        if tahta.beyaz_uzun_rok:
            hash_degeri ^= self.rok_hash['beyaz_uzun']
        if tahta.siyah_kisa_rok:
            hash_degeri ^= self.rok_hash['siyah_kisa']
        if tahta.siyah_uzun_rok:
            hash_degeri ^= self.rok_hash['siyah_uzun']

        # En passant hash'i
        if tahta.en_passant_kare != -1:
            sutun = tahta.en_passant_kare % 8
            hash_degeri ^= self.en_passant_hash[sutun]

        return hash_degeri

    def hamle_hash_guncelle(self, mevcut_hash, tahta, hamle, onceki_durum=None):
        """Hamle sonrası hash'i artımlı olarak güncelle"""
        kaynak, hedef = hamle[0], hamle[1]
        hamle_turu = hamle[3] if len(hamle) > 3 else 'normal'

        yeni_hash = mevcut_hash

        # Sıra değişimi
        yeni_hash ^= self.beyaz_sira_hash

        # Kaynak karedeki taşı kaldır
        if onceki_durum and onceki_durum.get('kaynak_tas'):
            renk, tur = onceki_durum['kaynak_tas']
            yeni_hash ^= self.tas_hash_tablosu[(renk, tur)][kaynak]

        # Hedef karedeki taşı kaldır (eğer alma hamlesi ise)
        if onceki_durum and onceki_durum.get('hedef_tas'):
            renk, tur = onceki_durum['hedef_tas']
            yeni_hash ^= self.tas_hash_tablosu[(renk, tur)][hedef]

        # Yeni pozisyondaki taşı ekle
        yeni_tas_bilgisi = tahta.tas_turu_al(hedef)
        if yeni_tas_bilgisi:
            renk, tur = yeni_tas_bilgisi
            yeni_hash ^= self.tas_hash_tablosu[(renk, tur)][hedef]

        # Özel hamle durumları
        if hamle_turu == 'kisa_rok':
            # Kale hareketini de hash'e dahil et
            renk = 'beyaz' if onceki_durum['beyaz_sira'] else 'siyah'
            if renk == 'beyaz':
                yeni_hash ^= self.tas_hash_tablosu[('beyaz', 'kale')][7]  # h1'den kaldır
                yeni_hash ^= self.tas_hash_tablosu[('beyaz', 'kale')][5]  # f1'e ekle
            else:
                yeni_hash ^= self.tas_hash_tablosu[('siyah', 'kale')][63]  # h8'den kaldır
                yeni_hash ^= self.tas_hash_tablosu[('siyah', 'kale')][61]  # f8'e ekle

        elif hamle_turu == 'uzun_rok':
            # Kale hareketini de hash'e dahil et
            renk = 'beyaz' if onceki_durum['beyaz_sira'] else 'siyah'
            if renk == 'beyaz':
                yeni_hash ^= self.tas_hash_tablosu[('beyaz', 'kale')][0]  # a1'den kaldır
                yeni_hash ^= self.tas_hash_tablosu[('beyaz', 'kale')][3]  # d1'e ekle
            else:
                yeni_hash ^= self.tas_hash_tablosu[('siyah', 'kale')][56]  # a8'den kaldır
                yeni_hash ^= self.tas_hash_tablosu[('siyah', 'kale')][59]  # d8'e ekle

        elif hamle_turu == 'en_passant':
            # Alınan piyonu hash'den çıkar
            if onceki_durum and 'alinen_piyon' in onceki_durum:
                renk, tur = onceki_durum['alinen_piyon']
                alinen_kare = onceki_durum['en_passant_hedef']
                yeni_hash ^= self.tas_hash_tablosu[(renk, tur)][alinen_kare]

        # Rok hakları değişimi
        if onceki_durum:
            # Eski rok haklarını çıkar
            if onceki_durum['beyaz_kisa_rok']:
                yeni_hash ^= self.rok_hash['beyaz_kisa']
            if onceki_durum['beyaz_uzun_rok']:
                yeni_hash ^= self.rok_hash['beyaz_uzun']
            if onceki_durum['siyah_kisa_rok']:
                yeni_hash ^= self.rok_hash['siyah_kisa']
            if onceki_durum['siyah_uzun_rok']:
                yeni_hash ^= self.rok_hash['siyah_uzun']

            # Yeni rok haklarını ekle
            if tahta.beyaz_kisa_rok:
                yeni_hash ^= self.rok_hash['beyaz_kisa']
            if tahta.beyaz_uzun_rok:
                yeni_hash ^= self.rok_hash['beyaz_uzun']
            if tahta.siyah_kisa_rok:
                yeni_hash ^= self.rok_hash['siyah_kisa']
            if tahta.siyah_uzun_rok:
                yeni_hash ^= self.rok_hash['siyah_uzun']

        # En passant değişimi
        if onceki_durum:
            # Eski en passant hash'ini çıkar
            if onceki_durum['en_passant_kare'] != -1:
                eski_sutun = onceki_durum['en_passant_kare'] % 8
                yeni_hash ^= self.en_passant_hash[eski_sutun]

            # Yeni en passant hash'ini ekle
            if tahta.en_passant_kare != -1:
                yeni_sutun = tahta.en_passant_kare % 8
                yeni_hash ^= self.en_passant_hash[yeni_sutun]

        return yeni_hash

    def hash_dogrula(self, tahta, beklenen_hash):
        """Hash doğruluğunu kontrol et (debug amaçlı)"""
        hesaplanan_hash = self.pozisyon_hash_hesapla(tahta)
        return hesaplanan_hash == beklenen_hash

    def hash_string(self, hash_degeri):
        """Hash değerini string olarak döndür (debug amaçlı)"""
        return f"0x{hash_degeri:016X}"


class TranspositionTable:
    """Zobrist hash tabanlı pozisyon saklama tablosu"""

    def __init__(self, boyut_mb=64):
        """Transposition table başlat"""
        # MB cinsinden boyutu entry sayısına çevir
        # Her entry: hash