# KFG Tagesstundenplan

Kartentyp: `custom:kfg-stundenplan-tag-card`

## Funktionsweise

Die Karte zeigt den aktuellen oder nächsten Unterrichtstag und ergänzt ihn um KFG-Vertretungsinformationen. Während eines Schultags bleibt der aktuelle Tag sichtbar, solange die letzte Unterrichtsstunde noch läuft. Danach sowie an Wochenenden oder unterrichtsfreien Tagen wird zum nächsten Unterrichtstag gewechselt. Die Auswahl wird alle 30 Sekunden neu berechnet.

Automatisch ausgewertet werden:

- `sensor.vertretungsplan` für Änderungen und Tagesnachrichten,
- `sensor.kfg_kollegium` zum Auflösen von Lehrerkürzeln,
- ein passender `sensor.schulkalender_*` für `Arbeiten` und `Klausuren`.

Die Karte berücksichtigt die A/B-Wochenkennung des Stundenplans. Vertretungen werden anhand von Klasse, Datum, Stunde und Fach zugeordnet und farbig hervorgehoben.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein Sensor mit passendem `kind_kürzel`.
3. Ohne `child`: `sensor.stundenplan`.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:kfg-stundenplan-tag-card` |
| `title` | String | leer | Optionaler Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel` |

## Beispiel

```yaml
type: custom:kfg-stundenplan-tag-card
title: Heute am KFG
child: mk
```

Explizit:

```yaml
type: custom:kfg-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
```

## Zusätzliche Darstellung

- A/B-Woche im Datumskopf
- Nachricht des Tages aus dem Vertretungsplan
- farbige Badges für Vertretung, Entfall, Raumänderung, Betreuung, Fachwechsel und weitere KFG-Arten
- Markierungen für Arbeiten und Klausuren aus dem SPH-Schulkalender

## Hinweise

- Die KFG-Zusatzsensoren sind optional; ohne sie arbeitet die Karte als Tagesstundenplan weiter.
- Ein bestimmter Tag kann nicht per YAML erzwungen werden; die Karte entscheidet anhand von Datum, Unterricht und Uhrzeit.
- Die Karte ist schreibgeschützt.
