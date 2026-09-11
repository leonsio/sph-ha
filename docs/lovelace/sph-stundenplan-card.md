# SPH Stundenplan

Kartentyp: `custom:sph-stundenplan-card`

## Funktionsweise

Die Karte zeigt den persönlichen Stundenplan Montag bis Freitag als Liste. Unterrichtseinträge mit identischer Start-/Endzeit werden als parallele Optionen zusammengefasst. Angezeigt werden Fach, Uhrzeit, Lehrkraft, Raum und A/B-Badges.

Zusätzlich sucht die Karte nach einem passenden `sensor.schulkalender_*` und blendet Termine der Arten `Arbeiten` und `Klausuren` an den zugehörigen Unterrichtsstunden ein. Die Zuordnung erfolgt über Datum und Fachbezeichnung; bei zeitlich begrenzten Kalendereinträgen kann außerdem die zeitliche Überlappung verwendet werden.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein Sensor mit passendem Attribut `kind_kürzel`.
3. Ohne `child`: `sensor.schulportal_hessen_stundenplan`.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-stundenplan-card` |
| `title` | String | leer | Optionaler Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel`, z. B. `mk` |

## Minimale Konfiguration

```yaml
type: custom:sph-stundenplan-card
```

## Empfohlene Konfiguration bei mehreren Kindern

```yaml
type: custom:sph-stundenplan-card
title: Stundenplan Maxim
child: mk
```

Oder vollständig explizit:

```yaml
type: custom:sph-stundenplan-card
entity: sensor.stundenplan_maxim_mk
title: Stundenplan Maxim
```

## Hinweise

- Es werden maximal die ersten fünf Tage aus `eigener_plan` dargestellt.
- Die Karte ist eine reine Anzeige; Stundenplaneinträge können nicht verändert werden.
- Kalender-Markierungen werden nur für `Arbeiten` und `Klausuren` dargestellt.
