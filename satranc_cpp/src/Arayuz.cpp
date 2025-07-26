#include "Arayuz.h"
#include "Oyun.h"
#include "Tahta.h"
#include <iostream>

// Yapıcı
Arayuz::Arayuz() 
    : seciliKare(-1), hamleAnimasyonu(false), suruklemeAktif(false),
      suruklenenKare(-1), terfiSecimAktif(false), terfiKaynak(-1),
      terfiHedef(-1), motorDerinlik(0), motorSkor(0), motorDugumSayisi(0),
      oyun(nullptr) {
    
    // Renkleri ayarla
    renkleriAyarla();
}

// Yıkıcı
Arayuz::~Arayuz() {
    if (pencere.isOpen()) {
        pencere.close();
    }
}

// Başlat
bool Arayuz::baslat() {
    // Pencere oluştur
    pencere.create(sf::VideoMode(PENCERE_GENISLIGI, PENCERE_YUKSEKLIGI), 
                   "Satranç Motoru - C++ / SFML",
                   sf::Style::Titlebar | sf::Style::Close);
    
    // View'ları ayarla
    tahtaGorunumu.reset(sf::FloatRect(0, 0, TAHTA_BOYUTU, TAHTA_BOYUTU));
    tahtaGorunumu.setViewport(sf::FloatRect(0, 0, 
        (float)TAHTA_BOYUTU / PENCERE_GENISLIGI, 1));
    
    panelGorunumu.reset(sf::FloatRect(0, 0, PANEL_GENISLIGI, PENCERE_YUKSEKLIGI));
    panelGorunumu.setViewport(sf::FloatRect(
        (float)TAHTA_BOYUTU / PENCERE_GENISLIGI, 0,
        (float)PANEL_GENISLIGI / PENCERE_GENISLIGI, 1));
    
    // Fontları yükle
    if (!fontlariYukle()) {
        std::cerr << "Fontlar yüklenemedi!\n";
        return false;
    }
    
    // Taş görsellerini yükle
    if (!tasGorselleriniYukle()) {
        std::cerr << "Taş görselleri yüklenemedi!\n";
        // Görsel olmadan da çalışabilir
    }
    
    return true;
}

// Ana döngü
void Arayuz::calistir() {
    if (!pencere.isOpen() || !oyun) return;
    
    while (pencere.isOpen()) {
        olaylariIsle();
        guncelle();
        ciz();
    }
}

// Olayları işle
void Arayuz::olaylariIsle() {
    sf::Event olay;
    while (pencere.pollEvent(olay)) {
        switch (olay.type) {
            case sf::Event::Closed:
                pencere.close();
                break;
                
            case sf::Event::MouseButtonPressed:
                fareTiklamisiniIsle(olay);
                break;
                
            case sf::Event::MouseButtonReleased:
                fareBirakmaIsle(olay);
                break;
                
            case sf::Event::MouseMoved:
                fareHareketiniIsle(olay);
                break;
                
            case sf::Event::KeyPressed:
                klavyeGirdisiniIsle(olay);
                break;
                
            default:
                break;
        }
    }
}

// Güncelle
void Arayuz::guncelle() {
    if (!oyun) return;
    
    // Motor hamlesi hazır mı?
    if (oyun->motorHazirMi()) {
        oyun->motorHamlesiniAl();
    }
    
    // Animasyon güncelle
    if (hamleAnimasyonu) {
        animasyonuGuncelle();
    }
}

// Çiz
void Arayuz::ciz() {
    pencere.clear();
    
    // Tahta görünümü
    pencere.setView(tahtaGorunumu);
    tahtaCiz();
    
    if (oyun) {
        taslariCiz(oyun->getTahta());
        sonHamleyiCiz();
        seciliKareCiz();
        legalHamleleriCiz();
        sahKontrolCiz(oyun->getTahta());
    }
    
    koordinatlariCiz();
    
    // Panel görünümü
    pencere.setView(panelGorunumu);
    panelCiz();
    
    pencere.display();
}

