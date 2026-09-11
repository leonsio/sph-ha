# KFG Stundenplan Raster

Kartentyp: `custom:kfg-stundenplan-grid-card`

## Funktionsweise

Die Karte stellt den persönlichen Stundenplan Montag bis Freitag als breites Raster dar und ergänzt die Zellen um KFG-Vertretungsinformationen. Zeilen entsprechen Unterrichtsstunden, Spalten den Wochentagen. Mehrstündige Blöcke werden zusammengefasst.

Automatisch ausgewertet werden:

- `sensor.vertretungsplan` für Vertretungen und sonstige Änderungen,
- `sensor.kfg_kollegium` zum Auflösen von Lehrerkürzeln,
- ein `sensor.schulkalender_*` für `Arbeiten` und `Klausuren`.

Die aktuelle A/B-Woche wird berücksichtigt. Änderungen werden aus Klasse, Datum, Stunde und Fach mit dem persönlichen Stundenplan abgeglichen und in der jeweiligen Rasterzelle dargestellt.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein Sensor mit passendem `kind_kürzel`.
3. Ohne `child`: `sensor.stundenplan`.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:kfg-stundenplan-grid-card` |
| `title` | String | leer | Optionaler Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel` |

## Beispiel

```yaml
type: custom:kfg-stundenplan-grid-card
title: KFG Wochenplan
entity: sensor.stundenplan_maxim_mk
```

Oder automatisch über das Kürzel:

```yaml
type: custom:kfg-stundenplan-grid-card
child: mk
```

## Darstellung

Die Karte unterscheidet unter anderem Vertretung, Entfall, Fachwechsel, Tausch, Betreuung, Freistunde, Raumänderung, Statt-Vertretung, Pausenaufsicht, Sonderunterricht und Vertretung ohne Lehrer. Arbeiten und Klausuren erhalten zusätzlich eine eigene Hervorhebung.

Für Sections-Dashboards meldet die Karte volle Breite, mindestens 12 Spalten und mindestens 5 Zeilen. Auf schmalen Geräten bleibt das Raster horizontal scrollbar.

## Hinweise

- Mindestens acht Unterrichtsstunden werden im Raster angelegt; bei späteren Stunden erweitert es sich automatisch.
- KFG-Zusatzsensoren sind optional. Ohne Vertretungsdaten bleibt der reguläre Stundenplan sichtbar.
- Die Karte verändert keine Daten.
