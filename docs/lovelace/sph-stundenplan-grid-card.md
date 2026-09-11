# SPH Stundenplan Raster

> Schulprofile: Normale SPH-Karten unterstützen `school-hacks: kfg`.
> [Konfiguration und Umstieg](school-hacks.md).


Kartentyp: `custom:sph-stundenplan-grid-card`

## Funktionsweise

Die Karte stellt den persönlichen Wochenstundenplan Montag bis Freitag als klassisches Tabellenraster dar. Zeilen entsprechen Unterrichtsstunden, Spalten den Wochentagen. Doppelstunden beziehungsweise längere Blöcke werden über mehrere Stundenzeilen zusammengefasst.

Die Zeitangaben der einzelnen Stunden werden aus Start, Ende und `duration` der vorhandenen Unterrichtseinträge abgeleitet. Mindestens acht Stundenzeilen werden dargestellt; bei späteren Stunden erweitert sich das Raster automatisch.

Passende Termine aus `sensor.schulkalender_*` der Arten `Arbeiten` und `Klausuren` werden in der jeweiligen Unterrichtszelle hervorgehoben.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein Sensor mit passendem Attribut `kind_kürzel`.
3. Ohne `child`: `sensor.stundenplan`.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-stundenplan-grid-card` |
| `title` | String | leer | Optionaler Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel`, z. B. `mk` |

## Beispiel

```yaml
type: custom:sph-stundenplan-grid-card
title: Wochenstundenplan
entity: sensor.stundenplan_maxim_mk
```

Oder über das Kind-Kürzel:

```yaml
type: custom:sph-stundenplan-grid-card
child: mk
```

## Darstellung im Sections-Dashboard

Die Karte meldet Home Assistant eigene Grid-Empfehlungen: volle Breite, mindestens 12 Spalten sowie mindestens 5 Zeilen. Auf schmalen Displays bleibt das Raster horizontal scrollbar.

## Hinweise

- Die Ansicht umfasst Montag bis Freitag.
- Kalender-Markierungen beziehen sich auf `Arbeiten` und `Klausuren`.
- Bei automatischer Kalendererkennung wird zunächst `sensor.schulkalender_maxim_mk` verwendet, falls vorhanden; andernfalls der erste passende `sensor.schulkalender_*`.
- Die Karte verändert keine Stundenplan- oder Kalendereinträge.
