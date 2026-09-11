# KFG Stundenplan

Kartentyp: `custom:kfg-stundenplan-card`

## Funktionsweise

Die Karte erweitert den persönlichen SPH-Wochenstundenplan um KFG-spezifische Informationen. Sie zeigt Montag bis Freitag als Liste und berücksichtigt dabei die aktuelle A/B-Wochenkennung des Stundenplans.

Zusätzlich werden automatisch folgende KFG-Entities ausgewertet, sofern vorhanden:

- `sensor.vertretungsplan` für Vertretungen, Entfall, Tausch, Betreuung, Raumänderungen und Tagesnachrichten,
- `sensor.kfg_kollegium` zum Auflösen von Lehrerkürzeln,
- ein passender `sensor.schulkalender_*` für `Arbeiten` und `Klausuren`.

Vertretungsinformationen werden anhand von Klasse, Datum/Wochentag, Stunde und Fach dem regulären Unterricht zugeordnet. Änderungen werden farbig markiert; Entfall wird durchgestrichen dargestellt.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein Sensor mit passendem `kind_kürzel`.
3. Ohne `child`: `sensor.stundenplan`.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:kfg-stundenplan-card` |
| `title` | String | leer | Optionaler Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel` |

## Beispiel

```yaml
type: custom:kfg-stundenplan-card
title: KFG Stundenplan Maxim
entity: sensor.stundenplan_maxim_mk
```

Oder:

```yaml
type: custom:kfg-stundenplan-card
child: mk
```

## Dargestellte Änderungen

Unter anderem werden `Vertretung`, `Entfall`, `Tausch`, `Betreuung`, `Freistunde`, `Raumänderung`, `Statt-Vertretung`, `Pausenaufsicht`, `Sonderunterricht`, `Vertretung ohne Lehrer` und erkannte Fachwechsel farblich unterschieden.

## Hinweise

- Die KFG-Zusatzinformationen sind optional. Fehlen `sensor.vertretungsplan` oder `sensor.kfg_kollegium`, bleibt der normale SPH-Stundenplan weiterhin nutzbar.
- Tagesnachrichten aus dem Vertretungsplan werden beim jeweiligen Datum oberhalb der Unterrichtseinträge angezeigt.
- Kalender-Markierungen werden für `Arbeiten` und `Klausuren` eingeblendet.
- Die Karte ist schreibgeschützt.
