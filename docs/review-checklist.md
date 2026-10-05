# 10 punktu pārskatīšanas kontrolsaraksts (review checklist)

Lieto visam, ko izmaiņa skar, ne tikai jaunajām rindām.

1. Pieņemšanas kritēriji izpildīti, arī negatīvie gadījumi
2. Līgums (API contract) nav mainīts, vai izmaiņa ir dokumentēta
3. Nav noslēpumu (secrets) kodā, konfigurācijā, testos, žurnālos vai uzvednēs
4. Nav personas datu žurnālos vai kļūdās vairāk, nekā vajag
5. Kļūdas apstrādātas skaidri un droši (fail safe), bez iekšējās informācijas atbildē
6. Ārējiem izsaukumiem ir noildze (timeout), statusa apstrāde un negaidītu vērtību apstrāde
7. Ievade ir validēta, vaicājumi ir parametrizēti
8. Atkarības eksistē, ir vajadzīgas, uzturētas, ar fiksētu versiju un bez zināmām ievainojamībām
9. Tikai uzdevumā paredzētās izmaiņas
10. Testi pierāda pieņemšanas kritērijus un **var krist**

## Atraduma pieraksts

| Vieta (fails:rinda) | Nozīmīgums | Ietekme | Labojums vai pamatojums |
|---|---|---|---|
| app/storage.py:258 (bandit B608) | jālabo | `withdraw()` SQL vaicājums tika veidots ar f-string. Tajā bija tikai `?` vietturi, bet paraugs viegli kļūst par SQL injekciju. | Labots: statusus nodod kā JSON parametru `json_each(?)`, bandit vairs neziņo, testi zaļi. |
| app/storage.py:246 | bloķējošs | `update_status` žurnālā rakstīja visu ierakstu: personas kodu, vārdu, e-pastu un tekstu (pārkāpj CR-A 8. kritēriju). | Labots: žurnālā tikai ID un statuss. Tests `test_cra_ac8_no_personal_data_in_logs_or_errors` krīt, ja atjauno veco kodu. |
| app/errors.py:60 | jālabo | 500 atbildē ir `str(exc)`, tātad iekšējā informācija (ID, SQLite versija). | Atlikts: CR-A ceļš 500 neizraisa, labojums mainītu visus galapunktus. Jāveido atsevišķs pieteikums. |
| app/storage.py:290 (bandit B608) | bloķējošs CR-B | `find_institution` ievieto `code` tieši SQL vaicājumā, tātad SQL injekcija. | Atlikts uz CR-B: CR-A šo funkciju neizmanto. |
| requirements.txt:3 (pip-audit) | jālabo | `requests==2.31.0` ir 6 zināmas ievainojamības. | Atlikts: CR-A atkarības nemaina. Jāatjaunina uz 2.33.0 atsevišķi un jāpārbauda ar CR-2 testiem. |
