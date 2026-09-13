# SPH Tagesstundenplan

Kartentyp: `custom:sph-stundenplan-tag-card`

## Funktion

Die Karte zeigt genau einen relevanten Unterrichtstag. Während eines Schultags bleibt der aktuelle Tag sichtbar, solange die letzte aktive Unterrichtsstunde noch nicht beendet ist. Danach sowie an Wochenenden oder unterrichtsfreien Tagen wird automatisch der nächste Unterrichtstag gewählt.

Die zeitabhängige Auswahl wird regelmäßig aktualisiert.

Angezeigt werden:

- Datum
- Uhrzeit
- Fach
- Lehrkraft
- Raum
- Badges
- Arbeiten/Klausuren aus dem Schulkalender
- Vertretungsinformationen

## Screenshot

![SPH Tagesstundenplan](images/tagesplan.webp)

## Vertretungen

Ohne School Hack verwendet die Karte automatisch den internen SPH-Vertretungsplan des Kindes.

Damit können Entfall, Vertretung, Fachwechsel, Raumänderung, Vertretungslehrkraft und Hinweise des tatsächlich ausgewählten Tages dargestellt werden.

Mit `school-hacks: <profil>` wird zuerst die schulische Profilquelle verwendet. Der interne SPH-Vertretungsplan dient als Fallback, sofern die Profilquelle für die konkrete Stunde keinen Treffer liefert.

Eine explizit gesetzte Vertretungsquelle bleibt autoritativ.

## School Hacks

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

Allgemein: [School Hacks](school-hacks.md).

KFG: [Kaiserin-Friedrich-Gymnasium Bad Homburg](../schools/kfg/README.md).

## Entity-Auswahl

1. `entity` oder `sensor`.
2. `child` über `kind_kürzel`.
3. automatische Stundenplan-Suche.

## Konfiguration

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-stundenplan-tag-card` |
| `title` | String | leer | Kartentitel |
| `entity` | Entity-ID | automatisch | Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias |
| `child` | String | leer | Kind/Kürzel |
| `school-hacks` | String/false | false | Optionales Schulprofil |
| `vertretungsplan_sensor` | Entity-ID | automatisch | Explizite Vertretungsquelle |
| `vertretungsplan` | Entity-ID | automatisch | Alias |
| `substitution_sensor` | Entity-ID | automatisch | Alias |

## Beispiel

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
title: Nächster Unterrichtstag
```

## Hinweise

- Ein fester Wochentag ist nicht konfigurierbar; die Karte wählt den relevanten Tag selbst.
- Unterrichtsfreie Tage aus dem Stundenplan werden übersprungen.
- Die Nachricht des Tages wird für das tatsächlich dargestellte Datum ausgewählt.
- Stundenplaneinträge sind schreibgeschützt.
