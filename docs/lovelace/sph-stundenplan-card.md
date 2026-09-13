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

## Screenshot

![SPH Stundenplan – Wochenplan als Liste](images/wochenplan.webp)

## Vertretungsinformationen

Die Karte verwendet automatisch den zum Kind passenden internen `sensor.vertretungsplan_*`. Ein aktives Schul-Profil kann zusätzlich eine bevorzugte Vertretungsquelle definieren.

Mögliche Darstellungen:

- Entfall/Ausfall
- Vertretung
- Fachwechsel inklusive ursprünglichem Fach
- Raumänderung
- Vertretungslehrkraft
- Nachricht/Hinweise des Tages

Die Quellen-Priorität lautet:

1. explizite Kartenquelle über `vertretungsplan_sensor`, `vertretungsplan` oder `substitution_sensor`,
2. bevorzugte Quelle des aktiven Schul-Profils,
3. interner SPH-Vertretungsplan als Fallback.

Eine explizite Kartenquelle bleibt autoritativ.

## Schul-Profile

Das im Integrationseintrag ausgewählte Profil wird über das Sensorattribut `school_profile` automatisch erkannt.

Für Tests oder einen gezielten Override:

```yaml
type: custom:sph-stundenplan-card
entity: sensor.stundenplan_maxim_mk
school-profile: kfg
```

Mit `school-profile: false` kann die Profil-Darstellung für eine einzelne Karte deaktiviert werden.

Allgemeine Beschreibung: [Schul-Profile](../SCHOOL_PROFILES.md).

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
| `school-profile` | String/false | automatisch | Expliziter Schul-Profil-Override |
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

- Die Karte verändert keine Home-Assistant-State-Objekte.
- Das aktive Profil wird normalerweise aus dem Stundenplan-Sensor übernommen.
- Der interne Vertretungsplan wird anhand des Kindes ausgewählt; bei mehreren Integrationsinstanzen ist eine explizite Stundenplan-Entity empfehlenswert.
