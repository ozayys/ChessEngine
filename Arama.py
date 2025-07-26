"""
MiniMax ve Alpha-Beta Pruning algoritmaları.
Derinlik bazlı arama.
Transposition table, killer moves ve hamle sıralama optimizasyonları.
"""

from HamleUret import HamleUretici
from Degerlendirme import Degerlendirici
from LegalHamle import LegalHamleBulucu
import copy
import time


class TranspositionTable:
    """Zobrist hash tabanlı transposition table"""
    def __init__(self, boyut_mb=32):
        # MB cinsinden boyutu entry sayısına çevir (her entry ~24 byte)
        self.boyut = (boyut_mb * 1024 * 1024) // 24
        self.tablo = {}
        self.hit = 0
        self.miss = 0
        
    def kaydet(self, hash_deger, derinlik, skor, bayrak, en_iyi_hamle=None):
        """Pozisyonu transposition table'a kaydet"""
        # Boyut kontrolü - eski girişleri temizle
        if len(self.tablo) > self.boyut:
            # En eski %25'ini sil
            silinecek = list(self.tablo.keys())[:len(self.tablo)//4]
            for key in silinecek:
                del self.tablo[key]
                
        self.tablo[hash_deger] = {
            'derinlik': derinlik,
            'skor': skor,
            'bayrak': bayrak,  # EXACT, LOWER, UPPER
            'en_iyi_hamle': en_iyi_hamle
        }
        
    def ara(self, hash_deger):
        """Pozisyonu transposition table'da ara"""
        if hash_deger in self.tablo:
            self.hit += 1
            return self.tablo[hash_deger]
        self.miss += 1
        return None
        
    def temizle(self):
        """Transposition table'ı temizle"""
        self.tablo.clear()
        self.hit = 0
        self.miss = 0


class Arama:
    def __init__(self, derinlik=6):
        self.derinlik = derinlik
        self.hamle_uretici = HamleUretici()
        self.degerlendirme = Degerlendirici()
        self.legal_bulucu = LegalHamleBulucu()
        self.dugum_sayisi = 0
        self.max_derinlik = 0
        
        # Optimizasyon yapıları
        self.transposition_table = TranspositionTable()
        self.killer_moves = {}  # Derinlik -> [hamle1, hamle2]
        self.history_table = {}  # (from, to) -> skor
        
        # Zaman yönetimi
        self.baslangic_zamani = 0
        self.zaman_limiti = 0
        self.zaman_asimi = False
        
        # PV araması mı?
        self._pv_aramasi = False

    def derinlik_degistir(self, yeni_derinlik):
        """Arama derinliğini değiştir"""
        self.derinlik = yeni_derinlik

    def en_iyi_hamle_bul(self, tahta, zaman_limiti=None):
        """Alpha-Beta pruning ile en iyi hamleyi bul"""
        self.dugum_sayisi = 0
        self.max_derinlik = 0
        self.baslangic_zamani = time.time()
        self.zaman_limiti = zaman_limiti if zaman_limiti else float('inf')
        self.zaman_asimi = False

        en_iyi_hamle = None
        en_iyi_skor = float('-inf') if tahta.beyaz_sira else float('inf')
        
        print(f"\n=== Arama Başlıyor - Derinlik: {self.derinlik} ===")

        try:
            # Legal hamleleri al
            hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)

            # Hamle yoksa None döndür
            if not hamleler:
                return None

            # Hamleleri sırala
            hamleler = self._hamleleri_sirala(tahta, hamleler, None)

            # İteratif derinleştirme
            aspiration_delta = 50  # Aspiration window başlangıç değeri
            
            for arama_derinligi in range(1, self.derinlik + 1):
                if self.zaman_asimi:
                    break
                
                print(f"  Derinlik {arama_derinligi} aramaya başlanıyor...")
                derinlik_baslangic = time.time()
                    
                temp_en_iyi_hamle = None
                temp_en_iyi_skor = float('-inf') if tahta.beyaz_sira else float('inf')
                
                # Aspiration window kullan (derinlik 3'ten sonra)
                if arama_derinligi >= 3 and en_iyi_skor != float('-inf') and en_iyi_skor != float('inf'):
                    asp_alpha = en_iyi_skor - aspiration_delta
                    asp_beta = en_iyi_skor + aspiration_delta
                else:
                    asp_alpha = float('-inf')
                    asp_beta = float('inf')
                
                for i, hamle in enumerate(hamleler):
                    if self._zaman_kontrolu():
                        self.zaman_asimi = True
                        break
                        
                    try:
                        # Hamleyi yap
                        tahta_kopyasi = tahta.kopyala()

                        if not tahta_kopyasi.hamle_yap(hamle):
                            continue

                        if tahta.beyaz_sira:  # Beyaz oynuyor (maksimize)
                            skor = self.alpha_beta(tahta_kopyasi, arama_derinligi - 1, 
                                                  asp_alpha, asp_beta, False)
                            if skor > temp_en_iyi_skor:
                                temp_en_iyi_skor = skor
                                temp_en_iyi_hamle = hamle
                        else:  # Siyah oynuyor (minimize)
                            skor = self.alpha_beta(tahta_kopyasi, arama_derinligi - 1, 
                                                  asp_alpha, asp_beta, True)
                            if skor < temp_en_iyi_skor:
                                temp_en_iyi_skor = skor
                                temp_en_iyi_hamle = hamle

                    except Exception as e:
                        print(f"Hamle değerlendirme hatası: {e}")
                        continue
                
                # Aspiration window fail kontrolü
                aspiration_fail = False
                if arama_derinligi >= 3 and en_iyi_skor != float('-inf') and en_iyi_skor != float('inf'):
                    if temp_en_iyi_skor <= asp_alpha or temp_en_iyi_skor >= asp_beta:
                        aspiration_fail = True
                        print(f"  Aspiration window fail! Skor: {temp_en_iyi_skor}, Window: [{asp_alpha}, {asp_beta}]")
                        
                        # Full window ile yeniden ara
                        temp_en_iyi_hamle = None
                        temp_en_iyi_skor = float('-inf') if tahta.beyaz_sira else float('inf')
                        
                        for i, hamle in enumerate(hamleler):
                            if self._zaman_kontrolu():
                                self.zaman_asimi = True
                                break
                                
                            try:
                                tahta_kopyasi = tahta.kopyala()
                                if not tahta_kopyasi.hamle_yap(hamle):
                                    continue

                                if tahta.beyaz_sira:
                                    skor = self.alpha_beta(tahta_kopyasi, arama_derinligi - 1, 
                                                          float('-inf'), float('inf'), False)
                                    if skor > temp_en_iyi_skor:
                                        temp_en_iyi_skor = skor
                                        temp_en_iyi_hamle = hamle
                                else:
                                    skor = self.alpha_beta(tahta_kopyasi, arama_derinligi - 1, 
                                                          float('-inf'), float('inf'), True)
                                    if skor < temp_en_iyi_skor:
                                        temp_en_iyi_skor = skor
                                        temp_en_iyi_hamle = hamle

                            except Exception as e:
                                print(f"Hamle değerlendirme hatası (aspiration retry): {e}")
                                continue
                
                # Bu derinlikte tamamlandıysa en iyi hamleyi güncelle
                if not self.zaman_asimi and temp_en_iyi_hamle:
                    en_iyi_hamle = temp_en_iyi_hamle
                    en_iyi_skor = temp_en_iyi_skor
                    
                    # Hamleleri en iyi hamle başta olacak şekilde yeniden sırala
                    if en_iyi_hamle in hamleler:
                        hamleler.remove(en_iyi_hamle)
                        hamleler.insert(0, en_iyi_hamle)
                    
                    # Aspiration window'u güncelle
                    if not aspiration_fail:
                        aspiration_delta = max(25, aspiration_delta // 2)  # Window'u daralt
                    else:
                        aspiration_delta = min(200, aspiration_delta * 2)  # Window'u genişlet
                    
                    derinlik_suresi = time.time() - derinlik_baslangic
                    print(f"  Derinlik {arama_derinligi} tamamlandı - Süre: {derinlik_suresi:.2f}s, En iyi skor: {en_iyi_skor}")

        except Exception as e:
            print(f"Arama genel hatası: {e}")
        
        toplam_sure = time.time() - self.baslangic_zamani
        
        if self.zaman_asimi:
            print(f"=== Arama Zaman Aşımı ile Tamamlandı ===")
            print(f"    Hedef derinlik: {self.derinlik}, Tamamlanan: {arama_derinligi-1 if 'arama_derinligi' in locals() else 0}")
            print(f"    Toplam süre: {toplam_sure:.2f}s, Düğüm sayısı: {self.dugum_sayisi}")
        else:
            print(f"=== Arama Tamamlandı - Hedef derinliğe ulaşıldı ({self.derinlik}) ===")
            print(f"    Toplam süre: {toplam_sure:.2f}s, Düğüm sayısı: {self.dugum_sayisi}")
        
        print()

        return en_iyi_hamle

    def _zaman_kontrolu(self):
        """Zaman aşımı kontrolü"""
        if self.zaman_limiti == float('inf'):
            return False
        return time.time() - self.baslangic_zamani > self.zaman_limiti

    def _hamleleri_sirala(self, tahta, hamleler, tt_hamle):
        """Hamleleri sırala - daha iyi sıralama için gelişmiş algoritma"""
        skorlu_hamleler = []
        
        for hamle in hamleler:
            skor = 0
            
            # Transposition table hamlesi en yüksek öncelik
            if tt_hamle and hamle == tt_hamle:
                skor += 10000
            
            # Killer moves
            derinlik_key = self.derinlik - tahta.yarim_hamle_sayici
            if derinlik_key in self.killer_moves:
                if hamle in self.killer_moves[derinlik_key]:
                    skor += 5000
            
            # Alma hamlesi kontrolü
            hedef_tas = tahta.tas_turu_al(hamle[1])
            if hedef_tas:
                # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
                kaynak_tas = tahta.tas_turu_al(hamle[0])
                if kaynak_tas:
                    victim_value = self._tas_degeri(hedef_tas[1])
                    attacker_value = self._tas_degeri(kaynak_tas[1])
                    skor += 1000 + (victim_value * 10) - attacker_value
            
            # History heuristic
            history_key = (hamle[0], hamle[1])
            if history_key in self.history_table:
                skor += self.history_table[history_key]
            
            # Merkeze doğru hamleler
            hedef_satir, hedef_sutun = divmod(hamle[1], 8)
            merkez_uzaklik = abs(hedef_satir - 3.5) + abs(hedef_sutun - 3.5)
            skor += (7 - merkez_uzaklik) * 10
            
            skorlu_hamleler.append((skor, hamle))
        
        # Skorlara göre sırala (büyükten küçüğe)
        skorlu_hamleler.sort(key=lambda x: x[0], reverse=True)
        
        return [hamle for skor, hamle in skorlu_hamleler]

    def _tas_degeri(self, tas_turu):
        """Taş değerlerini döndür"""
        degerler = {
            'piyon': 100,
            'at': 320,
            'fil': 330,
            'kale': 500,
            'vezir': 900,
            'sah': 20000
        }
        return degerler.get(tas_turu, 0)

    def alpha_beta(self, tahta, derinlik, alpha, beta, maksimize_ediyor):
        """Alpha-Beta pruning algoritması - optimizasyonlarla"""
        self.dugum_sayisi += 1
        self.max_derinlik = max(self.max_derinlik, self.derinlik - derinlik)
        
        # Zaman kontrolü
        if self._zaman_kontrolu():
            self.zaman_asimi = True
            return self.degerlendirme.degerlendir(tahta)

        # Transposition table kontrolü
        tt_entry = self.transposition_table.ara(tahta.zobrist_hash()) if hasattr(tahta, 'zobrist_hash') else None
        tt_hamle = None
        
        if tt_entry:
            # PV aramasında veya düşük derinliklerde TT kullanma
            if not self._pv_aramasi and tt_entry['derinlik'] >= derinlik:
                if tt_entry['bayrak'] == 'EXACT':
                    return tt_entry['skor']
                elif tt_entry['bayrak'] == 'LOWER':
                    alpha = max(alpha, tt_entry['skor'])
                elif tt_entry['bayrak'] == 'UPPER':
                    beta = min(beta, tt_entry['skor'])
                
                if alpha >= beta:
                    return tt_entry['skor']
            
            # Her zaman en iyi hamleyi kullan
            tt_hamle = tt_entry.get('en_iyi_hamle')

        # Oyun sonu kontrolü
        if tahta.mat_mi():
            skor = -self.degerlendirme.mat_skoru(self.derinlik - derinlik) if maksimize_ediyor else self.degerlendirme.mat_skoru(self.derinlik - derinlik)
            return skor
        
        if tahta.pat_mi():
            return 0

        # Derinlik 0'a ulaştığında - quiescence search ile değerlendir
        if derinlik <= 0:
            # Quiescence search ile durgun pozisyona ulaş
            return self.quiescence_search(tahta, alpha, beta, maksimize_ediyor)

        # Legal hamleleri al ve sırala
        hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)
        
        if not hamleler:
            return self.degerlendirme.degerlendir(tahta)
            
        hamleler = self._hamleleri_sirala(tahta, hamleler, tt_hamle)

        en_iyi_hamle = None
        hash_bayrak = 'UPPER'
        alpha_orig = alpha

        if maksimize_ediyor:
            max_eval = float('-inf')
            
            for hamle in hamleler:
                tahta_kopyasi = tahta.kopyala()
                tahta_kopyasi.hamle_yap(hamle)

                eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1, alpha, beta, False)
                
                if eval_skor > max_eval:
                    max_eval = eval_skor
                    en_iyi_hamle = hamle
                    
                if eval_skor > alpha:
                    alpha = eval_skor

                if alpha >= beta:
                    # Beta cutoff - killer move olarak kaydet
                    self._killer_move_ekle(derinlik, hamle)
                    self._history_guncelle(hamle, derinlik)
                    hash_bayrak = 'LOWER'
                    break
            
            # Hash bayrak belirleme
            if max_eval <= alpha_orig:
                hash_bayrak = 'UPPER'
            elif max_eval >= beta:
                hash_bayrak = 'LOWER'
            else:
                hash_bayrak = 'EXACT'

            if hasattr(tahta, 'zobrist_hash'):
                self.transposition_table.kaydet(tahta.zobrist_hash(), derinlik, max_eval, hash_bayrak, en_iyi_hamle)
            
            return max_eval
            
        else:
            min_eval = float('inf')
            beta_orig = beta
            
            for hamle in hamleler:
                tahta_kopyasi = tahta.kopyala()
                tahta_kopyasi.hamle_yap(hamle)

                eval_skor = self.alpha_beta(tahta_kopyasi, derinlik - 1, alpha, beta, True)
                
                if eval_skor < min_eval:
                    min_eval = eval_skor
                    en_iyi_hamle = hamle
                    
                if eval_skor < beta:
                    beta = eval_skor

                if beta <= alpha:
                    # Alpha cutoff - killer move olarak kaydet
                    self._killer_move_ekle(derinlik, hamle)
                    self._history_guncelle(hamle, derinlik)
                    hash_bayrak = 'UPPER'
                    break
            
            # Hash bayrak belirleme
            if min_eval >= beta_orig:
                hash_bayrak = 'LOWER'
            elif min_eval <= alpha:
                hash_bayrak = 'UPPER'
            else:
                hash_bayrak = 'EXACT'

            if hasattr(tahta, 'zobrist_hash'):
                self.transposition_table.kaydet(tahta.zobrist_hash(), derinlik, min_eval, hash_bayrak, en_iyi_hamle)
            
            return min_eval

    def principal_variation_eval(self, tahta, pv_derinlik, alpha, beta, maksimize_ediyor):
        """
        Principal Variation ile değerlendirme.
        Mevcut pozisyonu, sıradaki oyuncunun en iyi hamlesini yapacağını varsayarak değerlendirir.
        """
        # Önce mevcut pozisyonun statik değerlendirmesini al
        statik_skor = self.degerlendirme.degerlendir(tahta)
        
        # Eğer oyun bitmiş veya hamle yoksa statik skoru döndür
        hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)
        if not hamleler or tahta.mat_mi() or tahta.pat_mi():
            return statik_skor
        
        # Sıradaki oyuncunun en iyi hamlesini bul (1 derinlikte)
        en_iyi_skor = float('-inf') if maksimize_ediyor else float('inf')
        
        # Hamleleri sırala (daha iyi tahmini en iyi hamle için)
        hamleler = self._hamleleri_sirala(tahta, hamleler, None)[:10]  # İlk 10 hamleye bak
        
        for hamle in hamleler:
            tahta_kopyasi = tahta.kopyala()
            tahta_kopyasi.hamle_yap(hamle)
            
            # Bu hamleden sonraki pozisyonun statik değerlendirmesi
            hamle_skoru = self.degerlendirme.degerlendir(tahta_kopyasi)
            
            if maksimize_ediyor:
                en_iyi_skor = max(en_iyi_skor, hamle_skoru)
                if en_iyi_skor >= beta:
                    break
            else:
                en_iyi_skor = min(en_iyi_skor, hamle_skoru)
                if en_iyi_skor <= alpha:
                    break
        
        # En iyi hamle yapıldığında oluşacak skoru döndür
        return en_iyi_skor

    def quiescence_search(self, tahta, alpha, beta, maksimize_ediyor, qs_derinlik=0):
        """Quiescence search - sadece alma hamlelerini değerlendir"""
        self.dugum_sayisi += 1
        
        # QS derinlik limiti (max 4 ply)
        if qs_derinlik > 4:
            return self.degerlendirme.degerlendir(tahta)
        
        stand_pat = self.degerlendirme.degerlendir(tahta)
        
        if maksimize_ediyor:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)
        
        # Sadece alma hamlelerini al
        hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)
        alma_hamleleri = [h for h in hamleler if tahta.tas_turu_al(h[1])]
        
        if not alma_hamleleri:
            return stand_pat
            
        # Alma hamlelerini değerlendir
        for hamle in alma_hamleleri:
            tahta_kopyasi = tahta.kopyala()
            tahta_kopyasi.hamle_yap(hamle)
            
            skor = self.quiescence_search(tahta_kopyasi, alpha, beta, not maksimize_ediyor, qs_derinlik + 1)
            
            if maksimize_ediyor:
                alpha = max(alpha, skor)
                if alpha >= beta:
                    return beta
            else:
                beta = min(beta, skor)
                if beta <= alpha:
                    return alpha
                    
        return alpha if maksimize_ediyor else beta

    def _killer_move_ekle(self, derinlik, hamle):
        """Killer move ekle"""
        if derinlik not in self.killer_moves:
            self.killer_moves[derinlik] = []
        
        # Aynı hamle yoksa ekle
        if hamle not in self.killer_moves[derinlik]:
            self.killer_moves[derinlik].append(hamle)
            # En fazla 2 killer move tut
            if len(self.killer_moves[derinlik]) > 2:
                self.killer_moves[derinlik].pop(0)

    def _history_guncelle(self, hamle, derinlik):
        """History table güncelle"""
        key = (hamle[0], hamle[1])
        bonus = derinlik * derinlik
        
        if key not in self.history_table:
            self.history_table[key] = 0
        
        self.history_table[key] += bonus
        
        # Overflow kontrolü
        if self.history_table[key] > 10000:
            # Tüm değerleri yarıya indir
            for k in self.history_table:
                self.history_table[k] //= 2

    def minimax(self, tahta, derinlik, maksimize_ediyor):
        """Basit MiniMax algoritması (Alpha-Beta olmadan)"""
        self.dugum_sayisi += 1

        # Oyun sonu kontrolü
        if tahta.mat_mi():
            # Mat durumu - mevcut oyuncu için kötü
            if maksimize_ediyor:
                return -self.degerlendirme.mat_skoru(self.derinlik - derinlik)
            else:
                return self.degerlendirme.mat_skoru(self.derinlik - derinlik)
        
        if tahta.pat_mi():
            # Pat durumu - beraberlik
            return 0

        # Terminal düğüm kontrolü
        if derinlik == 0:
            return self.degerlendirme.degerlendir(tahta)

        # Legal hamleleri al
        hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)

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

    def pozisyon_degerlendir_pv(self, tahta):
        """
        GUI için pozisyon değerlendirmesi - Principal Variation mantığıyla.
        Daha tutarlı sonuçlar için kısa bir alpha-beta araması yapar.
        """
        # Oyun sonu kontrolü
        if tahta.mat_mi():
            return -20000 if tahta.beyaz_sira else 20000
        
        if tahta.pat_mi():
            return 0
            
        # Legal hamle kontrolü
        hamleler = self.legal_bulucu.legal_hamleleri_bul(tahta)
        if not hamleler:
            return self.degerlendirme.pozisyon_degerlendir(tahta)
        
        # Kısa bir 2-3 ply alpha-beta araması yap
        arama_derinligi = min(3, self.derinlik)
        
        # PV araması bayrağını aç
        eski_pv_durumu = self._pv_aramasi
        self._pv_aramasi = True
        
        try:
            # Alpha-beta araması
            skor = self.alpha_beta(tahta, arama_derinligi, float('-inf'), float('inf'), tahta.beyaz_sira)
        finally:
            # Bayrağı eski haline döndür
            self._pv_aramasi = eski_pv_durumu
        
        return skor

    def get_istatistikler(self):
        """Arama istatistiklerini döndür"""
        return {
            'dugum_sayisi': self.dugum_sayisi,
            'max_derinlik': self.max_derinlik,
            'derinlik': self.derinlik
        }