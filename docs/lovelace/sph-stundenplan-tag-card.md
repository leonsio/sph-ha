# SPH Tagesstundenplan

> Schulprofile: Normale SPH-Karten unterstützen `school-hacks: kfg`.
> [Konfiguration und Umstieg](school-hacks.md).


Kartentyp: `custom:sph-stundenplan-tag-card`

## Funktionsweise

Die Karte zeigt genau einen Unterrichtstag. Während eines Schultags bleibt der aktuelle Tag sichtbar, solange die letzte Unterrichtsstunde noch nicht beendet ist. Nach Unterrichtsende sowie an Wochenenden oder unterrichtsfreien Tagen springt die Karte automatisch zum nächsten Tag mit Unterricht. Die Berechnung wird zusätzlich alle 30 Sekunden aktualisiert.

Angezeigt werden Uhrzeit, Fach, Lehrkraft, Raum und A/B-Badges. Passende Termine aus `sensor.schulkalender_*` der Arten `Arbeiten` und `Klausuren` werden direkt an der betreffenden Unterrichtsstunde markiert.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein Sensor mit passendem Attribut `kind_kürzel`.
3. Ohne `child`: `sensor.schulportal_hessen_stundenplan`.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-stundenplan-tag-card` |
| `title` | String | leer | Optionaler Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Stundenplan-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel`, z. B. `mk` |

## Beispiel

```yaml
type: custom:sph-stundenplan-tag-card
title: Nächster Unterrichtstag
child: mk
```

Explizite Entity:

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
```

## Hinweise

- Die Karte wählt selbstständig den aktuellen bzw. nächsten Unterrichtstag aus; ein fester Wochentag ist nicht konfigurierbar.
- Die Datumsanzeige verwendet derzeit das deutsche Format.
- Kalender-Markierungen werden nur für `Arbeiten` und `Klausuren` berücksichtigt.
- Stundenplaneinträge sind schreibgeschützt.
