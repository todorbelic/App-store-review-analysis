# Arhitektura sistema velikih skupova podataka

### Analiza korisničkih recenzija mobilnih aplikacija

---

## 1. Domen i motivacija

Tržište mobilnih aplikacija jedan je od najdinamičnijih segmenata digitalne ekonomije. Google Play Store i Apple App Store zajedno broje više od pet miliona aktivnih aplikacija, a svakodnevno pristaju milioni novih korisničkih recenzija. Svaka recenzija predstavlja dragocen signal — o kvalitetu aplikacije, o reagovanju developera na probleme, o uticaju novih verzija na korisničko iskustvo.

Ovaj projekat bavi se prikupljanjem, čuvanjem, obradom i vizualizacijom takvih recenzija, sa ciljem izvlačenja upotrebljivih saznanja za različite zainteresovane strane u industriji mobilnih aplikacija.

---

## 2. Persone

### Persona 1 — Product Manager

Zanima ga kako korisnici reaguju na nove verzije aplikacije, koji problemi se ponavljaju u recenzijama i kako se sentiment menja kroz vreme. Želi da dobije upozorenje kada neka aplikacija naglo padne u ocenama nakon update-a, kao i da razume koje kategorije grešaka dominiraju u negativnim recenzijama.

### Persona 2 — Konsultant

Konsultant koji analizira konkurentske aplikacije za više klijenata. Zanima ga poređenje performansi aplikacija po kategorijama, trendovi sentimenta na različitim tržištima (SAD, Evropa, Indija), kao i identifikacija aplikacija koje dobijaju neuobičajeno visok broj negativnih recenzija u kratkom periodu (tzv. review bombing).

---

## 3. Skupovi podataka

### 3.1 Primarni skup — Google Play Store (web scraping)

Primarni, istorijski skup podataka prikuplja se tehnikom web scraping-a korišćenjem Python biblioteke `google-play-scraper`. Podaci se skupljaju za top 100 aplikacija po kategorijama, iz više zemalj, pri čemu se za svaku aplikaciju skupljaju i recenzije i metapodaci aplikacije.

**Očekivana veličina:** 100 aplikacija × 4 zemlje × 10.000 recenzija ≈ **4.000.000 redova / ~500 MB CSV**

#### Kolone — recenzije i metapodaci

| Kolona | Tip | Opis |
|---|---|---|
| `review_id` | STRING | Jedinstveni identifikator recenzije |
| `package_id` | STRING | Google Play paket ID aplikacije |
| `app_name` | STRING | Naziv aplikacije |
| `country` | STRING | Zemlja (ISO 3166) |
| `rating` | INTEGER | Ocena (1–5) |
| `review_text` | STRING | Tekst recenzije |
| `thumbs_up` | INTEGER | Broj "korisno" glasova |
| `app_version` | STRING | Verzija aplikacije u trenutku recenzije |
| `review_date` | TIMESTAMP | Datum i vreme recenzije |
| `dev_reply` | STRING | Odgovor developera (NULL ako nema) |
| `genre` | STRING | Kategorija aplikacije |
| `total_ratings` | INTEGER | Ukupan broj ocena aplikacije |
| `min_installs` | BIGINT | Minimalan broj instalacija |
| `free` | BOOLEAN | Da li je aplikacija besplatna |
| `offers_iap` | BOOLEAN | Da li nudi in-app kupovine |
| `developer` | STRING | Naziv developera |
| `content_rating` | STRING | Uzrasna kategorija (Everyone, Teen...) |
| `ad_supported` | BOOLEAN | Da li sadrži reklame |

### 3.2 Sekundarni skup — Apple RSS Feed API (real-time tok)

Sekundarni skup podataka prikuplja se periodičnim povlačenjem podataka sa Apple App Store RSS Feed API-ja. API je besplatan i javan, ne zahteva autentifikaciju, a vraća poslednjih 50 recenzija po aplikaciji po zahtevu. Polling se vrši na svakih 5 minuta za izabrane aplikacije, pri čemu se svaka nova recenzija objavljuje u Apache Kafka temu.

**Endpoint:** `https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json`

#### Kolone — Apple stream recenzije

| Kolona | Tip | Opis |
|---|---|---|
| `review_id` | STRING | Jedinstveni ID (app_id + country + entry_id) |
| `app_id` | STRING | Apple App Store identifikator |
| `app_name` | STRING | Naziv aplikacije |
| `country` | STRING | Zemlja (ISO 3166) |
| `rating` | INTEGER | Ocena (1–5) |
| `review_text` | STRING | Tekst recenzije |
| `app_version` | STRING | Verzija aplikacije |
| `timestamp` | TIMESTAMP | Datum i vreme recenzije |
| `category` | STRING | Kategorija (mapirana iz lookup tabele) |

---

## 4. Pitanja za paketnu obradu podataka

Implementiraju se kao Apache Spark batch upiti nad curated zonom jezera podataka.

1. Koje aplikacije su zabeležile najveći pad prosečne ocene u mesecu nakon objavljivanja nove verzije? 
2. Koja kategorija aplikacija ima najnegativniji prosečan sentiment recenzija? *(NLP + agregacija po kategoriji)*
3. Koje ključne reči se najčešće pojavljuju u recenzijama sa ocenom 1 i 2, po kategoriji? *(keyword extraction)*
4. Kako se prosečna ocena svake aplikacije menja kroz mesece — trend rasta ili pada? *(time series, window funkcija)*
5. Koje aplikacije imaju najveću disperziju ocena (polarizovane recenzije)? *(standardna devijacija po aplikaciji)*
6. Da li postoji korelacija između dužine teksta recenzije i date ocene?
7. Koje aplikacije imaju najviše recenzija koje pominju reči "crash", "bug", "freeze" ili "broken"?
8. Koji developeri konzistentno dobijaju visoke ocene kroz sve svoje aplikacije? *(window RANK po developeru)*
9. Da li aplikacije koje nude in-app kupovine (`offers_iap = true`) imaju lošije ocene od besplatnih bez IAP?
10. Koje aplikacije su imale naglo povećanje negativnih recenzija u kratkom periodu — detekcija review bombing-a? *(rolling window)*
11. Koliki procenat negativnih recenzija dobija odgovor od developera (`dev_reply IS NOT NULL`), po kategoriji?
12. Kako se sentiment recenzija razlikuje po zemljama za iste aplikacije? *(agregacija po country + app_name)*

---

## 5. Pitanja za obradu u realnom vremenu

Implementiraju se kao Apache Flink stream transformacije nad Apple RSS tokom podataka, uz korišćenje windowing-a i spajanja sa batch podacima iz curated zone.

1. Koji je trenutni prosečni sentiment novih Apple recenzija u sliding window-u od 30 minuta, po kategoriji? 
2. Da li neka aplikacija dobija neuobičajeno veliki broj negativnih recenzija upravo sada — anomaly?
3. Koje ključne reči dominiraju u recenzijama koje pristižu u realnom vremenu, u poslednjih 15 minuta? 
4. Kako se prosečna ocena Apple recenzija u sliding window-u od 1 sat poredi sa istorijskim prosekom iz Google Play batch podataka?
5. Koje aplikacije u realnom vremenu beleže pad ocene ispod praga od 3.0 u poslednjih 2 sata? 

---
