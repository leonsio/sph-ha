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

Die Karte verwendet automatisch den internen SPH-Vertretungsplan des Kindes. Ein aktives Schul-Profil kann zusätzlich eine bevorzugte Vertretungsquelle definieren.

Damit können Entfall, Vertretung, Fachwechsel, Raumänderung, Vertretungslehrkraft und Hinweise des tatsächlich ausgewählten Tages dargestellt werden.

Die Quellen-Priorität lautet:

1. explizite Kartenquelle über `vertretungsplan_sensor`, `vertretungsplan` oder `substitution_sensor`,
2. bevorzugte Quelle des aktiven Schul-Profils,
3. interner SPH-Vertretungsplan als Fallback.

Eine explizit gesetzte Vertretungsquelle bleibt autoritativ.

## Schul-Profile

Das im Integrationseintrag ausgewählte Profil wird über das Sensorattribut `school_profile` automatisch erkannt.

Für Tests oder einen gezielten Override:

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
school-profile: kfg
```

Mit `school-profile: false` kann die Profil-Darstellung für eine einzelne Karte deaktiviert werden.

Allgemein: [Schul-Profile](../SCHOOL_PROFILES.md).

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
| `school-profile` | String/false | automatisch | Expliziter Schul-Profil-Override |
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
