# SPH Kalender Lovelace-Karte

Die Karte `custom:sph-kalender-card` zeigt die von SPH-HA bereitgestellten Kalender in einer klassischen Kalenderdarstellung. Sie unterstützt Tag, Woche und Monat. In der Tages- und Wochenansicht werden Ganztages- und tagesübergreifende Termine oberhalb der Zeitleiste dargestellt.

Die Integration registriert die JavaScript-Ressource automatisch. Nach einem Update von SPH-HA genügt daher in der Regel ein Neustart von Home Assistant und ein Neuladen des Browsers.

## Minimale Konfiguration

```yaml
type: custom:sph-kalender-card
view: week
```

`view` kann `day`, `week` oder `month` sein. Die Ansicht kann anschließend auch direkt in der Karte gewechselt werden.

Die Karte erkennt SPH-Kalender automatisch:

- Existiert ein zusammengefasster `calendar.sph_*`, wird nur dieser verwendet.
- Andernfalls werden `calendar.schulkalender_*`, `calendar.stundenplan_*` und `calendar.lerngruppen_*` gemeinsam angezeigt.
- Der technische Kalender `calendar.bewegliche_ferientage_*` wird bei der automatischen Auswahl nicht angezeigt.

Bei mehreren SPH-Konfigurationen kann die Auswahl mit `child` auf ein Kind/Kürzel eingegrenzt werden.

```yaml
type: custom:sph-kalender-card
view: week
child: mk
```

## Filter und Farben

Bei mehreren Quellen zeigt die Karte Filter-Schaltflächen an. Zusätzlich lassen sich Filter dauerhaft in YAML festlegen:

```yaml
type: custom:sph-kalender-card
view: week
filters:
  calendars:
    - stundenplan
    - lerngruppen
    - schulkalender
    - manuell
  exclude:
    - Schulwoche
colors:
  stundenplan: "#1565c0"
  lerngruppen: "#7b1fa2"
  schulkalender: "#ef6c00"
  manuell: "#2e7d32"
```

Unter `filters` stehen zur Verfügung:

- `calendars` bzw. `include_calendars`: nur passende Kalender/Quellen anzeigen.
- `exclude_calendars`: passende Kalender/Quellen ausblenden.
- `include`: nur Termine anzeigen, deren Titel, Beschreibung, Ort, Kalendername oder Quelle einen der Texte enthält.
- `exclude`: Termine ausblenden, deren Titel, Beschreibung, Ort, Kalendername oder Quelle einen der Texte enthält.

Die Vergleiche sind nicht von Groß-/Kleinschreibung abhängig.

## Kalender explizit festlegen

Die automatische Erkennung kann vollständig überschrieben werden:

```yaml
type: custom:sph-kalender-card
view: month
calendars:
  - entity: calendar.schulkalender_maxim_mk
    name: Schulkalender
    color: "#ef6c00"
  - entity: calendar.stundenplan_maxim_mk
    name: Stundenplan
    color: "#1565c0"
  - entity: calendar.lerngruppen_maxim_mk
    name: Lerngruppen
    color: "#7b1fa2"
```

Ein Listeneintrag kann alternativ nur aus der Entity-ID bestehen.

## Eigene Termine

Über `+ Termin` können lokale Termine erstellt werden. Unterstützt werden:

- Termine mit Start- und Endzeit,
- Ganztagstermine,
- mehrtägige Termine,
- Titel, Ort und Beschreibung.

Eigene Termine werden dauerhaft im SPH-HA-Speicher abgelegt und mit dem Schulportal-Kalender zusammengeführt. Nur solche lokal erstellten Termine können aus der Karte wieder gelöscht werden. Vom Schulportal, Stundenplan oder Lerngruppen-Modul gelieferte Termine bleiben schreibgeschützt.

Wiederholungsregeln werden für lokale SPH-Termine derzeit nicht unterstützt.

## Weitere Darstellungsparameter

```yaml
type: custom:sph-kalender-card
view: week
start_hour: 7
end_hour: 19
hour_height: 54
month_max_events: 5
locale: de-DE
```

Wenn `start_hour` oder `end_hour` fehlen, erweitert die Karte den sichtbaren Zeitbereich automatisch, falls Termine außerhalb des Standardbereichs liegen.
