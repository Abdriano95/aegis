# Testdata: Iteration 2 (Artikel 9-texter)

Denna katalog innehåller testdata för utvärdering av gdpr-classifierns Article9Layer. Konstruktionen av detta dataset är uppdelad i två faser enligt en hybridmetod för datakonstruktion: FAS A (automatisk generering) och FAS B (manuell granskning).

FAS A genererade de syntetiska testkandidaterna. I denna fas instruerades en lokal språkmodell att skriva realistiska men helt påhittade texter som kunde utgöra e-postmeddelanden, chattkonversationer eller interna arbetsanteckningar. Språkmodellen ombads dessutom att markera eventuella artikel 9-uppgifter (som hälsoinformation eller facktillhörighet) i dessa texter. Dessa preliminära resultat samlades i filen `article9_dataset_candidates.json`. Tillsammans med kandidaterna sparades även metadata om genereringen i `.candidates_metadata.json`. Kandidaterna utgör inte facit (ground truth) och används därför inte av några enhetstester eller automatiska utvärderingar.

FAS B omfattade det manuella arbetet. Två oberoende mänskliga granskare läste kandidattexterna och bedömde om annoteringarna var korrekta enligt GDPR. Vid oenighet fördes en diskussion fram till dess att konsensus nåddes. Resultatet av denna granskning utgör det slutgiltiga testdatasetet, vilket ligger till grund för de faktiska prestandatesterna och finns i `article9_dataset.json`. 

För en fullständig redogörelse av datats beskaffenhet, demografiska överväganden och kända metodologiska begränsningar, vänligen se `data_statement.md` i samma katalog.
