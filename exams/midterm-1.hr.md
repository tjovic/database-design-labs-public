# Međuispit 1 – što vas očekuje

Međuispit 1 nosi 44 boda u 88 minuta, raspoređena na tri ishoda učenja. Ovdje su navedene vrste zadataka koje možete očekivati, koliko bodova nosi pojedina vrsta i gdje je u ovom repozitoriju možete vježbati.

---

## Format ispita

- Sve zadatke rješavate pisanjem T-SQL koda u SQL Server Management Studiju (SSMS).
- Ispit se piše nad bazom `AdventureWorksENG`, istom koju koristite na labovima.
- Predajete jednu `.sql` datoteku nazvanu `OBP-<Ime-Prezime>.sql`.
- Ispred svakog rješenja stavite komentar s oznakom zadatka, npr. `-- I2Z1` (ishod učenja 2, zadatak 1).
- Ako tijekom ispita oštetite bazu, možete je vratiti iz sigurnosne kopije (u SSMS-u: **Databases → Restore Database…**). Provjerite znate li to napraviti.
- Nije dozvoljeno korištenje opreme i usluga koje nisu navedene u uputama ispita.

| Ishod učenja | Teme | Zadaci | Bodovi | Vrijeme |
| --- | --- | --- | --- | --- |
| I1 | Pogledi i okidači | 6 | 24 | 48 min |
| I2 | Procedure, funkcije, indeksi, fizička pohrana | 4 | 13 | 26 min |
| I3 | CRUD operacije | 2 | 7 | 14 min |
| **Ukupno** | | **12** | **44** | **88 min** |

Predviđeno vrijeme je dvije minute po bodu. Koristite ga da procijenite kada je vrijeme da prijeđete na sljedeći zadatak.

---

## Ishod učenja 1 (I1) – pogledi i okidači (24 boda)

Očekujte četiri zadatka s pogledima (14 bodova) i dva zadatka s okidačima (10 bodova).

