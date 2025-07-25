"""
Pygame kullanarak GUI satranç oyunu.
İnsan vs Motor (Beyaz vs Siyah)
"""

import pygame
import sys
from Tahta import Tahta
from Arama import Arama
import threading


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
        self.arama = Arama(derinlik=3)
        self.secili_kare = None
        self.mumkun_hamleler = []
        self.oyun_bitti = False
        self.motor_dusunuyor = False

        # Taş sembolleri (Unicode)
        self.tas_sembolleri = {
            ('beyaz', 'sah'): '♔',
            ('beyaz', 'vezir'): '♕',
            ('beyaz', 'kale'): '♖',
            ('beyaz', 'fil'): '♗',
            ('beyaz', 'at'): '♘',
            ('beyaz', 'piyon'): '♙',
            ('siyah', 'sah'): '♚',
            ('siyah', 'vezir'): '♛',
            ('siyah', 'kale'): '♜',
            ('siyah', 'fil'): '♝',
            ('siyah', 'at'): '♞',
            ('siyah', 'piyon'): '♟'
        }

        # Taş fontu
        self.tas_font = pygame.font.Font(None, 60)

    def kare_koordinati_al(self, mouse_pos):
        """Mouse pozisyonundan kare koordinatını al"""
        x, y = mouse_pos
        if x < self.TAHTA_BOYUTU and y < self.TAHTA_BOYUTU:
            sutun = x // self.KARE_BOYUTU
            satir = y // self.KARE_BOYUTU
            return satir * 8 + sutun
        return None

    def kare_pozisyonu_al(self, kare_indeksi):
        """Kare indeksinden ekran pozisyonunu al"""
        satir = kare_indeksi // 8
        sutun = kare_indeksi % 8
        x = sutun * self.KARE_BOYUTU
        y = satir * self.KARE_BOYUTU
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
                if (renk, tas_turu) in self.tas_sembolleri:
                    sembol = self.tas_sembolleri[(renk, tas_turu)]

                    # Taş rengini ayarla
                    tas_rengi = (255, 255, 255) if renk == 'beyaz' else (0, 0, 0)

                    text = self.tas_font.render(sembol, True, tas_rengi)
                    text_rect = text.get_rect()

                    x, y = self.kare_pozisyonu_al(kare)
                    text_rect.center = (x + self.KARE_BOYUTU // 2, y + self.KARE_BOYUTU // 2)

                    self.ekran.blit(text, text_rect)

    def panel_ciz(self):
        """Sağ paneli çiz"""
        panel_rect = pygame.Rect(self.TAHTA_BOYUTU, 0, self.PANEL_GENISLIGI, self.EKRAN_YUKSEKLIGI)
        pygame.draw.rect(self.ekran, self.PANEL_RENK, panel_rect)

        y_offset = 20

        # Oyun durumu
        sira_text = "Beyaz Sıra" if self.tahta.beyaz_sira else "Siyah Sıra"
        if self.motor_dusunuyor:
            sira_text = "Motor Düşünüyor..."

        text = self.font.render(sira_text, True, self.YAZI_RENK)
        self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
        y_offset += 50

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
        y_offset += 50

        # Kontroller
        controls = [
            "Kontroller:",
            "R - Yeniden Başlat",
            "ESC - Çıkış",
            "1-9 - Derinlik",
            "",
            "Beyaz: İnsan",
            "Siyah: Motor"
        ]

        for control in controls:
            text = self.kucuk_font.render(control, True, self.YAZI_RENK)
            self.ekran.blit(text, (self.TAHTA_BOYUTU + 10, y_offset))
            y_offset += 25

    def kare_secimi_isle(self, kare):
        """Kare seçimini işle"""
        print(f"DEBUG: Kare seçildi: {kare}")
        print(f"DEBUG: Motor düşünüyor mu: {self.motor_dusunuyor}")
        print(f"DEBUG: Oyun bitti mi: {self.oyun_bitti}")
        print(f"DEBUG: Beyaz sıra mı: {self.tahta.beyaz_sira}")

        if self.motor_dusunuyor or self.oyun_bitti:
            print("DEBUG: Motor düşünüyor veya oyun bitti, işlem iptal")
            return

        # Sadece beyaz sırasında insan oynayabilir
        if not self.tahta.beyaz_sira:
            print("DEBUG: Siyah sıra, insan oynayamaz")
            return

        # Eğer seçili kare yoksa
        if self.secili_kare is None:
            tas_info = self.tahta.karedeki_tas(kare)
            print(f"DEBUG: Karedeki taş: {tas_info}")

            if tas_info and tas_info[0] == 'beyaz':  # Sadece beyaz taşları seçilebilir
                self.secili_kare = kare
                self.mumkun_hamleler = self.kare_icin_hamleler_bul(kare)
                print(f"DEBUG: Seçili kare: {kare}, Mümkün hamleler: {len(self.mumkun_hamleler)}")

                # Hamleleri detaylı yazdır
                for i, hamle in enumerate(self.mumkun_hamleler):
                    print(f"DEBUG: Hamle {i}: {hamle}")
            else:
                print("DEBUG: Beyaz taş değil veya boş kare")
        else:
            print(f"DEBUG: Zaten seçili kare var: {self.secili_kare}, hedef: {kare}")

            # Hamle yapmaya çalış
            hamle_yapildi = self.hamle_dene(self.secili_kare, kare)
            print(f"DEBUG: Hamle yapıldı mı: {hamle_yapildi}")

            if hamle_yapildi:
                self.secili_kare = None
                self.mumkun_hamleler = []
                # Motor sırası
                self.motor_hamle_yap()
            else:
                # Yeni kare seç
                tas_info = self.tahta.karedeki_tas(kare)
                if tas_info and tas_info[0] == 'beyaz':
                    self.secili_kare = kare
                    self.mumkun_hamleler = self.kare_icin_hamleler_bul(kare)
                    print(f"DEBUG: Yeni kare seçildi: {kare}, Mümkün hamleler: {len(self.mumkun_hamleler)}")
                else:
                    self.secili_kare = None
                    self.mumkun_hamleler = []
                    print("DEBUG: Seçim iptal edildi")

    def kare_icin_hamleler_bul(self, kaynak_kare):
        """Belirli bir kare için mümkün hamleleri bul"""
        try:
            from HamleUret import HamleUretici
            uretici = HamleUretici()
            tum_hamleler = uretici.tum_hamleleri_uret(self.tahta)
            print(f"DEBUG: Toplam hamle sayısı: {len(tum_hamleler)}")

            # Sadece bu kareden başlayan hamleleri filtrele
            kare_hamleleri = [hamle for hamle in tum_hamleler if hamle[0] == kaynak_kare]
            print(f"DEBUG: Kare {kaynak_kare} için hamle sayısı: {len(kare_hamleleri)}")
            return kare_hamleleri
        except Exception as e:
            print(f"DEBUG: Hamle bulma hatası: {e}")
            return []

    def hamle_dene(self, kaynak, hedef):
        """Hamle yapmaya çalış"""
        print(f"DEBUG: Hamle deneniyor: {kaynak} -> {hedef}")
        print(f"DEBUG: Mevcut hamleler: {self.mumkun_hamleler}")

        for hamle in self.mumkun_hamleler:
            if hamle[0] == kaynak and hamle[1] == hedef:
                print(f"DEBUG: Hamle bulundu: {hamle}")
                try:
                    self.tahta.hamle_yap(hamle)
                    print("DEBUG: Hamle başarıyla yapıldı")
                    return True
                except Exception as e:
                    print(f"DEBUG: Hamle yapma hatası: {e}")
                    return False

        print("DEBUG: Geçersiz hamle")
        return False

    def motor_hamle_yap(self):
        """Motor hamlesi yapılacak (thread'de)"""
        if not self.tahta.beyaz_sira and not self.oyun_bitti:
            self.motor_dusunuyor = True
            print("DEBUG: Motor hamle yapmaya başlıyor...")
            motor_thread = threading.Thread(target=self.motor_hamle_hesapla)
            motor_thread.daemon = True
            motor_thread.start()

    def motor_hamle_hesapla(self):
        """Motor hamlesi hesapla (thread fonksiyonu)"""
        try:
            # Önce normal arama ile dene
            en_iyi_hamle = self.arama.en_iyi_hamle_bul(self.tahta)
            if en_iyi_hamle:
                self.tahta.hamle_yap(en_iyi_hamle)
                print(f"DEBUG: Motor hamle yaptı: {en_iyi_hamle}")
            else:
                print("DEBUG: Motor hamle bulamadı")
        except Exception as e:
            print(f"Motor hamle hatası: {e}")
            print("DEBUG: Rastgele hamle deneniyor...")

        # Eğer normal arama başarısız olursa rastgele hamle yap
        if self.tahta.beyaz_sira:  # Hala siyah sırasıysa hamle yapılmamış demektir
            try:
                from HamleUret import HamleUretici
                uretici = HamleUretici()
                tum_hamleler = uretici.tum_hamleleri_uret(self.tahta)
                print(f"DEBUG: Siyah için {len(tum_hamleler)} hamle bulundu")

                if tum_hamleler:
                    import random
                    rastgele_hamle = random.choice(tum_hamleler)
                    self.tahta.hamle_yap(rastgele_hamle)
                    print(f"DEBUG: Motor rastgele hamle yaptı: {rastgele_hamle}")
                else:
                    print("DEBUG: Hiç hamle bulunamadı!")
            except Exception as e2:
                print(f"Rastgele hamle hatası: {e2}")

        self.motor_dusunuyor = False

    def yeniden_baslat(self):
        """Oyunu yeniden başlat"""
        self.tahta = Tahta()
        self.secili_kare = None
        self.mumkun_hamleler = []
        self.oyun_bitti = False
        self.motor_dusunuyor = False

    def calistir(self):
        """Ana oyun döngüsü"""
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.yeniden_baslat()
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        yeni_derinlik = event.key - pygame.K_0
                        self.arama.derinlik_degistir(yeni_derinlik)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Sol tık
                        kare = self.kare_koordinati_al(event.pos)
                        print(f"DEBUG: Mouse tıklandı, pozisyon: {event.pos}, kare: {kare}")
                        if kare is not None:
                            self.kare_secimi_isle(kare)

            # Ekranı temizle ve çiz
            self.ekran.fill((0, 0, 0))
            self.tahta_ciz()
            self.secili_kare_ciz()
            self.mumkun_hamleleri_ciz()
            self.taslari_ciz()
            self.panel_ciz()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


def main():
    """Ana fonksiyon"""
    try:
        print("DEBUG: Oyun başlatılıyor...")
        oyun = SatrancGUI()
        print("DEBUG: GUI oluşturuldu, oyun döngüsü başlıyor...")
        oyun.calistir()
    except Exception as e:
        print(f"Oyun hatası: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()