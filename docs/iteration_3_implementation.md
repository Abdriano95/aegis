# Iteration 3: Implementationsplanering

**Projekt:** gdpr-classifier  
**Iteration:** 3 (v0.3.0-dev)  
**Period:** V19–V21  
**Metodik:** Scrumban (kanban-board i GitHub Projects)

> **[UNDER UPPBYGGNAD]** Denna fil är under aktiv uppbyggnad. Iterationsförberedelse pågår och specifik teknisk planering — inklusive issue-specifikationer, beroendekarta och förväntade resultat — fylls i löpande i takt med att planeringen för iteration 3 genomförs tillsammans med arkitekt-agenten. En framtida läsare (handledare, examinator eller annan agent) bör beakta att innehållet reflekterar ett pågående arbete och att tomma sektioner är avsiktliga platshållare.

**Startdatum:** 2026-05-07  
**Slutdatum (planerat):** 2026-05-20  
**Status:** Pågår

---

## Mål och scope

[Fastställs i planeringssession]

---

## Beroendekarta

Beroendekartan visar vilka issues som beror på varandra och i vilken ordning de bör implementeras, inklusive parallella spår och konvergenspunkter.

<!-- Kluster-struktur fastställs i planeringssession -->

---

## Förväntade resultat

[Fastställs i planeringssession]

---

## Issue-specifikationer

Status-legenda: ✅ Klar | 🔄 Pågår | ⏸️ Blockerad | ⬜ Ej startad

<!-- Kluster-struktur fastställs i planeringssession -->

---

## Loggbok

Designbeslut för iteration 3 dokumenteras i Loggboken (Google Docs) under fliken **"Loggbok - iteration 3"**. Format: beslut, alternativ som övervägdes, motivering, koppling till GDPR-krav eller empiriskt stöd.

Denna fil listar inga beslut. Alla arkitektoniska och metodologiska avgöranden under iteration 3 förs in direkt i Loggboken med full motivering. Om ett beslut genereras under en agent-session ska det även noteras i sessionens post under "Beslut fattade" nedan, med hänvisning till Loggboken för längre motivering.

---

## Arbetsflöde

Iteration 3 följer samma åtta-stegs-loop som iteration 1 och 2, beskriven i [`arbetsflode.md`](arbetsflode.md). Skillnaden mot iteration 1 är att Claude Code används som implementations-agent istället för Cursor: Claude Code tar emot issue-specifikationer, genererar plan i Plan Mode, och implementerar i Agent Mode efter användarens godkännande.

---

## Agent-sessionslogg

### Regel

**Varje agent (AI eller människa) som arbetar i en session ska logga sin session här efter avslutad iteration.** Loggen är komplement till Loggboken ovan: Loggboken dokumenterar *beslut och motiveringar*, medan sessionsloggen dokumenterar *vad som faktiskt gjordes, i vilken ordning, och av vem*. Syftet är spårbarhet och att nästa agent (eller granskare) snabbt ska kunna förstå repots historik utan att läsa hela git-loggen.

### Format

Lägg till en ny post längst ner. Använd följande mall:

```markdown
### Session YYYY-MM-DD - [Agent/Person]

**Iteration:** [t.ex. 3 / v0.3.0]
**Mål:** [en mening om vad sessionen skulle åstadkomma]

**Ändrade filer:**
- `path/till/fil.py` - [kort beskrivning]

**Gjort:**
- [punkt per konkret åtgärd]

**Beslut fattade:** [kort; länka till Loggboken om längre motivering behövs]
**Öppet/Nästa steg:** [vad som återstår eller blockerar]
```

### Regler för loggning

1. Logga **efter varje iteration** (eller efter en sammanhållen arbetssession om iterationen sträcker sig över flera dagar).
2. En post per session, inte per commit.
3. Håll det kort: punktlistor, inga resonemang (de hör hemma i Loggboken).
4. Ändra aldrig tidigare poster. Lägg till en ny post om något behöver korrigeras.
5. Om sessionen genererade arkitekturbeslut ska dessa även föras in i Loggboken med full motivering.

### Poster

<!-- Kommande sessionsposter läggs till här i kronologisk ordning. -->