| Vrsta zadatka | Bodovi | Trebate znati | Gdje vježbati |
| --- | --- | --- | --- |
| Pogled s agregacijom | 3 | Napraviti pogled koji vraća agregiranu vrijednost iz spojenih i filtriranih tablica; ukloniti ga | Lab 01: [Sekcija 1](../labs/lab01-views.md#section-1--why-views-exist), [Sekcija 3](../labs/lab01-views.md#section-3--modifying-and-dropping-views)<br>[Vježbe s pogledima](../exercises/lab01-views.md): [Vježba 1](../exercises/lab01-views.md#exercise-1--create-your-first-view-beginner), [Vježba 2](../exercises/lab01-views.md#exercise-2--modify-the-view-beginner), [Vježba 3](../exercises/lab01-views.md#exercise-3--hide-a-join-inside-a-view-beginner) |
| Korištenje pogleda u upitu | 4 | Napraviti pogled i koristiti ga u upitu s grupiranjem, filtriranjem ili `TOP`; ukloniti ga | Lab 01: [Sekcija 1](../labs/lab01-views.md#section-1--why-views-exist)<br>[Vježbe s pogledima](../exercises/lab01-views.md): [Vježba 3](../exercises/lab01-views.md#exercise-3--hide-a-join-inside-a-view-beginner) |
| Opcije pogleda | 3–4 | Prepoznati koju opciju zahtjev traži – `WITH ENCRYPTION`, `WITH SCHEMABINDING` ili `WITH CHECK OPTION` – i primijeniti je s `ALTER VIEW` | Lab 01: [Sekcija 7 (CHECK OPTION)](../labs/lab01-views.md#section-7--with-check-option), [Sekcija 8 (SCHEMABINDING)](../labs/lab01-views.md#section-8--with-schemabinding), [Sekcija 9 (ENCRYPTION)](../labs/lab01-views.md#section-9--with-encryption), [Sekcija 10](../labs/lab01-views.md#section-10--combining-view-options)<br>[Vježbe s pogledima](../exercises/lab01-views.md): [Vježba 8](../exercises/lab01-views.md#exercise-8--with-check-option-advanced), [Vježba 9](../exercises/lab01-views.md#exercise-9--schemabinding-advanced) |
| Okidač koji prepoznaje situaciju | 5 | Napraviti tablicu zapisnika i `INSERT` ili `UPDATE` okidač koji prepoznaje što se dogodilo i upisuje odgovarajuću poruku; demonstrirati svaki slučaj; ukloniti okidač | Lab 02: [Sekcija 3](../labs/lab02-triggers.md#section-3--the-inserted-and-deleted-tables), [Sekcija 4](../labs/lab02-triggers.md#section-4--triggers-fire-once-per-statement), [Sekcija 8](../labs/lab02-triggers.md#section-8--one-trigger-for-multiple-events), [Sekcija 10](../labs/lab02-triggers.md#section-10--real-world-example-checking-a-business-rule)<br>[Vježbe s okidačima](../exercises/lab02-triggers.md): [Vježba 1](../exercises/lab02-triggers.md#exercise-1--first-logging-trigger-beginner), [Vježba 2](../exercises/lab02-triggers.md#exercise-2--log-inserted-rows-beginner), [Vježba 4](../exercises/lab02-triggers.md#exercise-4--log-renamed-cities-intermediate), [Vježba 5](../exercises/lab02-triggers.md#exercise-5--audit-inserted-products-beginner) |
| Okidač sa starim i novim vrijednostima | 5 | Napraviti `UPDATE` okidač koji reagira na promjene određenih stupaca i zapisuje stare i nove vrijednosti; obraditi promjenu jednog i više redaka; demonstrirati svaki slučaj | Lab 02: [Sekcija 5](../labs/lab02-triggers.md#section-5--update-old-and-new-values), [Sekcija 7](../labs/lab02-triggers.md#section-7--the-update-function)<br>[Vježbe s okidačima](../exercises/lab02-triggers.md): [Vježba 3](../exercises/lab02-triggers.md#exercise-3--multi-row-safety-intermediate), [Vježba 4](../exercises/lab02-triggers.md#exercise-4--log-renamed-cities-intermediate), [Vježba 6](../exercises/lab02-triggers.md#exercise-6--audit-actual-price-changes-intermediate), [Vježba 9](../exercises/lab02-triggers.md#exercise-9--debug-a-flawed-price-audit-trigger-advanced) |

Zadaci s opcijama pogleda opisuju problem, a ne opciju. Vježbajte čitanje zahtjeva („nitko ne smije pročitati definiciju“, „pogled je prestao raditi nakon promjene tablice“, „redak koji sam upisao kroz pogled je nestao“) i prepoznavanje opcije koja ga rješava.

---

## Ishod učenja 2 (I2) – procedure, funkcije, indeksi, fizička pohrana (13 bodova)

Očekujte po jedan zadatak svake vrste.

| Vrsta zadatka | Bodovi | Trebate znati | Gdje vježbati |
| --- | --- | --- | --- |
| Pohranjena procedura s OUTPUT i RETURN | 5 | Napisati proceduru koja ovisno o podacima vraća različite vrijednosti kroz `OUTPUT` parametre i `RETURN`; pozvati je za svaki slučaj | Lab 03: [Sekcija 4](../labs/lab03-stored-procedures.md#section-4--returning-data), [Sekcija 5](../labs/lab03-stored-procedures.md#section-5--putting-it-together-bank-transfer)<br>[Vježbe s procedurama](../exercises/lab03-stored-procedures.md): [Vježba 4](../exercises/lab03-stored-procedures.md#exercise-4--find-the-bug-beginner), [Vježba 5](../exercises/lab03-stored-procedures.md#exercise-5--return-invoices-and-a-match-count-intermediate), [Vježba 7](../exercises/lab03-stored-procedures.md#exercise-7--return-a-product-price-and-status-advanced) |
| Skalarna funkcija | 3 | Napisati skalarnu funkciju koja čita podatke; pozvati je samostalno i unutar upita; promijeniti je s `ALTER`; ukloniti je | Lab 04: [Sekcija 3](../labs/lab04-functions.md#section-3--scalar-functions), [Sekcija 4](../labs/lab04-functions.md#section-4--scalar-functions-that-read-data)<br>[Vježbe s funkcijama](../exercises/lab04-functions.md): [Vježba 4](../exercises/lab04-functions.md#exercise-4--total-quantity-sold-per-product-intermediate), [Vježba 5](../exercises/lab04-functions.md#exercise-5--latest-invoice-date-per-customer-intermediate) |
| Optimizacija upita | 3 | Ukloniti neklasterirane indekse s tablice, a zatim zadani upit učiniti što bržim: po potrebi prepisati uvjete i napraviti odgovarajući indeks; dokazati poboljšanje sa `SET STATISTICS IO ON` | Lab 04: [Sekcija 7](../labs/lab04-functions.md#section-7--two-performance-warnings)<br>Lab 06: [Sekcija 8](../labs/lab06-indexes.md#8-create-indexes-and-observe-the-changing-plan), [Sekcija 10](../labs/lab06-indexes.md#10-index-design-principles)<br>[Vježbe s indeksima](../exercises/lab06-indexes.md) |
| Fizička pohrana | 2 | Utvrditi koliko podatkovnih i indeksnih stranica tablica koristi, koji su reci na određenoj stranici i kolika je duljina zapisa; naredbe i odgovore upisati u skriptu | Lab 05: [Sekcija 11](../labs/lab05-physical-storage.md#11-dbcc-ind--which-pages-belong-to-a-table), [Sekcija 12](../labs/lab05-physical-storage.md#12-dbcc-page--look-inside-a-data-page), [Sekcija 13](../labs/lab05-physical-storage.md#13-practical-example--how-much-space-does-a-row-occupy)<br>[Vježbe za fizičku pohranu](../exercises/lab05-physical-storage.md) |

---

## Ishod učenja 3 (I3) – CRUD operacije (7 bodova)

Očekujte dva zadatka. Pažljivo pročitajte koje objekte zadatak traži i trebaju li se obraditi i povezane tablice.

| Vrsta zadatka | Bodovi | Trebate znati | Gdje vježbati |
| --- | --- | --- | --- |
| CRUD nad jednom tablicom | 4 | Napraviti točno tražene objekte – npr. jednu proceduru za sve operacije ili proceduru i funkciju – za upis, dohvat, izmjenu i brisanje nad tablicom; demonstrirati sve četiri operacije | Lab 07: [Sekcija 2](../labs/lab07-crud-operations.md#section-2--crud-with-separate-procedures), [Sekcija 3](../labs/lab07-crud-operations.md#section-3--practice-crud-for-state-and-city), [Sekcija 4](../labs/lab07-crud-operations.md#section-4--functions-and-data-access), [Sekcija 5](../labs/lab07-crud-operations.md#section-5--one-procedure-for-multiple-operations)<br>[CRUD vježbe](../exercises/lab07-crud-operations.md): [Vježba 1](../exercises/lab07-crud-operations.md#exercise-1--one-procedure-per-operation-beginner), [Vježba 2](../exercises/lab07-crud-operations.md#exercise-2--read-through-an-inline-table-valued-function-beginner), [Vježba 3](../exercises/lab07-crud-operations.md#exercise-3--insert-and-update-in-one-procedure-intermediate), [Vježba 4](../exercises/lab07-crud-operations.md#exercise-4--find-the-bug-intermediate), [Vježba 5](../exercises/lab07-crud-operations.md#exercise-5--one-procedure-for-several-operations-intermediate) |
| CRUD s povezanim tablicama | 3 | Napisati proceduru za jednu CRUD operaciju (npr. upis ili brisanje) koja obrađuje i retke povezanih tablica; demonstrirati je | Lab 07: [Sekcija 6](../labs/lab07-crud-operations.md#section-6--error-handling-in-crud-operations), [Sekcija 7](../labs/lab07-crud-operations.md#section-7--data-integrity-and-business-rules), [Sekcija 8](../labs/lab07-crud-operations.md#section-8--final-exercise-get-and-delete-without-breaking-the-rules)<br>[CRUD vježbe](../exercises/lab07-crud-operations.md): [Vježba 6](../exercises/lab07-crud-operations.md#exercise-6--where-to-catch-the-error-intermediate), [Vježba 7](../exercises/lab07-crud-operations.md#exercise-7--delete-with-related-rows-advanced), [Vježba 8](../exercises/lab07-crud-operations.md#exercise-8--insert-with-related-rows-advanced) |

---

## Savjeti

- **Demonstrirajte svaki slučaj** koji zadatak traži: svaki poziv procedure, funkcije ili okidača mora biti u skripti.
- **Odgovore na pitanja** (npr. broj stranica) upišite kao komentar, uz naredbe kojima ste do njih došli.
- **Napišite naredbu `DROP`** kad zadatak traži uklanjanje objekta.
- **Prije predaje jednom pokrenite cijelu skriptu** i provjerite rade li svi zadaci bez grešaka.
