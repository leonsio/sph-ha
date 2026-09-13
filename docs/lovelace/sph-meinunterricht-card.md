# SPH Mein Unterricht

Kartentyp: `custom:sph-meinunterricht-card`

## Funktion

Die Karte zeigt Hausaufgaben aus dem Modul **Mein Unterricht** tabellarisch. Angezeigt werden unter anderem Datum, Fach/Kurs, Thema, Aufgabe, Lehrkraft, Status und Quelle.

Lokale Hausaufgaben können direkt über die Karte angelegt und wieder gelöscht werden. Vom Schulportal geladene Einträge bleiben schreibgeschützt.

## Kurs- und Fachnormalisierung

Kursnamen werden bereits im Backend auf gemeinsame Fachbezeichnungen normalisiert.

Beispiele:

```text
D 05cG        → Deutsch
Deutsch 7n    → Deutsch
M 05cG        → Mathematik
Biologie 05cg → Biologie
```

Klassenbestandteile werden entfernt, bekannte Kürzel ausgeschrieben und der ursprüngliche Kursname bleibt im Feld `kurs` erhalten.

Normaler Sensor und JSON-Sensor enthalten zusätzlich:

- `faecher`
- `faecher_gesamt`
- `faecher_offen`

Die Karte selbst bleibt primär eine Aufgabenansicht; die Fachübersicht steht für weitere Dashboards und Automationen im Sensor zur Verfügung.

## Schul-Profile

Das pro Kind ausgewählte Schul-Profil wird bereits serverseitig auf den Sensor- und JSON-Payload angewandt. Dadurch können beispielsweise schulspezifische Fach- oder Lehrernamen direkt in den veröffentlichten Daten erscheinen.

Die Karte erkennt das Profil zusätzlich über `school_profile`. Für Tests oder einen gezielten Darstellungs-Override kann verwendet werden:

```yaml
type: custom:sph-meinunterricht-card
entity: sensor.mein_unterricht_maxim_mk
school-profile: kfg
```

Mit `school-profile: false` kann die Profil-Darstellung einer einzelnen Karte deaktiviert werden.

Allgemein: [Schul-Profile](../SCHOOL_PROFILES.md).

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
| `school-profile` | String/false | automatisch | Expliziter Schul-Profil-Override |

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
