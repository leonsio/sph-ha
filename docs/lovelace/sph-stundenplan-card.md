# SPH Stundenplan

Kartentyp: `custom:sph-stundenplan-card`

## Funktion

Die Karte zeigt den persönlichen Stundenplan Montag bis Freitag als Liste. Einträge mit identischer Start-/Endzeit werden als parallele Optionen zusammengefasst.

Angezeigt werden unter anderem:

- Uhrzeit
- Fach
- Lehrkraft
- Raum
- Badges
- Kalenderhinweise für Arbeiten/Klausuren
- Vertretungsinformationen

## Vertretungsinformationen

Seit 0.5.0 verwendet die Karte ohne School Hack automatisch den zum Kind passenden internen `sensor.vertretungsplan_*`.

Mögliche Darstellungen:

- Entfall/Ausfall
- Vertretung
- Fachwechsel inklusive ursprünglichem Fach
- Raumänderung
- Vertretungslehrkraft
- Nachricht/Hinweise des Tages

Mit `school-hacks: <profil>` wird zuerst die bevorzugte Vertretungsquelle des Schulprofils verwendet. Falls sie für eine konkrete Stunde keinen Treffer liefert, kann der interne SPH-Vertretungsplan als Fallback dienen.

Eine explizite Kartenquelle über `vertretungsplan_sensor`, `vertretungsplan` oder `substitution_sensor` bleibt autoritativ.

## School Hacks

```yaml
type: custom:sph-stundenplan-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

Allgemeine Beschreibung: [School Hacks](school-hacks.md).

KFG: [Kaiserin-Friedrich-Gymnasium Bad Homburg](../schools/kfg/README.md).

## Kalender-Markierungen

Passende Termine aus `sensor.schulkalender_*` der Arten `Arbeiten` und `Klausuren` werden an der zugehörigen Unterrichtsstunde eingeblendet. Die Zuordnung erfolgt über Datum/Fach und bei zeitgebundenen Terminen zusätzlich über zeitliche Überlappung.

## Entity-Auswahl

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei `child`: passender Stundenplan über `kind_kürzel`.
3. Andernfalls automatische Stundenplan-Suche.

## Konfiguration

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-stundenplan-card` |
| `title` | String | leer | Kartentitel |
| `entity` | Entity-ID | automatisch | Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über Kind/Kürzel |
| `school-hacks` | String/false | false | Optionales Schulprofil |
| `vertretungsplan_sensor` | Entity-ID | automatisch | Explizite Vertretungsquelle |
| `vertretungsplan` | Entity-ID | automatisch | Alias |
| `substitution_sensor` | Entity-ID | automatisch | Alias |

## Beispiel

```yaml
type: custom:sph-stundenplan-card
entity: sensor.stundenplan_maxim_mk
title: Stundenplan Maxim
```

## Hinweise

- Die Karte verändert keine SPH-Daten.
- School Hacks wirken nur auf die Darstellung.
- Der interne Vertretungsplan wird anhand des Kindes ausgewählt; bei mehreren Integrationsinstanzen ist eine explizite Stundenplan-Entity empfehlenswert.
