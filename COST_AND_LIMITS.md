# Maliyet ve Limitler

- Ücretli model API'si kullanılmaz.
- Model açık ağırlıklıdır.
- Inference `llama.cpp` ile GitHub-hosted runner üzerinde yapılır.
- Model ve motor private GitHub Release asset'i olarak saklanır.
- AI işlerinin eşzamanlılığı 1 ile sınırlıdır.
- Analiz, kodlama ve review workflow'larında süre sınırı vardır.
- Günlük tarama model çalıştırmaz; yalnızca klasör ve issue yönetimi yapar.

Private repo Actions kullanımı plan kotana tabidir. Beklenmedik ödeme ihtimalini azaltmak için
GitHub Billing'de Actions bütçesini sıfır dolarlık hard stop olarak ayarla.
