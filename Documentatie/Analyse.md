# Analyse
In dit project ontwikkelden we een complete implementatie van Vier op een Rij met een intelligente 
AI-tegenstander. Het doel was een spelervaring te creëren waarin de speler in real time tegen een sterke, maar 
snelle computertegenstander kan spelen. Om dit te bereiken werd eerst de probleemstelling geanalyseerd en vertaald 
naar een concrete technische aanpak.

De analyse startte met het vaststellen van de uitdagingen die verbonden zijn aan bordspellen: het zoekoppervlak 
groeit exponentieel naarmate meer toekomstige zetten worden overwogen. Daarom kozen we voor een methode die 
optimaal geschikt is voor deterministische, perfect-informatie spellen: een zoekalgoritme gebaseerd op minimax in 
combinatie met alpha-beta pruning. Deze technieken zijn veel efficiënter dan brute-force zoeken en sluiten perfect 
aan bij het type probleem dat Vier op een Rij vormt.

Tijdens de analyse werd duidelijk dat verdere optimalisatie noodzakelijk was om de AI binnen een krappe 
tijdslimiet (2 seconden per zet) te laten functioneren. We implementeerden daarom verschillende optimalisaties: 
iterative deepening zodat de AI in steeds grotere diepte zoekt zolang er tijd over is, move ordering om winnende 
en blokkerende zetten te prioriteren, en een transposition table met Zobrist hashing om eerder berekende 
bordsituaties te herkennen. Deze combinatie van technieken maakt het mogelijk om op consumentenharde snel sterke 
zetten te berekenen. Daarnaast werd een heuristische evaluatiefunctie ontwikkeld die de kwaliteit van een 
bordpositie inschat op basis van rijen, kolommen en diagonalen.

Naast de AI-analyse werd ook de gebruikerservaring onder de loep genomen. Om het spel visueel aantrekkelijk en 
intuïtief te maken, is gekozen voor Pygame. Deze library zorgt voor het tekenen van het bord, de animatie van 
vallende stukken en de interactie met muis en toetsenbord. Een belangrijk aandachtspunt in deze fase was het 
voorkomen dat de UI blokkeert terwijl de AI denkt. Dit is opgelost door de AI-logica in een aparte thread uit te 
voeren, waardoor de interface altijd responsief blijft.

Dit project maakt geen gebruik van datasets. De AI is volledig regelgebaseerd en vergt geen training. 
Vergelijkbare projecten zijn onder meer andere klassieke bordspellen (zoals schaak- of dam-AI’s) die eveneens 
zoekalgoritmes met optimalisaties inzetten.

De inferentie gebeurt volledig lokaal en real time op de CPU. Er is geen speciale hardware vereist: elke standaard 
laptop of desktop kan de AI zonder merkbare vertraging draaien. Evenmin is er specifieke trainingshardware nodig, 
omdat er geen machine-learningmodel gebruikt wordt.

Qua software voldoet een standaard Python-omgeving (Python 3.10+) op Windows, macOS of Linux. De belangrijkste 
libraries zijn Pygame, threading en diverse standaardmodules zoals math, random en time.

Voor de distributie van het project is gekozen voor een gebruiksvriendelijke deployvorm: een zelfstandig 
uitvoerbaar .exe-bestand. Dit maakt het mogelijk het spel te gebruiken zonder Python-installatie, en biedt een 
professionele eindgebruikerervaring.

Deze analyse toont aan dat het gekozen ontwerp – gebaseerd op klassieke AI-technieken, optimalisaties en een 
responsieve grafische interface – een efficiënte en toegankelijke oplossing vormt voor een uitdagend real-time 
bordspel als Vier op een Rij.

voor een samenvatting van de werking van de code kun je gaan naar [Werking AI](../Software/WerkingAI.md)



⬅️ [Terug naar overzicht](../README.md#Inhoud)