// Tahta çiz
void Arayuz::tahtaCiz() {
    for (int satir = 0; satir < 8; satir++) {
        for (int sutun = 0; sutun < 8; sutun++) {
            sf::RectangleShape kare(sf::Vector2f(KARE_BOYUTU, KARE_BOYUTU));
            kare.setPosition(sutun * KARE_BOYUTU, (7 - satir) * KARE_BOYUTU);
            
            // Satranç tahtası deseni
            if ((satir + sutun) % 2 == 0) {
                kare.setFillColor(beyazKareRengi);
            } else {
                kare.setFillColor(siyahKareRengi);
            }
            
            pencere.draw(kare);
        }
    }
}

// Taşları çiz
void Arayuz::taslariCiz(const Tahta& tahta) {
    for (int kare = 0; kare < 64; kare++) {
        // Sürüklenen taşı atla
        if (suruklemeAktif && kare == suruklenenKare) continue;
        
        TasTuru tas = tahta.tasAl(kare);
        if (tas != TasTuru::YOK) {
            Renk renk = tahta.renkAl(kare);
            
            // Basit görselleştirme (sprite yoksa)
            if (tasSpriteleri.empty()) {
                sf::CircleShape tasGorseli(KARE_BOYUTU * 0.4f);
                sf::Vector2f pozisyon = kareyePixel(kare);
                tasGorseli.setPosition(pozisyon.x + KARE_BOYUTU * 0.1f,
                                       pozisyon.y + KARE_BOYUTU * 0.1f);
                
                // Renk ayarla
                if (renk == Renk::BEYAZ) {
                    tasGorseli.setFillColor(sf::Color::White);
                    tasGorseli.setOutlineColor(sf::Color::Black);
                } else {
                    tasGorseli.setFillColor(sf::Color::Black);
                    tasGorseli.setOutlineColor(sf::Color::White);
                }
                tasGorseli.setOutlineThickness(2);
                
                pencere.draw(tasGorseli);
                
                // Taş harfi
                sf::Text tasHarfi;
                tasHarfi.setFont(anaFont);
                tasHarfi.setCharacterSize(30);
                tasHarfi.setFillColor(renk == Renk::BEYAZ ? sf::Color::Black : sf::Color::White);
                
                std::string harf;
                switch (tas) {
                    case TasTuru::PIYON: harf = "P"; break;
                    case TasTuru::AT: harf = "N"; break;
                    case TasTuru::FIL: harf = "B"; break;
                    case TasTuru::KALE: harf = "R"; break;
                    case TasTuru::VEZIR: harf = "Q"; break;
                    case TasTuru::SAH: harf = "K"; break;
                    default: break;
                }
                
                tasHarfi.setString(harf);
                sf::FloatRect bounds = tasHarfi.getLocalBounds();
                tasHarfi.setOrigin(bounds.width / 2, bounds.height / 2);
                tasHarfi.setPosition(pozisyon.x + KARE_BOYUTU / 2,
                                    pozisyon.y + KARE_BOYUTU / 2);
                
                pencere.draw(tasHarfi);
            } else {
                // Sprite kullan
                auto it = tasSpriteleri.find({renk, tas});
                if (it != tasSpriteleri.end()) {
                    spriteKonumlandir(it->second, kare);
                    pencere.draw(it->second);
                }
            }
        }
    }
    
    // Sürüklenen taşı çiz
    if (suruklemeAktif && suruklenenKare >= 0) {
        sf::Vector2i farePoz = sf::Mouse::getPosition(pencere);
        sf::Vector2f dunya = pencere.mapPixelToCoords(farePoz, tahtaGorunumu);
        
        TasTuru tas = oyun->getTahta().tasAl(suruklenenKare);
        Renk renk = oyun->getTahta().renkAl(suruklenenKare);
        
        if (tasSpriteleri.empty()) {
            sf::CircleShape tasGorseli(KARE_BOYUTU * 0.4f);
            tasGorseli.setPosition(dunya.x - KARE_BOYUTU * 0.4f,
                                  dunya.y - KARE_BOYUTU * 0.4f);
            
            if (renk == Renk::BEYAZ) {
                tasGorseli.setFillColor(sf::Color(255, 255, 255, 200));
                tasGorseli.setOutlineColor(sf::Color::Black);
            } else {
                tasGorseli.setFillColor(sf::Color(0, 0, 0, 200));
                tasGorseli.setOutlineColor(sf::Color::White);
            }
            tasGorseli.setOutlineThickness(2);
            
            pencere.draw(tasGorseli);
        }
    }
}

