# SPH Mein Unterricht

Kartentyp: `custom:sph-meinunterricht-card`

## Funktion

Die Karte zeigt Hausaufgaben aus dem Modul **Mein Unterricht** tabellarisch. Angezeigt werden unter anderem Datum, Fach/Kurs, Thema, Aufgabe, Lehrkraft, Status und Quelle.

Lokale Hausaufgaben können direkt über die Karte angelegt und wieder gelöscht werden. Vom Schulportal geladene Einträge bleiben schreibgeschützt.

## Kurs- und Fachnormalisierung

Seit 0.5.0 werden Kursnamen bereits im Backend auf gemeinsame Fachbezeichnungen normalisiert.

Beispiele:

```text
D 05cG      → Deutsch
Deutsch 7n  → Deutsch
M 05cG      → Mathematik
Biologie 05cg → Biologie
```

Klassenbestandteile werden entfernt, bekannte Kürzel ausgeschrieben und der ursprüngliche Kursname bleibt im Feld `kurs` erhalten.

Normaler Sensor und JSON-Sensor enthalten zusätzlich:

- `faecher`
- `faecher_gesamt`
- `faecher_offen`

Die Karte selbst bleibt primär eine Aufgabenansicht; die Fachübersicht steht für weitere Dashboards und Automationen im Sensor zur Verfügung.

## School Hacks

Ein Schulprofil kann beispielsweise Lehrerkürzel auflösen:

```yaml
type: custom:sph-meinunterricht-card
entity: sensor.mein_unterricht_maxim_mk
school-hacks: kfg
```

Allgemein: [School Hacks](school-hacks.md).

## Entity-Auswahl

1. `entity` oder `sensor`.
2. Bei `child`: passender `sensor.mein_unterricht_*` über `kind_kürzel`.
3. Sonst erster passender strukturierter Mein-Unterricht-Sensor.

JSON-Sensoren mit `_json` werden nicht als Kartenquelle gewählt.

## Konfiguration

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-meinunterricht-card` |
| `title` | String | `Mein Unterricht – Hausaufgaben` | Kartentitel |
| `entity` | Entity-ID | automatisch | Strukturierter Mein-Unterricht-Sensor |
| `sensor` | Entity-ID | automatisch | Alias |
| `child` | String | leer | Kind/Kürzel |
| `school-hacks` | String/false | false | Optionales Schulprofil |

## Eigene Hausaufgaben

`+ Hausaufgabe hinzufügen` öffnet einen Dialog für:

- Datum
- Fach
- optionalen Kurs
- optionale Lehrkraft
- optionales Thema
- Aufgabe
- Erledigt-Status

Services:

```text
sph.meinunterricht_hausaufgabe_hinzufuegen
sph.meinunterricht_hausaufgabe_loeschen
```

Manuelle Hausaufgaben werden persistent gespeichert und sieben Tage nach dem eingetragenen Aufgabendatum automatisch bereinigt.

## Hinweise

- SPH-Einträge sind schreibgeschützt.
- Manuelle Einträge werden als Quelle `Manuell` gekennzeichnet.
- Die Tabelle ist horizontal scrollbar.
- Dialoginhalt, Fokus und Scrollposition werden bei Sensorupdates möglichst erhalten.
