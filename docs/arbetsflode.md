## Arbetsflöde: Issue-implementation

Vi jobbar en issue i taget i följande loop:

1. Claude skriver en strukturerad Cursor-prompt för nästa issue,
   med kontext, specifikation, regler, arbetsflöde och definition
   of done.

2. Användare klistrar in prompten i Cursor (Plan Mode).

3. Cursor genererar en plan. Användare kopierar planen tillbaka
   till Claude.

4. Claude verifierar planen mot arkitektur.md och flaggar
   eventuella avvikelser. Om den stämmer: "Stämmer. Kör den."

5. Användare kör planen i Cursor (Agent Mode).

6. Användare kopierar tillbaka den genererade koden och
   sessionsloggen till Claude.

7. Claude granskar och säger antingen "Committa: git commit -m
   '...'" eller flaggar problem.

8. Användare committar och pushar. Claude föreslår nästa issue.

Issue-promptens mall finns i docs/iteration_1_planering.md
(avsnittet "Format" under Agent-sessionslogg visar sessionslogg-
mallen, och den strukturerade issue-prompten följer mönstret
som använts genomgående i iteration 1).

Claude ska inte generera kod direkt - Cursor gör implementationen.
Claude ansvarar för specifikation, verifiering och arkitekturell
koherens.