// Panel çiz
void Arayuz::panelCiz() {
    // Arka plan
    sf::RectangleShape arkaplan(sf::Vector2f(PANEL_GENISLIGI, PENCERE_YUKSEKLIGI));
    arkaplan.setFillColor(panelArkaplanRengi);
    pencere.draw(arkaplan);
    
    oyunBilgileriniCiz();
    hamleGecmisiCiz();
    motorBilgileriniCiz();
}

// Oyun bilgilerini çiz
void Arayuz::oyunBilgileriniCiz() {
    if (!oyun) return;
    
    sf::Text baslik;
    baslik.setFont(anaFont);
    baslik.setCharacterSize(24);
    baslik.setFillColor(sf::Color::White);
    baslik.setString("Satranç Motoru");
    baslik.setPosition(10, 10);
    pencere.draw(baslik);
    
    // Sıra kimde
    sf::Text sira;
    sira.setFont(anaFont);
    sira.setCharacterSize(18);
    sira.setFillColor(sf::Color::White);
    sira.setString("Sıra: " + std::string(oyun->getSira() == Renk::BEYAZ ? "Beyaz" : "Siyah"));
    sira.setPosition(10, 50);
    pencere.draw(sira);
    
    // Oyun durumu
    if (oyun->oyunBittiMi()) {
        sf::Text durum;
        durum.setFont(anaFont);
        durum.setCharacterSize(16);
        durum.setFillColor(sf::Color::Yellow);
        durum.setString(oyun->sonucMetni());
        durum.setPosition(10, 80);
        pencere.draw(durum);
    }
}

// Motor bilgilerini çiz
void Arayuz::motorBilgileriniCiz() {
    sf::Text baslik;
    baslik.setFont(anaFont);
    baslik.setCharacterSize(18);
    baslik.setFillColor(sf::Color::White);
    baslik.setString("Motor Bilgisi");
    baslik.setPosition(10, 300);
    pencere.draw(baslik);
    
    // Derinlik
    sf::Text derinlik;
    derinlik.setFont(anaFont);
    derinlik.setCharacterSize(14);
    derinlik.setFillColor(sf::Color::White);
    derinlik.setString("Derinlik: " + std::to_string(motorDerinlik));
    derinlik.setPosition(10, 330);
    pencere.draw(derinlik);
    
    // Düğüm sayısı
    sf::Text dugumler;
    dugumler.setFont(anaFont);
    dugumler.setCharacterSize(14);
    dugumler.setFillColor(sf::Color::White);
    dugumler.setString("Düğümler: " + std::to_string(motorDugumSayisi));
    dugumler.setPosition(10, 350);
    pencere.draw(dugumler);
    
    // Düşünce
    if (!motorDusuncesi.empty()) {
        sf::Text dusunce;
        dusunce.setFont(anaFont);
        dusunce.setCharacterSize(14);
        dusunce.setFillColor(sf::Color::Cyan);
        dusunce.setString(motorDusuncesi);
        dusunce.setPosition(10, 370);
        pencere.draw(dusunce);
    }
}

// Hamle geçmişini çiz
void Arayuz::hamleGecmisiCiz() {
    sf::Text baslik;
    baslik.setFont(anaFont);
    baslik.setCharacterSize(18);
    baslik.setFillColor(sf::Color::White);
    baslik.setString("Hamleler");
    baslik.setPosition(10, 120);
    pencere.draw(baslik);
    
    // Son 8 hamleyi göster
    int baslangic = std::max(0, (int)hamleGecmisi.size() - 8);
    for (int i = baslangic; i < hamleGecmisi.size(); i++) {
        sf::Text hamle;
        hamle.setFont(anaFont);
        hamle.setCharacterSize(14);
        hamle.setFillColor(sf::Color::White);
        
        std::string hamleStr;
        if (i % 2 == 0) {
            hamleStr = std::to_string(i/2 + 1) + ". ";
        } else {
            hamleStr = "    ";
        }
        hamleStr += hamleGecmisi[i];
        
        hamle.setString(hamleStr);
        hamle.setPosition(10, 150 + (i - baslangic) * 18);
        pencere.draw(hamle);
    }
}

