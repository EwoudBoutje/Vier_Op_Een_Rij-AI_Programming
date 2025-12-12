# Resultaat
n dit project hebben we verschillende belangrijke onderdelen ontwikkeld die samen een complete, speelbare en gebruiksvriendelijke game vormen. De belangrijkste onderdelen zijn:

1. Een hoofdmenu met drie spelmodes
2. Een leaderboard voor winnaars en verliezers
3. Geluidseffecten in de game
4. Animaties en visuele effecten
5. Een AI-tegenstander
6. Een overzichtelijke interface en bediening

In de volgende secties wordt elk onderdeel verder uitgewerkt.

## 1.  Hoofdmenu met drie spelmodes

Het project bevat een duidelijk hoofdmenu waarin spelers kunnen kiezen uit drie verschillende spelmodi: Player tegen AI, Player tegen Player en AI tegen AI. Dit menu vormt de start van de hele game en bepaalt hoe het spelverloop verder gaat. Spelers kunnen zo zelf kiezen of ze tegen elkaar willen spelen, tegen de computer, of een volledig geautomatiseerde simulatie willen zien.

<img src="./afbeeldingen/Hoofdmenu.png" alt="Hoofdmenu" width="28%">

## 2. Leaderboard voor winnaars en verliezers

De game beschikt over een automatisch werkend leaderboard waarin per potje wordt bijgehouden wie er heeft gewonnen of verloren. Na afloop voert de 
dezelfde naam speelt, wordt de bestaande score alleen overschreven als de nieuwe prestatie beter (bij winst) of juist slechter (bij verlies) is.

Een voorbeeld: als een speler het vorige potje verloor in 15 zetten en nu verliest in slechts 7 zetten, dan wordt de score vervangen omdat 7 
zetten een “sneller verlies” is en dus een slechter resultaat.

Het leaderboard bestaat uit twee lijsten: de Hall of Fame (beste prestaties) en de Hall of Shame (slechtste prestaties). In beide lijsten worden 
maximaal vijf namen getoond. Overige scores worden nog steeds opgeslagen in het JSON-bestand, maar verschijnen niet meer zichtbaar in de top vijf.

<img src="./afbeeldingen/leaderbord.png" alt="Leaderbord" width="28%">
<img src="./afbeeldingen/winst.png" alt="winst" width="28%" height="120px">
<img src="./afbeeldingen/verlies.png" alt="verlies" width="28%" height="120px">


## 3. Geluidseffecten in de game

Bij verschillende acties en gebeurtenissen worden passende geluidseffecten afgespeeld. Denk hierbij aan geluid bij het klikken op knoppen, het vallen van muntjes en bij winst of verlies. Dit zorgt voor een levendige en meeslepende spelervaring.

[Sounds](/Software/GameWithAi/sounds/)

## 4. Animaties en visuele effecten

De game bevat animaties die ervoor zorgen dat het spel er dynamisch uitziet. Het meest opvallend is de animatie waarin een muntje echt naar beneden valt in het bord. Ook wordt een winnende rij visueel gemarkeerd zodat de speler snel ziet hoe het spel gewonnen is.

Waar afbeelding toevoegen:
➡ Afbeelding 4: Screenshot van een muntje dat halverwege naar beneden valt.
➡ Afbeelding 5: Screenshot van een winnende vier-op-een-rij met highlight.

## 5. Kunstmatige intelligentie (AI)

De game bevat een slimme AI die strategische zetten kan bepalen. De AI analyseert mogelijke zetten, beoordeelt kansen op winst en speelt op een manier die het voor de speler uitdagend maakt. Daarnaast wordt de AI ook gebruikt in de AI-tegen-AI-modus, waarbij het spel volledig automatisch verloopt.

Waar afbeelding toevoegen:
➡ Afbeelding 6: Screenshot van een AI-beweging of een situatie waarin “AI is thinking” zichtbaar is.

## 6. Interface en bediening

De game heeft een overzichtelijke interface met duidelijke knoppen voor teruggaan, opnieuw starten en het aanpassen van de snelheid voor AI-tegen-AI. De vormgeving is eenvoudig en ondersteunt de speler in het navigeren door het spel en het begrijpen van de spelstatus.

Waar afbeelding toevoegen:
➡ Afbeelding 7: Screenshot van het spelbord inclusief UI-elementen (restart-icoon, home-icoon, tekst bovenaan).