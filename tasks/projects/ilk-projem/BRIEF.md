# OC — Yerel-First Kişisel AI Çalışma Alanı

## Fikir

OC, kullanıcının bilgisayarında yaşayan ve projelerini zaman içinde tanıyan kişisel bir yapay zekâ çalışma alanıdır.

Amaç yalnızca bir sohbet ekranı yapmak değildir.

OC; kullanıcının projelerini, dosyalarını, geçmiş kararlarını, görevlerini ve üretim alışkanlıklarını tek bir yerel sistem içinde anlamalıdır. Kullanıcı her yeni sohbette bütün bağlamı yeniden anlatmak zorunda kalmamalıdır.

Sistem internet bağlantısı olmadığında da temel işlevlerini sürdürebilmeli ve harici ücretli bir yapay zekâ API’sine bağımlı olmamalıdır.

İlk ürün Windows üzerinde çalışan, kurulabilir bir masaüstü uygulaması olacaktır.

## Neden önemli?

Bugünkü AI araçlarının çoğu kullanıcının hayatını ve projelerini parçalı biçimde ele alıyor.

Bir konuşmada verilen bilgi başka bir projeye taşınmıyor. Dosyalar farklı yerlerde tutuluyor. Kullanıcı aynı bağlamı tekrar tekrar anlatıyor. Yerel ve özel kalması gereken bilgiler çoğu zaman dış servislerle paylaşılıyor.

OC’nin temel iddiası şudur:

> Yapay zekâ kullanıcıya ait olmalı; kullanıcının alanında çalışmalı ve kontrolü kullanıcıdan almamalıdır.

Bu sistem özellikle yaratıcı üreticiler, bağımsız çalışanlar ve aynı anda çok sayıda fikir geliştiren kişiler için anlamlıdır.

## Kim için?

İlk kullanıcı Koray Taşan’dır.

İlk kullanım alanları:

- Kreative Core projelerinin yönetimi
- IT’S US / US-Core fikirlerinin geliştirilmesi
- video, müzik ve senaryo projelerinin takibi
- GitHub repolarının anlaşılması
- proje dosyaları arasında bağ kurulması
- görevlerin planlanması
- kararların ve geçmiş bağlamın korunması

Daha sonraki hedef kullanıcılar:

- bağımsız yaratıcılar
- video üreticileri
- yazarlar
- geliştiriciler
- küçük ekipler
- kişisel verilerini dış servislerde tutmak istemeyen kullanıcılar

## Çözülen problem

Kullanıcı şu anda:

- fikirlerini farklı sohbetlerde tutuyor
- proje bağlamını yeniden anlatmak zorunda kalıyor
- dosyaları ve görevleri farklı uygulamalarda yönetiyor
- hangi kararın neden alındığını zamanla kaybediyor
- yerel modelleri kullanmak için teknik kurulumlarla uğraşıyor
- AI aracının hangi dosyaya eriştiğini veya ne yaptığını her zaman göremiyor

OC bu parçaları tek bir çalışma alanında birleştirmeyi hedefler.

## Temel ürün ilkeleri

### Local-first

Veriler varsayılan olarak kullanıcının bilgisayarında tutulur.

### Kullanıcı kontrolü

AI hiçbir dosyayı kullanıcı izni olmadan değiştirmez, silmez veya paylaşmaz.

### Açık davranış

Sistem başarısız olduğunda sessizce geçmez. Hatanın sebebini ve çözüm yolunu gösterir.

### Kalıcı proje hafızası

Her proje kendi geçmişine, kararlarına, görevlerine ve bağlamına sahip olur.

### Modüler yapı

Model sağlayıcısı, hafıza, dosya okuyucu ve araç sistemi birbirinden bağımsız geliştirilebilir.

### Küçük ve çalışan ilk sürüm

İlk sürüm her şeyi yapmaya çalışmaz. Az sayıda özelliği güvenilir şekilde çalıştırır.

## İlk sürümde ne olacak?

İlk MVP aşağıdaki akışı tamamlamalıdır:

1. Kullanıcı uygulamayı Windows’a kurar.
2. Yerel model sağlayıcısını bağlar.
3. Bağlantı testi yapar.
4. Yeni bir proje oluşturur.
5. Bilgisayarından bir proje klasörü seçer.
6. Uygulama desteklenen metin dosyalarını okur.
7. Kullanıcı proje hakkında yerel modelle konuşur.
8. Sohbet ve proje özeti yerel veri tabanında saklanır.
9. Kullanıcı izin verdiğinde tek bir güvenli araç çalıştırılır.
10. Yapılan işlem ve sonuç açık biçimde gösterilir.

## MVP modülleri

### Desktop Shell

Tauri tabanlı Windows masaüstü uygulaması.

### Local Model Connection