// Fare tıklaması işle
void Arayuz::fareTiklamisiniIsle(const sf::Event& olay) {
    if (!oyun || oyun->oyunBittiMi()) return;
    
    // Sol tık
    if (olay.mouseButton.button == sf::Mouse::Left) {
        sf::Vector2i piksel(olay.mouseButton.x, olay.mouseButton.y);
        sf::Vector2f dunya = pencere.mapPixelToCoords(piksel, tahtaGorunumu);
        
        if (tahtaIcindeMi(dunya)) {
            int kare = pixeldenKareye(dunya);
            
            // Terfi seçimi aktifse
            if (terfiSecimAktif) {
                // Terfi taşı seçimi yapılacak
                return;
            }
            
            // Taş seç veya hamle yap
            if (seciliKare == -1) {
                // Taş seç
                if (!oyun->getTahta().bosMu(kare) &&
                    oyun->getTahta().renkAl(kare) == oyun->getSira()) {
                    seciliKare = kare;
                    legalHamleKareleri.clear();
                    
                    // Legal hamleleri bul
                    HamleListesi legalHamleler = oyun->legalHamleleriAl(kare);
                    for (const Hamle& hamle : legalHamleler) {
                        legalHamleKareleri.push_back(hamle.hedef);
                    }
                    
                    // Sürüklemeyi başlat
                    suruklemeAktif = true;
                    suruklenenKare = kare;
                }
            } else {
                // Hamle yap
                hamleYap(seciliKare, kare);
                seciliKare = -1;
                legalHamleKareleri.clear();
            }
        }
    }
}

// Fare bırakma işle
void Arayuz::fareBirakmaIsle(const sf::Event& olay) {
    if (suruklemeAktif) {
        sf::Vector2i piksel(olay.mouseButton.x, olay.mouseButton.y);
        sf::Vector2f dunya = pencere.mapPixelToCoords(piksel, tahtaGorunumu);
        
        if (tahtaIcindeMi(dunya)) {
            int hedefKare = pixeldenKareye(dunya);
            
            if (hedefKare != suruklenenKare) {
                hamleYap(suruklenenKare, hedefKare);
            }
        }
        
        suruklemeAktif = false;
        suruklenenKare = -1;
        seciliKare = -1;
        legalHamleKareleri.clear();
    }
}

// Fare hareketi işle
void Arayuz::fareHareketiniIsle(const sf::Event& olay) {
    if (suruklemeAktif) {
        // Fare pozisyonunu güncelle (sürükleme animasyonu için)
        sf::Vector2i farePoz(olay.mouseMove.x, olay.mouseMove.y);
        sf::Vector2f dunya = pencere.mapPixelToCoords(farePoz, tahtaGorunumu);
        
        // Sürükleme offset'ini güncelle
        suruklemeOffset = dunya;
    }
}

// Hamle yap
void Arayuz::hamleYap(int kaynak, int hedef) {
    if (!oyun) return;
    
    // Legal mi kontrol et
    bool legal = false;
    for (int legalKare : legalHamleKareleri) {
        if (legalKare == hedef) {
            legal = true;
            break;
        }
    }
    
    if (!legal && seciliKare != -1) return;
    
    // Terfi kontrolü
    TasTuru tas = oyun->getTahta().tasAl(kaynak);
    Renk renk = oyun->getTahta().renkAl(kaynak);
    int hedefSatir = satirIndeksi(hedef);
    
    if (tas == TasTuru::PIYON && 
        ((renk == Renk::BEYAZ && hedefSatir == 7) ||
         (renk == Renk::SIYAH && hedefSatir == 0))) {
        // Terfi seçimi göster
        terfiSeciminiGoster(kaynak, hedef);
        return;
    }
    
    // Normal hamle
    oyun->hamleYap(kaynak, hedef);
    sonHamle = Hamle(kaynak, hedef, tas);
}

