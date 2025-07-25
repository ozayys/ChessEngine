"""
Pygame kullanarak GUI satranç oyunu.
İnsan vs Motor (Beyaz vs Siyah)
"""

import pygame
import sys
import os
from Tahta import Tahta
from Arama import Arama
import threading
import time


class SatrancGUI:
    def __init__(self):
        pygame.init()

        # Ekran ayarları
        self.KARE_BOYUTU = 80
        self.TAHTA_BOYUTU = 8 * self.KARE_BOYUTU
        self.PANEL_GENISLIGI = 200
        self.EKRAN_GENISLIGI = self.TAHTA_BOYUTU + self.PANEL_GENISLIGI
        self.EKRAN_YUKSEKLIGI = self.TAHTA_BOYUTU

        # Renkler
        self.BEYAZ_KARE = (240, 217, 181)
        self.SIYAH_KARE = (181, 136, 99)
        self.SECILI_RENK = (255, 255, 0, 128)
        self.HAMLE_RENGI = (0, 255, 0, 128)
        self.PANEL_RENK = (50, 50, 50)
        self.YAZI_RENK = (255, 255, 255)

        self.ekran = pygame.display.set_mode((self.EKRAN_GENISLIGI, self.EKRAN_YUKSEKLIGI))
        pygame.display.set_caption("Satranç - İnsan vs Motor")

        # Font
        self.font = pygame.font.Font(None, 36)
        self.kucuk_font = pygame.font.Font(None, 24)

        # Oyun durumu
        self.tahta = Tahta()
        self.arama = Arama(derinlik=4)
        self.secili_kare = None
        self.mumkun_hamleler = []
        self.oyun_bitti = False
        self.motor_dusunuyor = False
        
        # Piyon terfisi
        self.terfi_bekliyor = False
        self.terfi_kare = None
        self.terfi_hamle = None
        self.terfi_secenekleri = ['vezir', 'kale', 'fil', 'at']
        
        # Terfi menüsü animasyon ve hover efektleri
        self.terfi_menu_alpha = 0
        self.terfi_menu_animasyon = False
        self.hover_tas = None
        self.hover_scale = {}
        for tas in self.terfi_secenekleri:
            self.hover_scale[tas] = 1.0
        
        # Değerlendirme bilgileri
        self.son_degerlendirme = 0
        self.dugum_sayisi = 0
        self.son_hamle = None

        # Taş resimlerini yükle
        self.tas_resimleri = {}
        self._tas_resimlerini_yukle()

    def _tas_resimlerini_yukle(self):
        """Taş resimlerini yükle ve boyutlandır"""
        tas_dosyalari = {
            ('beyaz', 'sah'): 'beyazSah.png',
            ('beyaz', 'vezir'): 'beyazVezir.png', 
            ('beyaz', 'kale'): 'beyazKale.png',
            ('beyaz', 'fil'): 'beyazFil.png',
            ('beyaz', 'at'): 'beyazAt.png',
            ('beyaz', 'piyon'): 'beyazPiyon.png',
            ('siyah', 'sah'): 'siyahSah.png',
            ('siyah', 'vezir'): 'siyahVezir.png',
            ('siyah', 'kale'): 'siyahKale.png', 
            ('siyah', 'fil'): 'siyahFil.png',
            ('siyah', 'at'): 'siyahAt.png',
            ('siyah', 'piyon'): 'siyahPiyon.png'
        }

        for (renk, tas_turu), dosya_adi in tas_dosyalari.items():
            try:
                dosya_yolu = os.path.join('taslar', dosya_adi)
                if os.path.exists(dosya_yolu):
                    resim = pygame.image.load(dosya_yolu)
                    # Taş resmini kare boyutuna göre ölçekle
                    resim = pygame.transform.scale(resim, (self.KARE_BOYUTU - 10, self.KARE_BOYUTU - 10))
                    self.tas_resimleri[(renk, tas_turu)] = resim
                    print(f"✓ {dosya_adi} başarıyla yüklendi")
                else:
                    print(f"✗ {dosya_yolu} bulunamadı")
            except Exception as e:
                print(f"✗ {dosya_adi} yüklenirken hata: {e}")

        print(f"Toplam {len(self.tas_resimleri)} taş resmi yüklendi")

    def kare_koordinati_al(self, mouse_pos):
        """Mouse pozisyonundan kare koordinatını al"""
        x, y = mouse_pos
        if x < self.TAHTA_BOYUTU and y < self.TAHTA_BOYUTU:
            sutun = x // self.KARE_BOYUTU
            satir = 7 - (y // self.KARE_BOYUTU)  # Tahtayı ters çevir
            return satir * 8 + sutun
        return None

    def kare_pozisyonu_al(self, kare_indeksi):
        """Kare indeksinden ekran pozisyonunu al"""
        satir = kare_indeksi // 8
        sutun = kare_indeksi % 8
        x = sutun * self.KARE_BOYUTU
        y = (7 - satir) * self.KARE_BOYUTU  # Tahtayı ters çevir
        return x, y

    def tahta_ciz(self):
        """Satranç tahtasını çiz"""
        for satir in range(8):
            for sutun in range(8):
                x = sutun * self.KARE_BOYUTU
                y = satir * self.KARE_BOYUTU

                # Kare rengi
                if (satir + sutun) % 2 == 0:
                    renk = self.BEYAZ_KARE
                else:
                    renk = self.SIYAH_KARE

                pygame.draw.rect(self.ekran, renk,
                                 (x, y, self.KARE_BOYUTU, self.KARE_BOYUTU))

    def secili_kare_ciz(self):
        """Seçili kareyi vurgula"""
        if self.secili_kare is not None:
            x, y = self.kare_pozisyonu_al(self.secili_kare)
            overlay = pygame.Surface((self.KARE_BOYUTU, self.KARE_BOYUTU))
            overlay.set_alpha(128)
            overlay.fill((255, 255, 0))
            self.ekran.blit(overlay, (x, y))

    def mumkun_hamleleri_ciz(self):
        """Mümkün hamleleri göster"""
        for hamle in self.mumkun_hamleler:
            hedef_kare = hamle[1]
            x, y = self.kare_pozisyonu_al(hedef_kare)
            overlay = pygame.Surface((self.KARE_BOYUTU, self.KARE_BOYUTU))
            overlay.set_alpha(100)
            overlay.fill((0, 255, 0))
            self.ekran.blit(overlay, (x, y))

            # Küçük daire çiz
            merkez_x = x + self.KARE_BOYUTU // 2
            merkez_y = y + self.KARE_BOYUTU // 2
            pygame.draw.circle(self.ekran, (0, 150, 0), (merkez_x, merkez_y), 10)

    def taslari_ciz(self):
        """Taşları tahta üzerine çiz"""
        for kare in range(64):
            tas_info = self.tahta.karedeki_tas(kare)
            if tas_info:
                renk, tas_turu = tas_info
                if (renk, tas_turu) in self.tas_resimleri:
                    # Resim varsa resmi kullan
                    resim = self.tas_resimleri[(renk, tas_turu)]
                    x, y = self.kare_pozisyonu_al(kare)
                    # Resmi ortala
                    resim_rect = resim.get_rect()
                    resim_rect.center = (x + self.KARE_BOYUTU // 2, y + self.KARE_BOYUTU // 2)
                    self.ekran.blit(resim, resim_rect)
                else:
                    # Resim yoksa Unicode sembol kullan (backup)
                    self._unicode_tas_ciz(kare, renk, tas_turu)

    def _unicode_tas_ciz(self, kare, renk, tas_turu):
        """Unicode semboller ile taş çiz (backup)"""
        tas_sembolleri = {
            ('beyaz', 'sah'): '♔', ('beyaz', 'vezir'): '♕', ('beyaz', 'kale'): '♖',
            ('beyaz', 'fil'): '♗', ('beyaz', 'at'): '♘', ('beyaz', 'piyon'): '♙',
            ('siyah', 'sah'): '♚', ('siyah', 'vezir'): '♛', ('siyah', 'kale'): '♜',
            ('siyah', 'fil'): '♝', ('siyah', 'at'): '♞', ('siyah', 'piyon'): '♟'
        }
        
        if (renk, tas_turu) in tas_sembolleri:
            sembol = tas_sembolleri[(renk, tas_turu)]
            tas_rengi = (255, 255, 255) if renk == 'beyaz' else (0, 0, 0)
            
            # Font oluştur (eğer yoksa)
            if not hasattr(self, 'tas_font'):
                self.tas_font = pygame.font.Font(None, 60)
            
            text = self.tas_font.render(sembol, True, tas_rengi)
            text_rect = text.get_rect()
            x, y = self.kare_pozisyonu_al(kare)
            text_rect.center = (x + self.KARE_BOYUTU // 2, y + self.KARE_BOYUTU // 2)
            self.ekran.blit(text, text_rect)

    def _kare_notasyonu(self, kare_indeksi):
        """Kare indeksini satranç notasyonuna çevir (örn: 0 -> a1)"""
        satir = kare_indeksi // 8
        sutun = kare_indeksi % 8
        return chr(ord('a') + sutun) + str(satir + 1)

    def terfi_menusu_ciz(self):
        """Piyon terfisi menüsünü çiz"""
        if not self.terfi_bekliyor:
            return
        
        # Terfi olan piyonu vurgula
        if self.terfi_kare is not None:
            satir = self.terfi_kare // 8
            sutun = self.terfi_kare % 8
            x = sutun * self.KARE_BOYUTU
            y = satir * self.KARE_BOYUTU
            
            # Parlayan efekt için animasyon
            pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500.0
            highlight_alpha = int(100 + 100 * pulse)
            
            highlight_surface = pygame.Surface((self.KARE_BOYUTU, self.KARE_BOYUTU))
            highlight_surface.set_alpha(highlight_alpha)
            highlight_surface.fill((255, 215, 0))  # Altın rengi
            self.ekran.blit(highlight_surface, (x, y))
            
            # Çerçeve
            pygame.draw.rect(self.ekran, (255, 215, 0), 
                           pygame.Rect(x, y, self.KARE_BOYUTU, self.KARE_BOYUTU), 3)
        
        # Animasyon güncelle
        if self.terfi_menu_animasyon:
            if self.terfi_menu_alpha < 255:
                self.terfi_menu_alpha = min(255, self.terfi_menu_alpha + 15)
        
        # Yarı saydam arka plan (animasyonlu)
        overlay = pygame.Surface((self.EKRAN_GENISLIGI, self.EKRAN_YUKSEKLIGI))
        overlay.set_alpha(min(200, self.terfi_menu_alpha))
        overlay.fill((0, 0, 0))
        self.ekran.blit(overlay, (0, 0))
        
        # Menü arka planı - daha geniş ve modern
        menu_genislik = 400
        menu_yukseklik = 140
        menu_x = (self.TAHTA_BOYUTU - menu_genislik) // 2
        menu_y = (self.TAHTA_BOYUTU - menu_yukseklik) // 2
        
        # Gölge efekti
        golge_rect = pygame.Rect(menu_x + 5, menu_y + 5, menu_genislik, menu_yukseklik)
        golge_surface = pygame.Surface((menu_genislik, menu_yukseklik))
        golge_surface.set_alpha(100)
        golge_surface.fill((0, 0, 0))
        self.ekran.blit(golge_surface, (menu_x + 5, menu_y + 5))
        
        # Ana menü arka planı (gradient efekti simülasyonu)
        menu_rect = pygame.Rect(menu_x, menu_y, menu_genislik, menu_yukseklik)
        pygame.draw.rect(self.ekran, (40, 40, 45), menu_rect, border_radius=15)
        pygame.draw.rect(self.ekran, (70, 70, 75), menu_rect, 3, border_radius=15)
        
        # İç çerçeve (ışık efekti)
        ic_rect = pygame.Rect(menu_x + 5, menu_y + 5, menu_genislik - 10, menu_yukseklik - 10)
        pygame.draw.rect(self.ekran, (60, 60, 65), ic_rect, 1, border_radius=12)
        
        # Başlık - daha büyük ve gösterişli
        baslik_font = pygame.font.Font(None, 42)
        baslik_text = baslik_font.render("Piyon Terfisi", True, (255, 255, 255))
        baslik_rect = baslik_text.get_rect(center=(menu_x + menu_genislik // 2, menu_y - 35))
        
        # Başlık gölgesi
        baslik_golge = baslik_font.render("Piyon Terfisi", True, (50, 50, 50))
        golge_rect = baslik_golge.get_rect(center=(menu_x + menu_genislik // 2 + 2, menu_y - 33))
        self.ekran.blit(baslik_golge, golge_rect)
        self.ekran.blit(baslik_text, baslik_rect)
        
        # Alt başlık
        alt_baslik_font = pygame.font.Font(None, 20)
        alt_baslik_text = alt_baslik_font.render("Bir taş seçin", True, (180, 180, 180))
        alt_baslik_rect = alt_baslik_text.get_rect(center=(menu_x + menu_genislik // 2, menu_y - 10))
        self.ekran.blit(alt_baslik_text, alt_baslik_rect)
        
        # Klavye kısayolları bilgisi
        kisayol_font = pygame.font.Font(None, 16)
        kisayol_text = kisayol_font.render("Q-Vezir  R-Kale  B-Fil  N-At  (veya 1-2-3-4)", True, (150, 150, 150))
        kisayol_rect = kisayol_text.get_rect(center=(menu_x + menu_genislik // 2, menu_y + menu_yukseklik + 20))
        self.ekran.blit(kisayol_text, kisayol_rect)
        
        # Taş seçenekleri
        tas_boyut = 80
        tas_aralik = 15
        toplam_genislik = 4 * tas_boyut + 3 * tas_aralik
        baslangic_x = menu_x + (menu_genislik - toplam_genislik) // 2
        
        renk = 'beyaz' if self.tahta.beyaz_sira else 'siyah'
        mouse_pos = pygame.mouse.get_pos()
        
        for i, tas_turu in enumerate(self.terfi_secenekleri):
            x = baslangic_x + i * (tas_boyut + tas_aralik)
            y = menu_y + 30
            
            # Hover efekti için scale güncelle
            secenek_rect = pygame.Rect(x, y, tas_boyut, tas_boyut)
            if secenek_rect.collidepoint(mouse_pos):
                if self.hover_scale[tas_turu] < 1.15:
                    self.hover_scale[tas_turu] = min(1.15, self.hover_scale[tas_turu] + 0.05)
                self.hover_tas = tas_turu
            else:
                if self.hover_scale[tas_turu] > 1.0:
                    self.hover_scale[tas_turu] = max(1.0, self.hover_scale[tas_turu] - 0.05)
            
            # Seçenek kutusu - hover ile değişen renk
            scale = self.hover_scale[tas_turu]
            boyut = int(tas_boyut * scale)
            x_offset = (boyut - tas_boyut) // 2
            y_offset = (boyut - tas_boyut) // 2
            
            kutucuk_rect = pygame.Rect(x - x_offset, y - y_offset, boyut, boyut)
            
            # Arka plan rengi (hover'da parlak)
            if self.hover_tas == tas_turu and kutucuk_rect.collidepoint(mouse_pos):
                bg_color = (80, 80, 90)
                border_color = (255, 215, 0)  # Altın rengi
                border_width = 4
            else:
                bg_color = (60, 60, 65)
                border_color = (150, 150, 150)
                border_width = 2
            
            # Kutucuk çiz
            pygame.draw.rect(self.ekran, bg_color, kutucuk_rect, border_radius=10)
            pygame.draw.rect(self.ekran, border_color, kutucuk_rect, border_width, border_radius=10)
            
            # İç ışık efekti
            ic_kutucuk = pygame.Rect(kutucuk_rect.x + 3, kutucuk_rect.y + 3, 
                                    kutucuk_rect.width - 6, kutucuk_rect.height - 6)
            pygame.draw.rect(self.ekran, (90, 90, 95), ic_kutucuk, 1, border_radius=8)
            
            # Taş resmi
            if (renk, tas_turu) in self.tas_resimleri:
                resim = self.tas_resimleri[(renk, tas_turu)]
                # Hover'da büyüt
                resim_boyut = int((boyut - 20) * 0.9)
                resim = pygame.transform.scale(resim, (resim_boyut, resim_boyut))
                resim_rect = resim.get_rect(center=kutucuk_rect.center)
                self.ekran.blit(resim, resim_rect)
            
            # Taş ismi ve kısayol (hover'da göster)
            if self.hover_tas == tas_turu and kutucuk_rect.collidepoint(mouse_pos):
                isim_font = pygame.font.Font(None, 18)
                kisayol_map = {'vezir': 'Q/1', 'kale': 'R/2', 'fil': 'B/3', 'at': 'N/4'}
                isim_text = isim_font.render(f"{tas_turu.capitalize()} ({kisayol_map[tas_turu]})", True, (255, 255, 255))
                isim_rect = isim_text.get_rect(center=(kutucuk_rect.centerx, kutucuk_rect.bottom + 15))
                self.ekran.blit(isim_text, isim_rect)
            
            # Küçük kısayol göstergesi
            else:
                kisayol_font = pygame.font.Font(None, 14)
                kisayol_map = {'vezir': '1', 'kale': '2', 'fil': '3', 'at': '4'}
                kisayol_text = kisayol_font.render(kisayol_map[tas_turu], True, (120, 120, 120))
                kisayol_rect = kisayol_text.get_rect(center=(kutucuk_rect.centerx, kutucuk_rect.bottom + 8))
                self.ekran.blit(kisayol_text, kisayol_rect)
            
            # Hover efekti için rect'i sakla
            setattr(self, f'terfi_{tas_turu}_rect', secenek_rect)

    def terfi_menusu_tikla(self, mouse_pos):
        """Terfi menüsünde tıklama kontrolü"""
        if not self.terfi_bekliyor:
            return None
        
        for tas_turu in self.terfi_secenekleri:
            rect = getattr(self, f'terfi_{tas_turu}_rect', None)
            if rect and rect.collidepoint(mouse_pos):
                return tas_turu
        
        return None
    
    def terfi_klavye_secimi(self, key):
        """Klavye ile terfi seçimi"""
        if not self.terfi_bekliyor:
            return None
        
        # Q: Vezir, R: Kale, B: Fil, N: At
        klavye_map = {
            pygame.K_q: 'vezir',
            pygame.K_r: 'kale',
            pygame.K_b: 'fil',
            pygame.K_n: 'at',
            pygame.K_1: 'vezir',
            pygame.K_2: 'kale',
            pygame.K_3: 'fil',
            pygame.K_4: 'at'
        }
        
        return klavye_map.get(key, None)

    def panel_ciz(self):
        """Sağ paneli çiz"""
        panel_rect = pygame.Rect(self.TAHTA_BOYUTU, 0, self.PANEL_GENISLIGI, self.EKRAN_YUKSEKLIGI)
        pygame.draw.rect(self.ekran, self.PANEL_RENK, panel_rect)

        y_offset = 20

        # Oyun durumu
        oyun_durumu, kazanan = self.tahta.oyun_sonu_durumu()
        
        if oyun_durumu == 'mat':
            durum_text = f"MAT! {kazanan.capitalize()} Kazandı"
            renk = (255, 0, 0)  # Kırmızı
            font = self.font
        elif oyun_durumu == 'pat':
            durum_text = "PAT! Berabere"
            renk = (255, 255, 0)  # Sarı
            font = self.font
        else:
            sira_text = "Beyaz Sıra" if self.tahta.beyaz_sira else "Siyah Sıra"
            if self.motor_dusunuyor:
                sira_text = "Motor Düşünüyor..."
            durum_text = sira_text
            renk = self.YAZI_RENK
            font = self.font

        text = font.render(durum_text, True, renk)
        self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
        y_offset += 50

        # Şah kontrolü
        if not oyun_durumu:  # Oyun devam ediyorsa
            renk = 'beyaz' if self.tahta.beyaz_sira else 'siyah'
            if self.tahta.sah_tehdit_altinda_mi(renk):
                sah_text = "ŞAH!"
                text = self.font.render(sah_text, True, (255, 100, 100))
                self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
                y_offset += 40

        # Arama derinliği
        derinlik_text = f"Derinlik: {self.arama.derinlik}"
        text = self.kucuk_font.render(derinlik_text, True, self.YAZI_RENK)
        self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
        y_offset += 30

        # Hamle sayısı
        hamle_sayisi = self.tahta.hamle_sayisi if hasattr(self.tahta, 'hamle_sayisi') else 0
        hamle_text = f"Hamle: {hamle_sayisi}"
        text = self.kucuk_font.render(hamle_text, True, self.YAZI_RENK)
        self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
        y_offset += 30

        # Değerlendirme skoru
        degerlendirme_text = f"Skor: {self.son_degerlendirme:+.1f}"
        if self.son_degerlendirme > 0:
            renk = (150, 255, 150)  # Açık yeşil - beyaz iyi
        elif self.son_degerlendirme < 0:
            renk = (255, 150, 150)  # Açık kırmızı - siyah iyi  
        else:
            renk = self.YAZI_RENK
        text = self.kucuk_font.render(degerlendirme_text, True, renk)
        self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
        y_offset += 25

        # Düğüm sayısı
        dugum_text = f"Düğüm: {self.dugum_sayisi}"
        text = self.kucuk_font.render(dugum_text, True, self.YAZI_RENK)
        self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
        y_offset += 25

        # Son hamle
        if self.son_hamle:
            # Hamleyi insan okunabilir formatta göster
            kaynak_str = self._kare_notasyonu(self.son_hamle[0])
            hedef_str = self._kare_notasyonu(self.son_hamle[1])
            hamle_str = f"Son: {kaynak_str}-{hedef_str}"
            text = self.kucuk_font.render(hamle_str, True, self.YAZI_RENK)
            self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
            y_offset += 30

        # Kontroller
        controls = [
            "R - Yeniden Başlat",
            "ESC - Çıkış",
            "Beyaz: İnsan",
            "Siyah: Motor"
        ]

        for control in controls:
            text = self.kucuk_font.render(control, True, self.YAZI_RENK)
            self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
            y_offset += 25

    def kare_secimi_isle(self, kare):
        """Kare seçimini işle"""
        if self.motor_dusunuyor or self.terfi_bekliyor:
            return

        # Oyun bitti mi kontrol et
        if self.tahta.oyun_bitti_mi():
            self.oyun_bitti = True
            return

        # Sadece beyaz sırasında insan oynayabilir
        if not self.tahta.beyaz_sira:
            return

        # Eğer seçili kare yoksa
        if self.secili_kare is None:
            tas_info = self.tahta.karedeki_tas(kare)

            if tas_info and tas_info[0] == 'beyaz':  # Sadece beyaz taşları seçilebilir
                self.secili_kare = kare
                # Legal hamleleri bul
                from LegalHamle import LegalHamleBulucu
                legal_bulucu = LegalHamleBulucu()
                tum_legal_hamleler = legal_bulucu.legal_hamleleri_bul(self.tahta)
                self.mumkun_hamleler = [hamle for hamle in tum_legal_hamleler if hamle[0] == kare]
        else:
            # Hamle yapmaya çalış
            hamle_yapildi = self.hamle_dene(self.secili_kare, kare)

            if hamle_yapildi:
                self.secili_kare = None
                self.mumkun_hamleler = []
                
                # Oyun bitti mi kontrol et
                if self.tahta.oyun_bitti_mi():
                    self.oyun_bitti = True
                    return
                
                # Motor sırası başlat - sadece siyah sırasıysa
                if not self.tahta.beyaz_sira:
                    pygame.time.set_timer(pygame.USEREVENT + 1, 500)  # 500ms sonra motor hamlesini başlat
            else:
                # Yeni kare seç
                tas_info = self.tahta.karedeki_tas(kare)
                if tas_info and tas_info[0] == 'beyaz':
                    self.secili_kare = kare
                    # Legal hamleleri bul
                    from LegalHamle import LegalHamleBulucu
                    legal_bulucu = LegalHamleBulucu()
                    tum_legal_hamleler = legal_bulucu.legal_hamleleri_bul(self.tahta)
                    self.mumkun_hamleler = [hamle for hamle in tum_legal_hamleler if hamle[0] == kare]
                else:
                    self.secili_kare = None
                    self.mumkun_hamleler = []

    def kare_icin_hamleler_bul(self, kaynak_kare):
        """Belirli bir kare için mümkün hamleleri bul"""
        try:
            from LegalHamle import LegalHamleBulucu
            legal_bulucu = LegalHamleBulucu()
            tum_hamleler = legal_bulucu.legal_hamleleri_bul(self.tahta)

            # Sadece bu kareden başlayan hamleleri filtrele
            kare_hamleleri = [hamle for hamle in tum_hamleler if hamle[0] == kaynak_kare]
            return kare_hamleleri
        except Exception as e:
            return []

    def hamle_dene(self, kaynak, hedef):
        """Hamle yapmaya çalış"""
        for hamle in self.mumkun_hamleler:
            if hamle[0] == kaynak and hamle[1] == hedef:
                # Piyon terfisi kontrolü
                if len(hamle) > 3 and hamle[3] in ['terfi', 'terfi_alma']:
                    # Terfi menüsünü göster
                    self.terfi_bekliyor = True
                    self.terfi_kare = hedef
                    self.terfi_hamle = hamle
                    self.terfi_menu_animasyon = True
                    self.terfi_menu_alpha = 0
                    return False  # Henüz hamle yapma, terfi seçimi bekle
                
                try:
                    if self.tahta.hamle_yap(hamle):
                        self.son_hamle = hamle
                        
                        # Pozisyonu değerlendir (beyaz perspektifinden)
                        from Degerlendirme import Degerlendirici
                        degerlendirici = Degerlendirici()
                        # Değerlendirmeyi beyaz perspektifinden al (pozitif = beyaz iyi, negatif = siyah iyi)
                        raw_skor = degerlendirici.pozisyon_degerlendir(self.tahta)
                        self.son_degerlendirme = raw_skor / 100.0
                        
                        return True
                    return False
                except Exception as e:
                    return False
        return False

    def terfi_hamlesini_yap(self, terfi_tasi):
        """Terfi hamlesini seçilen taş ile yap"""
        if not self.terfi_bekliyor or not self.terfi_hamle:
            return False
        
        # Terfi hamlesini güncelle
        hamle = list(self.terfi_hamle)
        if len(hamle) > 4:
            hamle[4] = terfi_tasi
        else:
            hamle.append(terfi_tasi)
        
        try:
            if self.tahta.hamle_yap(hamle):
                self.son_hamle = hamle
                
                # Pozisyonu değerlendir
                from Degerlendirme import Degerlendirici
                degerlendirici = Degerlendirici()
                raw_skor = degerlendirici.pozisyon_degerlendir(self.tahta)
                self.son_degerlendirme = raw_skor / 100.0
                
                # Terfi durumunu sıfırla
                self.terfi_bekliyor = False
                self.terfi_kare = None
                self.terfi_hamle = None
                self.terfi_menu_animasyon = False
                self.terfi_menu_alpha = 0
                self.hover_tas = None
                for tas in self.terfi_secenekleri:
                    self.hover_scale[tas] = 1.0
                
                return True
        except Exception as e:
            print(f"Terfi hamlesi hatası: {e}")
        
        return False

    def motor_hamle_yap(self):
        """Motor hamlesi yapılacak (thread'de)"""
        if not self.tahta.beyaz_sira and not self.oyun_bitti and not self.motor_dusunuyor:
            self.motor_dusunuyor = True
            motor_thread = threading.Thread(target=self.motor_hamle_hesapla)
            motor_thread.daemon = True
            motor_thread.start()

    def motor_hamle_hesapla(self):
        """Motor hamlesi hesapla (thread fonksiyonu)"""
        try:
            # Önce mevcut hamleleri kontrol et
            from LegalHamle import LegalHamleBulucu
            legal_bulucu = LegalHamleBulucu()
            mevcut_hamleler = legal_bulucu.legal_hamleleri_bul(self.tahta)

            if not mevcut_hamleler:
                print("Motor için hamle bulunamadı!")
                # Oyun bitti kontrolü
                if self.tahta.mat_mi():
                    self.oyun_bitti = True
                    print("Mat! Beyaz kazandı.")
                elif self.tahta.pat_mi():
                    self.oyun_bitti = True
                    print("Pat! Berabere.")
                return

            # Zaman limiti ile arama yap (3 saniye)
            baslangic_zamani = time.time()
            en_iyi_hamle = self.arama.en_iyi_hamle_bul(self.tahta, zaman_limiti=3.0)
            
            # Arama süresi
            gecen_sure = time.time() - baslangic_zamani
            
            if en_iyi_hamle and en_iyi_hamle in mevcut_hamleler:
                # Hamleyi yap
                if self.tahta.hamle_yap(en_iyi_hamle):
                    # Hamle notasyonu oluştur
                    hamle_str = self._hamle_notasyonu_olustur(en_iyi_hamle)
                    
                    # Arama istatistiklerini güncelle
                    istatistikler = self.arama.get_istatistikler()
                    self.dugum_sayisi = istatistikler['dugum_sayisi']
                    
                    print(f"Motor hamle yaptı: {hamle_str}")
                    print(f"Düşünme süresi: {gecen_sure:.2f}s, Değerlendirilen pozisyon: {self.dugum_sayisi:,}")
                    
                    # Transposition table istatistikleri
                    if hasattr(self.arama.transposition_table, 'hit'):
                        tt_hit_rate = self.arama.transposition_table.hit / max(1, self.arama.transposition_table.hit + self.arama.transposition_table.miss) * 100
                        print(f"TT Hit Rate: {tt_hit_rate:.1f}%")
                    
                    self.son_hamle = en_iyi_hamle
                    
                    # Pozisyonu değerlendir (beyaz perspektifinden)
                    from Degerlendirme import Degerlendirici
                    degerlendirici = Degerlendirici()
                    # Değerlendirmeyi beyaz perspektifinden al (pozitif = beyaz iyi, negatif = siyah iyi)
                    raw_skor = degerlendirici.pozisyon_degerlendir(self.tahta)
                    self.son_degerlendirme = raw_skor / 100.0  # Centipawn'dan pawn'a çevir
                    
                    # Oyun bitti mi kontrol et
                    if self.tahta.oyun_bitti_mi():
                        self.oyun_bitti = True
                        if self.tahta.mat_mi():
                            print("Mat! Siyah kazandı.")
                        elif self.tahta.pat_mi():
                            print("Pat! Berabere.")
                else:
                    print("Motor hamle yapamadı!")
            else:
                # Güvenlik: Legal hamle bulunamadıysa ilk legal hamleyi yap
                print("Uyarı: Motor legal hamle bulamadı, ilk legal hamle yapılıyor.")
                ilk_hamle = mevcut_hamleler[0]
                if self.tahta.hamle_yap(ilk_hamle):
                    self.son_hamle = ilk_hamle
                    self.son_degerlendirme = 0
                    
                    # Oyun bitti mi kontrol et
                    if self.tahta.oyun_bitti_mi():
                        self.oyun_bitti = True

        except Exception as e:
            print(f"Motor hamle hatası: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.motor_dusunuyor = False
    
    def _hamle_notasyonu_olustur(self, hamle):
        """Hamle için satranç notasyonu oluştur"""
        kaynak, hedef = hamle[0], hamle[1]
        
        # Kare indekslerini satranç notasyonuna çevir
        kaynak_str = self.kare_notasyonu(kaynak)
        hedef_str = self.kare_notasyonu(hedef)
        
        # Basit notasyon
        return f"{kaynak_str}-{hedef_str}"

    def yeniden_baslat(self):
        """Oyunu yeniden başlat"""
        self.tahta = Tahta()
        self.secili_kare = None
        self.mumkun_hamleler = []
        self.oyun_bitti = False
        self.motor_dusunuyor = False
        
        # Piyon terfisi durumunu sıfırla
        self.terfi_bekliyor = False
        self.terfi_kare = None
        self.terfi_hamle = None
        self.terfi_menu_animasyon = False
        self.terfi_menu_alpha = 0
        self.hover_tas = None
        for tas in self.terfi_secenekleri:
            self.hover_scale[tas] = 1.0
        
        # Değerlendirme bilgilerini sıfırla
        self.son_degerlendirme = 0
        self.dugum_sayisi = 0
        self.son_hamle = None
        
        pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Timer'ı iptal et

    def calistir(self):
        """Ana oyun döngüsü"""
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.USEREVENT + 1:
                    # Motor hamle timer'ı
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Timer'ı iptal et
                    self.motor_hamle_yap()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and not self.terfi_bekliyor:
                        self.yeniden_baslat()
                    elif self.terfi_bekliyor:
                        # Terfi seçimi için klavye kısayolları
                        terfi_secimi = self.terfi_klavye_secimi(event.key)
                        if terfi_secimi:
                            if self.terfi_hamlesini_yap(terfi_secimi):
                                self.secili_kare = None
                                self.mumkun_hamleler = []
                                
                                # Oyun bitti mi kontrol et
                                if self.tahta.oyun_bitti_mi():
                                    self.oyun_bitti = True
                                    continue
                                
                                # Motor sırası başlat
                                if not self.tahta.beyaz_sira:
                                    pygame.time.set_timer(pygame.USEREVENT + 1, 500)
                    elif pygame.K_1 <= event.key <= pygame.K_9 and not self.terfi_bekliyor:
                        yeni_derinlik = event.key - pygame.K_0
                        self.arama.derinlik_degistir(yeni_derinlik)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Sol tık
                        # Terfi menüsü açıksa önce onu kontrol et
                        if self.terfi_bekliyor:
                            terfi_secimi = self.terfi_menusu_tikla(event.pos)
                            if terfi_secimi:
                                if self.terfi_hamlesini_yap(terfi_secimi):
                                    self.secili_kare = None
                                    self.mumkun_hamleler = []
                                    
                                    # Oyun bitti mi kontrol et
                                    if self.tahta.oyun_bitti_mi():
                                        self.oyun_bitti = True
                                        continue
                                    
                                    # Motor sırası başlat
                                    if not self.tahta.beyaz_sira:
                                        pygame.time.set_timer(pygame.USEREVENT + 1, 500)
                        else:
                            # Normal kare seçimi
                            kare = self.kare_koordinati_al(event.pos)
                            if kare is not None:
                                self.kare_secimi_isle(kare)

            # Ekranı temizle ve çiz
            self.ekran.fill((0, 0, 0))
            self.tahta_ciz()
            self.secili_kare_ciz()
            self.mumkun_hamleleri_ciz()
            self.taslari_ciz()
            self.panel_ciz()
            
            # Terfi menüsü varsa onu da çiz
            self.terfi_menusu_ciz()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


def main():
    """Ana fonksiyon"""
    try:
        oyun = SatrancGUI()
        oyun.calistir()
    except Exception as e:
        print(f"Oyun hatası: {e}")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()