Ollama veya llama.cpp uyumlu yerel model sağlayıcısına bağlanma.

### Model Manager

En azından mevcut modelleri listeleme, model seçme ve bağlantı durumunu gösterme.

### Local Chat

Proje bağlamı ile çalışan temel sohbet ekranı.

### Project Memory

Proje özeti, kararlar, görevler ve konuşma geçmişi için yerel hafıza.

### Local File Reader

İzin verilen klasör içindeki `.md`, `.txt`, `.json`, `.toml` ve kaynak kod dosyalarını okuyabilme.

### Diagnostics

Model bağlantısı, dosya izinleri ve uygulama hatalarını açık biçimde gösterme.

### Permission Manager

Dosya yazma, komut çalıştırma ve ağ erişimi gibi işlemlerde kullanıcı onayı isteme.

### Tool Runner

İlk sürümde yalnızca izinli ve önceden tanımlanmış tek bir güvenli araç.

### Installer

Windows üzerinde normal kullanıcı tarafından kurulabilir paket.

## İlk sürümde olmayacaklar

- mobil uygulama
- bulut senkronizasyonu
- tam otonom bilgisayar kontrolü
- sınırsız shell erişimi
- kullanıcı onayı olmadan dosya değiştirme
- çok kullanıcılı şirket paneli
- ödeme sistemi
- marketplace
- otomatik sosyal medya paylaşımı
- production deployment
- gizli biçimde veri toplama

## Teknik yaklaşım

Önerilen ilk teknoloji seti:

- Tauri
- Rust
- TypeScript
- React
- SQLite
- Ollama veya llama.cpp uyumlu local inference

Sistem doğrudan tek bir modele kilitlenmemelidir. Model sağlayıcısı değiştirilebilir bir adaptör olarak ele alınmalıdır.

Uygulama içindeki AI, serbestçe terminal komutu üretip çalıştırmamalıdır. Araç sistemi allowlist yaklaşımıyla tasarlanmalıdır.

## Güvenlik ve etik

OC’nin güvenlik sınırları ürünün sonradan eklenen bir özelliği değil, temel mimarisidir.

Aşağıdaki işlemler açık kullanıcı onayı gerektirir:

- dosya yazma
- dosya silme
- terminal veya sistem komutu
- harici ağ bağlantısı
- repository push
- pull request açma
- veri dışa aktarma
- production release

Secret, token, banka bilgisi, müşteri verisi, sağlık verisi veya aile bilgisi proje reposuna yazılmamalıdır.

## Başarı ölçütü

İlk sürüm başarılı sayılacaktır eğer:

- Windows üzerinde kurulabiliyorsa
- yerel model bağlantısı kurulabiliyorsa
- proje klasörü okunabiliyorsa
- proje bağlamıyla sohbet edilebiliyorsa
- konuşma ve proje hafızası uygulama kapatılıp açıldığında korunuyorsa
- en az bir güvenli araç izin sistemiyle çalışabiliyorsa
- hatalar anlaşılır biçimde gösteriliyorsa
- bütün temel işlevler ücretli harici AI API olmadan çalışabiliyorsa

## Şirketten beklenen ilk çalışma

Kreative Core AI Company bu proje için önce uygulama geliştirmeye başlamamalıdır.

İlk döngüde şunları üretmelidir:

1. problem ve kullanıcı analizi
2. MVP kapsam doğrulaması
3. departman dağılımı
4. teknik mimari önerisi
5. veri ve izin modeli
6. güvenlik riskleri
7. 6–8 haftalık aşamalı yol haritası
8. ilk prototip görevleri
9. kabul kriterleri
10. kurucu karar listesi

## Açık sorular

- İlk sürüm yalnızca Ollama mı desteklemeli, yoksa llama.cpp de doğrudan eklenmeli mi?
- Proje hafızasında hangi bilgiler otomatik, hangileri kullanıcı onayıyla saklanmalı?
- İlk güvenli araç ne olmalı?
- Uygulama yalnız kişisel kullanım için mi tasarlanmalı, yoksa daha sonra küçük ekip yapısına açık mı bırakılmalı?
- Lisanslama ilk MVP’den önce mi, ürün doğrulandıktan sonra mı ele alınmalı?
- İlk installer imzalı mı olmalı, yoksa erken test sürümü imzasız mı dağıtılmalı?

## Somut bitiş çıktısı

Bu projenin ilk aşaması tamamlandığında elimizde şunlar olmalıdır:

- onaylanmış MVP tanımı
- mimari doküman
- veri ve izin modeli
- ekran akışları
- görev kırılımı
- risk kaydı
- çalışan Tauri uygulama kabuğu
- yerel model bağlantı testi
- proje oluşturma prototipi
- yerel hafıza prototipi
- ilk Windows test paketi