// Seçili kareyi çiz
void Arayuz::seciliKareCiz() {
    if (seciliKare >= 0) {
        dikdortgenCiz(seciliKare, seciliKareRengi, 4);
    }
}

// Legal hamleleri çiz
void Arayuz::legalHamleleriCiz() {
    for (int kare : legalHamleKareleri) {
        daireCiz(kare, legalHamleRengi, KARE_BOYUTU * 0.15f);
    }
}

// Son hamleyi çiz
void Arayuz::sonHamleyiCiz() {
    if (sonHamle.kaynak != sonHamle.hedef) {
        dikdortgenCiz(sonHamle.kaynak, sonHamleKaynakRengi, 3);
        dikdortgenCiz(sonHamle.hedef, sonHamleHedefRengi, 3);
    }
}

// Şah kontrolü çiz
void Arayuz::sahKontrolCiz(const Tahta& tahta) {
    if (tahta.sahCekildiMi(tahta.getSira())) {
        int sahKare = tahta.sahPozisyonu(tahta.getSira());
        dikdortgenCiz(sahKare, sahKontrolRengi, 5);
    }
}

// Koordinatları çiz
void Arayuz::koordinatlariCiz() {
    // Dosya harfleri (a-h)
    for (int i = 0; i < 8; i++) {
        sf::Text harf;
        harf.setFont(anaFont);
        harf.setCharacterSize(16);
        harf.setFillColor(sf::Color(200, 200, 200));
        harf.setString(std::string(1, 'a' + i));
        harf.setPosition(i * KARE_BOYUTU + KARE_BOYUTU/2 - 5, 
                        TAHTA_BOYUTU + 5);
        pencere.draw(harf);
    }
    
    // Satır numaraları (1-8)
    for (int i = 0; i < 8; i++) {
        sf::Text numara;
        numara.setFont(anaFont);
        numara.setCharacterSize(16);
        numara.setFillColor(sf::Color(200, 200, 200));
        numara.setString(std::to_string(i + 1));
        numara.setPosition(-20, (7 - i) * KARE_BOYUTU + KARE_BOYUTU/2 - 10);
        pencere.draw(numara);
    }
}

// Renkleri ayarla
void Arayuz::renkleriAyarla() {
    beyazKareRengi = sf::Color(240, 217, 181);
    siyahKareRengi = sf::Color(181, 136, 99);
    seciliKareRengi = sf::Color(255, 255, 0, 128);
    legalHamleRengi = sf::Color(0, 255, 0, 100);
    sonHamleKaynakRengi = sf::Color(255, 255, 0, 80);
    sonHamleHedefRengi = sf::Color(255, 255, 0, 120);
    sahKontrolRengi = sf::Color(255, 0, 0, 150);
    panelArkaplanRengi = sf::Color(50, 50, 50);
}

// Fontları yükle
bool Arayuz::fontlariYukle() {
    // Sistem fontunu yükle (varsayılan)
    if (!anaFont.loadFromFile("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf") &&
        !anaFont.loadFromFile("C:\\Windows\\Fonts\\arial.ttf") &&
        !anaFont.loadFromFile("/System/Library/Fonts/Helvetica.ttc")) {
        
        // Font bulunamazsa basit bir font oluştur
        std::cerr << "Varsayılan font yüklenemedi, devam ediliyor...\n";
        return true; // Hata verse de devam et
    }
    
    sembolFont = anaFont; // Şimdilik aynı fontu kullan
    return true;
}

// Taş görsellerini yükle
bool Arayuz::tasGorselleriniYukle() {
    // Şimdilik boş bırak, basit çizimler kullanacağız
    return true;
}

// Piksel koordinatından kare indeksine çevir
int Arayuz::pixeldenKareye(const sf::Vector2f& pozisyon) const {
    int sutun = pozisyon.x / KARE_BOYUTU;
    int satir = 7 - (pozisyon.y / KARE_BOYUTU);
    return kareIndeksi(satir, sutun);
}

