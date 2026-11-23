# SPH Nachrichten

Kartentyp: `custom:sph-nachrichten-card`

Die Karte zeigt die Nachrichten aus dem Posteingang des Schulportals. Standardmäßig werden nur ungelesene Unterhaltungen angezeigt.

## Darstellung

Angezeigt werden je Unterhaltung:

- Betreff (ungelesene hervorgehoben)
- Absender
- Datum (`heute`, `gestern` oder Datum)

Kopfzeile und Zähler zeigen die Anzahl ungelesener Unterhaltungen, die Fußzeile Datum und Uhrzeit des letzten Abrufs. Vor dem ersten Abruf nach einem Neustart zeigt die Karte „Noch kein Abruf erfolgt.“ Ein Klick auf eine Nachricht oder auf **Im Schulportal öffnen** öffnet den Posteingang des Schulportals in einem neuen Tab. Den Nachrichtentext zeigt die Karte nicht an.

## Beispiel

```yaml
type: custom:sph-nachrichten-card
entity: sensor.nachrichten_ungelesen_maxim_mk
```

Alternativ:

```yaml
type: custom:sph-nachrichten-card
child: mk
show_read: true
max: 5
```

## Optionen

| Option | Standard | Wirkung |
|---|---|---|
| `entity` / `sensor` | automatisch | Expliziter Nachrichtensensor `sensor.nachrichten_ungelesen_*` |
| `child` | leer | Kindname oder Kürzel für automatische Sensorwahl |
| `title` | `Nachrichten <Kind>` | Kartenüberschrift |
| `show_read` | `false` | Auch gelesene Unterhaltungen anzeigen |
| `max` | `10` | Maximale Anzahl angezeigter Unterhaltungen |

## Datenquelle

Betreff, Absender und Datum stehen bewusst nicht in den Sensorattributen, damit der Sensor sie nicht in die Recorder-Datenbank schreibt. Die Karte lädt sie über den WebSocket-Befehl `sph/nachrichten` und aktualisiert sich, sobald sich der Sensor nach einem Abruf ändert.
