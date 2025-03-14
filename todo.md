# 📌 To-Do List

## File System
- [x] **Correzione Bug del File System**
  - [x] Risolvere il caricamento ricorsivo delle sottocartelle all'apertura del progetto
  - [x] Gestire errori di rinomina (PermissionError, RecursionError, UnboundLocalError)
  - [x] Assicurare che le cartelle vuote siano gestite correttamente nel menu contestuale
- [x] **Test del File System**
  - [x] Verifica caricamento di progetti con struttura annidata
  - [x] Test della rinomina di file e cartelle (con aggiornamento icone)
  - [x] Test dell'aggiunta/eliminazione di file e cartelle
- [ ] **Ottimizzazioni del File System**
  - [ ] Implementare un sistema di caching per velocizzare il caricamento di progetti grandi
  - [ ] Aggiungere supporto per file nascosti opzionale (es. toggle per mostrare `.git`)
  - [x] Aggiungere un controllo per evitare nomi di file/cartelle duplicati

## Generale
- [x] **Creazione delle Icone (Parziale)**
  - [x] Icone base: `folder.png`, `html.png`, `css.png`, `file.png`, `js.png`
  - [ ] Creare icone aggiuntive per altri tipi di file (es. `.json`, `.png`, `.py`)
  - [ ] Migliorare la risoluzione delle icone (es. supportare 32x32 o temi dark/light)
- [x] **Implementazione Stile (Parziale)**
  - [x] Stile base per l'interfaccia (QSplitter, QTreeWidget)
  - [ ] Implementare un tema personalizzabile (es. chiaro/scuro)
  - [ ] Aggiungere stili per pulsanti e toolbar (es. hover effects)

## Design Workspace
- [ ] **Implementazione Design Workspace**
  - [ ] Creare un'area canvas per la visualizzazione grafica degli elementi HTML
  - [ ] Integrare il `design_view` come workspace interattivo
- [ ] **Aggiungere Sezione Elementi dell'HTML**
  - [ ] Creare una barra laterale con lista di elementi HTML (es. `<div>`, `<p>`, `<img>`)
  - [ ] Aggiungere icone e descrizioni per ogni elemento
- [ ] **Implementare il Drag and Drop degli Elementi**
  - [ ] Supportare il trascinamento dalla barra degli elementi al canvas
  - [ ] Gestire la nidificazione degli elementi (es. `<div>` dentro `<div>`)
- [ ] **Implementare il Ridimensionamento degli Elementi**
  - [ ] Aggiungere maniglie di ridimensionamento sugli elementi selezionati
  - [ ] Aggiornare le proprietà CSS (width, height) in tempo reale
- [ ] **Implementare il Movimento sulla Griglia degli Elementi**
  - [ ] Creare una griglia visibile opzionale nel canvas
  - [ ] Aggiungere snap-to-grid per il posizionamento preciso
- [ ] **Implementare gli Strumenti di Allineamento**
  - [ ] Aggiungere pulsanti per allineare elementi (es. sinistra, centro, destra)
  - [ ] Supportare l'allineamento multiplo di più elementi selezionati
- [ ] **Implementare il Menu delle Proprietà degli Elementi**
  - [ ] Creare un pannello delle proprietà (es. posizione, dimensioni, colori)
  - [ ] Aggiornare dinamicamente il pannello in base all'elemento selezionato

## Code Workspace
- [ ] **Implementazione Code Workspace**
  - [ ] Ottimizzare il `code_view` per diventare un editor di codice completo
  - [ ] Aggiungere supporto per più schede (multi-file editing)
- [ ] **Implementazione Indicizzazione delle Righe di Codice**
  - [ ] Mostrare numeri di riga a sinistra del `code_view`
  - [ ] Sincronizzare i numeri con lo scorrimento del testo
- [ ] **Implementazione dell'Auto Indent**
  - [ ] Aggiungere indentazione automatica dopo `{`, `<`, ecc.
  - [ ] Supportare la formattazione con tasto (es. Ctrl+Shift+F)
- [ ] **Implementazione degli Highlights del Codice (Keyword colorate)**
  - [ ] Evidenziare parole chiave HTML, CSS e JS con colori distinti
  - [ ] Usare una libreria di syntax highlighting (es. QTextCharFormat)
- [ ] **Implementazione Auto Completamento del Codice**
  - [ ] Suggerire tag HTML, proprietà CSS e funzioni JS durante la digitazione
  - [ ] Mostrare un menu a tendina con opzioni selezionabili

## Relazione Design-Code Workspace
- [ ] **Implementazione Modifiche in Tempo Reale da Design a Codice**
  - [ ] Tradurre modifiche grafiche (es. drag, resize) in codice HTML/CSS
  - [ ] Aggiornare il `code_view` senza sovrascrivere modifiche manuali
- [ ] **Implementazione Modifiche in Tempo Reale da Codice a Design**
  - [ ] Parsare il codice HTML/CSS dal `code_view` per aggiornare il canvas
  - [ ] Gestire conflitti tra modifiche manuali e grafiche

## Testing e Debug
- [ ] **Test di Stabilità**
  - [ ] Verificare il comportamento con progetti di grandi dimensioni
  - [ ] Testare tutti i comandi del menu contestuale su file e cartelle
- [ ] **Debug Avanzato**
  - [ ] Aggiungere log per tracciare errori (es. file di log opzionale)
  - [ ] Implementare un sistema di feedback per crash imprevisti

## Extra (Opzionale)
- [ ] **Supporto Multilingua**
  - [ ] Aggiungere traduzioni per menu e messaggi (es. italiano/inglese)
- [ ] **Esportazione Progetto**
  - [ ] Implementare un'opzione per esportare il progetto come ZIP
- [ ] **Integrazione con Git**
  - [ ] Aggiungere comandi base per il controllo di versione