// Kare indeksinden piksel koordinatına çevir
sf::Vector2f Arayuz::kareyePixel(int kare) const {
    int satir = satirIndeksi(kare);
    int sutun = sutunIndeksi(kare);
    return sf::Vector2f(sutun * KARE_BOYUTU, (7 - satir) * KARE_BOYUTU);
}

// Tahta içinde mi?
bool Arayuz::tahtaIcindeMi(const sf::Vector2f& pozisyon) const {
    return pozisyon.x >= 0 && pozisyon.x < TAHTA_BOYUTU &&
           pozisyon.y >= 0 && pozisyon.y < TAHTA_BOYUTU;
}

// Dikdörtgen çiz
void Arayuz::dikdortgenCiz(int kare, const sf::Color& renk, float kalinlik) {
    sf::Vector2f pozisyon = kareyePixel(kare);
    sf::RectangleShape dikdortgen(sf::Vector2f(KARE_BOYUTU, KARE_BOYUTU));
    dikdortgen.setPosition(pozisyon);
    dikdortgen.setFillColor(sf::Color::Transparent);
    dikdortgen.setOutlineColor(renk);
    dikdortgen.setOutlineThickness(kalinlik);
    pencere.draw(dikdortgen);
}

// Daire çiz
void Arayuz::daireCiz(int kare, const sf::Color& renk, float yariCap) {
    sf::Vector2f pozisyon = kareyePixel(kare);
    sf::CircleShape daire(yariCap);
    daire.setPosition(pozisyon.x + KARE_BOYUTU/2 - yariCap,
                     pozisyon.y + KARE_BOYUTU/2 - yariCap);
    daire.setFillColor(renk);
    pencere.draw(daire);
}

// Sprite konumlandır
void Arayuz::spriteKonumlandir(sf::Sprite& sprite, int kare) {
    sf::Vector2f pozisyon = kareyePixel(kare);
    sprite.setPosition(pozisyon);
}

// Bilgi güncelleme
void Arayuz::hamleEkle(const Hamle& hamle, const std::string& notasyon) {
    hamleGecmisi.push_back(notasyon);
    sonHamle = hamle;
}

void Arayuz::motorBilgisiGuncelle(int derinlik, int skor, uint64_t dugumSayisi, 
                                 const std::string& dusunce) {
    motorDerinlik = derinlik;
    motorSkor = skor;
    motorDugumSayisi = dugumSayisi;
    motorDusuncesi = dusunce;
}

void Arayuz::oyunSonuBildir(const std::string& sonuc) {
    // Oyun sonu bildirimini göster
    std::cout << "Oyun Bitti: " << sonuc << std::endl;
}

// Terfi seçimi
void Arayuz::terfiSeciminiGoster(int kaynak, int hedef) {
    terfiSecimAktif = true;
    terfiKaynak = kaynak;
    terfiHedef = hedef;
}

void Arayuz::terfiTasiniSec(TasTuru tas) {
    if (terfiSecimAktif && oyun) {
        oyun->hamleYap(terfiKaynak, terfiHedef, tas);
        terfiSecimAktif = false;
    }
}

// Animasyon güncelle
void Arayuz::animasyonuGuncelle() {
    // Şimdilik animasyon yok
    hamleAnimasyonu = false;
}

// Klavye girdisi işle
void Arayuz::klavyeGirdisiniIsle(const sf::Event& olay) {
    switch (olay.key.code) {
        case sf::Keyboard::Escape:
            pencere.close();
            break;
            
        case sf::Keyboard::R:
            // Yeni oyun
            if (oyun) {
                oyun->yeniOyun();
                hamleGecmisi.clear();
                sonHamle = Hamle();
            }
            break;
            
        case sf::Keyboard::U:
            // Hamle geri al
            if (oyun) {
                oyun->hamleGeriAl();
                if (!hamleGecmisi.empty()) {
                    hamleGecmisi.pop_back();
                }
            }
            break;
            
        default:
            break;
    }
}