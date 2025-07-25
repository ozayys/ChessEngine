"""
Mat ve Pat kontrol modülü.
Oyun bitişi durumlarını tespit eder.
"""

from HamleUret import HamleUretici


class MatPatKontrolcu:
    def __init__(self):
        self.hamle_uretici = HamleUretici()
    
    def oyun_durumu_kontrol(self, tahta):
        """
        Oyun durumunu kontrol et
        Returns: 'devam', 'mat_beyaz', 'mat_siyah', 'pat'
        """
        legal_hamleler = self._legal_hamleleri_bul(tahta)
        
        if len(legal_hamleler) == 0:
            # Hiç legal hamle yok
            if self.sah_tehdidinde_mi(tahta, tahta.beyaz_sira):
                # Şah tehdidinde ve hamle yok = Mat
                return 'mat_siyah' if tahta.beyaz_sira else 'mat_beyaz'
            else:
                # Şah tehdidinde değil ama hamle yok = Pat
                return 'pat'
        
        return 'devam'
    
    def is_mate(self, tahta):
        """Mat durumu kontrolü"""
        durum = self.oyun_durumu_kontrol(tahta)
        return durum in ['mat_beyaz', 'mat_siyah']
    
    def is_stalemate(self, tahta):
        """Pat durumu kontrolü"""
        return self.oyun_durumu_kontrol(tahta) == 'pat'
    
    def is_game_over(self, tahta):
        """Oyun bitti mi kontrolü"""
        return self.oyun_durumu_kontrol(tahta) != 'devam'
    
    def get_mate_score(self, tahta, derinlik):
        """Mat skoru hesapla (derinliğe göre)"""
        durum = self.oyun_durumu_kontrol(tahta)
        
        if durum == 'mat_beyaz':
            return 10000 - derinlik  # Beyaz kazandı, erken mat daha iyi
        elif durum == 'mat_siyah':
            return -10000 + derinlik  # Siyah kazandı, geç mat daha iyi
        elif durum == 'pat':
            return 0  # Pat = berabere
        
        return None  # Oyun devam ediyor
    
    def sah_tehdidinde_mi(self, tahta, beyaz_sah):
        """Şahın tehdit altında olup olmadığını kontrol et"""
        try:
            # Şahın pozisyonunu bul
            if beyaz_sah:
                sah_bitboard = tahta.beyaz_sah
            else:
                sah_bitboard = tahta.siyah_sah
            
            if sah_bitboard == 0:
                return False
            
            sah_pozisyonu = tahta.en_dusuk_bit_al(sah_bitboard)
            
            # Rakip taşların saldırı kontrolü
            return self.hamle_uretici.saldiri_altinda_mi(tahta, sah_pozisyonu, not beyaz_sah)
            
        except Exception as e:
            return False
    
    def _legal_hamleleri_bul(self, tahta):
        """Legal hamleleri bul (basit implementasyon)"""
        try:
            pseudo_legal = self.hamle_uretici.tum_hamleleri_uret(tahta)
            legal_hamleler = []
            
            for hamle in pseudo_legal:
                # Hamleyi geçici olarak yap
                tahta_kopyasi = tahta.kopyala()
                if tahta_kopyasi.hamle_yap(hamle):
                    # Hamle sonrası kendi şahımız tehdit altında mı?
                    if not self.sah_tehdidinde_mi(tahta_kopyasi, not tahta_kopyasi.beyaz_sira):
                        legal_hamleler.append(hamle)
            
            return legal_hamleler
            
        except Exception as e:
            return []
    
    def check_insufficient_material(self, tahta):
        """Yetersiz malzeme kontrolü (gelecek için)"""
        # Basit implementasyon: sadece şahlar kaldıysa
        toplam_tas = (tahta.bit_sayisi(tahta.beyaz_piyon) + 
                     tahta.bit_sayisi(tahta.beyaz_kale) +
                     tahta.bit_sayisi(tahta.beyaz_at) +
                     tahta.bit_sayisi(tahta.beyaz_fil) +
                     tahta.bit_sayisi(tahta.beyaz_vezir) +
                     tahta.bit_sayisi(tahta.siyah_piyon) +
                     tahta.bit_sayisi(tahta.siyah_kale) +
                     tahta.bit_sayisi(tahta.siyah_at) +
                     tahta.bit_sayisi(tahta.siyah_fil) +
                     tahta.bit_sayisi(tahta.siyah_vezir))
        
        return toplam_tas == 0  # Sadece şahlar kaldı