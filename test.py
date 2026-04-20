import spacy
nlp = spacy.load("sv_core_news_lg")
doc = nlp("Hej Anna Svensson, tack för att du hörde av dig angående ärendet.")
for ent in doc.ents:
    print(f"{ent.text!r} → {ent.label_}")