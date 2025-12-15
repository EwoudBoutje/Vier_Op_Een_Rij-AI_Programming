

#  **Overzicht: hoe werkt de AI?**

De AI werkt in 5 fasen:

1. KILL-move check --> direct winnen?
2. BLOCK-move check --> meteen dreiging van de tegenstander blokkeren?
3. Minimax + Alpha-Beta pruning + iterative deepening
4. Transposition table --> vroeger berekende borden hergebruiken
5. Tijdslimiet --> AI stopt denken na X seconden

Alles gebeurt in `ai_thread_func()` en `minimax()`.

---

#  1. **KILLER MOVE (directe winst)**

In `ai_thread_func()`:

```python
for col in valid_moves:
    row = get_next_open_row(board_copy, col)
    board_copy[row][col] = my_piece
    if winning_move(board_copy, my_piece):
        result_container['col'] = col
        return
```


- De AI test elke kolom
-  Als ze ermee kan winnen → meteen die kolom spelen


---

#  2. **BLOCK MOVE (tegenstander blokkeren)**


```python
for col in valid_moves:
    row = get_next_open_row(...)
    board_copy[row][col] = opp_piece
    if winning_move(board_copy, opp_piece):
        result_container['col'] = col
        return
```


-  Als de mens in 1 zet kan winnen
-  Dan speelt de AI automatisch die blokkerende zet



---

#  3. **Minimax + Alpha-Beta + Iterative Deepening**

Als er geen directe winst of dreiging is, dan denkt de AI verder met minimax:

```python
for depth in range(1, limit + 1):
    col, score = minimax(...)
    if col is not None:
        best_col = col
    if score > INF // 2:
        break
```

###  iterative deepening:

* De AI begint met diepte = 1
* Dan diepte = 2
* Dan diepte = 3
* etc...

Tot de maximale diepte of tijdslimiet bereikt is.


---

#  **Minimax functie**

```python
col, score = minimax(board_copy, depth, alpha, beta, maximizingPlayer, ...)
```

In de functie gebeurt:

### a. Terminale borden checken

```python
if winning_move(board, piece): return score = +INF
if winning_move(board, opp): return score = -INF
```

### b. Heuristische evaluatie (score van het bord)

Komt uit:

```python
score_position(board, piece)
```

Deze functie kijkt naar alle "windows" van 4:

* AI 4-op-een-rij --> +100.000.000
* AI 3-open --> +10.000
* AI 2-open --> +500
* Tegenstander 3-open --> −800.000
* Tegenstander 2-open --> −10.000
* Center kolom bonus --> +200

Deze waarden worden opgeteld --> de evaluatiescore.

---

#  **c. Move ordering**

De code sorteert zetten:

```python
valid_locations.sort(key=lambda x: abs(x - COLUMNS//2))
```

Dit betekent:
-  AI bekijkt eerst zetten in het midden van het bord
-  Daarna pas de randen

Waarom?

* Middelste kolommen zijn veel sterker in vier op een rij
* Alpha-Beta pruning werkt beter wanneer goede zetten eerst komen

---

#  **d. Alpha-Beta Pruning**

De kern:

```python
if maximizingPlayer:
    value = -inf
    ...
    alpha = max(alpha, value)
    if alpha >= beta:
        break   # prune
else:
    value = +inf
    ...
    beta = min(beta, value)
    if alpha >= beta:
        break   # prune
```

Betekenis: Als een tak niet beter kan worden dan wat al gevonden is --> stop zoeken.


---

# 4. **Transposition Table (memoization)**

Bovenaan minimax:

```python
board_tuple = tuple(tuple(row) for row in board)
if board_tuple in memo:
    ...
    return cached value
```

Deze slaat borden op die de AI al eerder heeft gezien.

Vier op een rij bevat erg veel symmetrische en herhalende borden.

Dus Als de AI dezelfde configuratie later weer tegenkomt Hoeft ze niet opnieuw minimax uit te voeren en skippen we duizenden berekeningen.


---

#  5. **Tijdslimiet (time limit)**

In minimax:

```python
if time.time() - start_time > time_limit:
    return None, 0
```

En in de AI-thread:

* PvAI: AI heeft vast limiet (2.5 sec)
* AIvAI: limiet hangt af van slider (turbo ↔ traag)

- De AI stopt altijd binnen die tijd.
- Daarom bevriest de UI nooit.

---

#  **Hoe de AI uiteindelijk zijn zet kiest**

Volgorde:

1. Kan ik winnen?
   --> Speel die zet.

2. Kan de tegenstander winnen?
   --> Blokkeer.

3. Anders:
   --> Doe Minimax met alle optimalisaties
   --> Kies de *beste* move die gevonden werd
   --> Binnen tijdslimiet


