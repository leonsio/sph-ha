# SPH Kalender

Kartentyp: `custom:sph-kalender-card`

## Funktionsweise

Die Karte zeigt die von SPH-HA bereitgestellten Home-Assistant-Kalender in einer klassischen Kalenderansicht. Unterstützt werden Tag, Woche und Monat. Die Ansicht kann per YAML vorgegeben und anschließend direkt in der Karte umgeschaltet werden.

In Tag und Woche werden Ganztages- und tagesübergreifende Termine oberhalb der Stundenzeitleiste als Balken dargestellt. Zeitgebundene Termine erscheinen als positionierte Blöcke in der Zeitleiste; überlappende Termine werden nebeneinander angeordnet. Die Monatsansicht zeigt kompakte Terminblöcke pro Tag.

Die Karte verwendet `calendar/event/subscribe` und erhält Terminänderungen dadurch live über Home Assistants WebSocket-API.

## Automatische Kalenderauswahl

Ohne `calendars:` sucht die Karte verfügbare SPH-Kalender automatisch:

1. Existiert ein `calendar.sph_*`, wird nur der zusammengefasste SPH-Kalender verwendet.
2. Andernfalls werden `calendar.schulkalender_*`, `calendar.stundenplan_*` und `calendar.lerngruppen_*` gemeinsam verwendet.
3. `calendar.bewegliche_ferientage_*` wird bei der automatischen Auswahl nicht eingeblendet.

Bei mehreren Kindern kann `child` die Suche anhand von Entity-ID und Anzeigename eingrenzen.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-kalender-card` |
| `title` | String | `SPH Kalender` | Titel innerhalb der Karte |
| `view` | `day`, `week`, `month` | `week` | Startansicht |
| `date` | `YYYY-MM-DD` | heute | Anfangsdatum/Navigation-Ausgangspunkt |
| `locale` | String | `de-DE` | Locale für Datums-/Zeitformatierung |
| `child` | String | leer | Begrenzt automatisch gefundene Kalender auf ein Kind/Kürzel |
| `calendars` | Liste | automatisch | Explizite Kalenderliste; überschreibt die automatische Erkennung |
| `filters` | Objekt | leer | Dauerhafte YAML-Filter |
| `colors` | Objekt | interne Farben | Farben pro erkannter Quelle |
| `start_hour` | Zahl | `7`/automatisch erweitert | Früheste Stunde der Tag-/Wochenansicht |
| `end_hour` | Zahl | `18`/automatisch erweitert | Letzte Stunde der Tag-/Wochenansicht |
| `hour_height` | Zahl | `52` | Pixelhöhe pro Stunde; Minimum 36 |
| `month_max_events` | Zahl | `4` | Maximale direkt sichtbare Termine pro Tag in der Monatsansicht; Minimum 1 |

## Minimale Konfiguration

```yaml
type: custom:sph-kalender-card
view: week
```

Mit Kind-Auswahl:

```yaml
type: custom:sph-kalender-card
view: week
child: mk
```

## Kalender explizit konfigurieren

`calendars` kann Entity-IDs als String oder Objekte enthalten. Ein Objekt unterstützt `entity`, `name`, `color` und optional `source`.

```yaml
type: custom:sph-kalender-card
view: week
calendars:
  - entity: calendar.schulkalender_maxim_mk
    name: Schulkalender
    color: "#ef6c00"
    source: schulkalender
  - entity: calendar.stundenplan_maxim_mk
    name: Stundenplan
    color: "#1565c0"
    source: stundenplan
  - entity: calendar.lerngruppen_maxim_mk
    name: Lerngruppen
    color: "#7b1fa2"
    source: lerngruppen
```

Kurzform:

```yaml
calendars:
  - calendar.schulkalender_maxim_mk
  - calendar.stundenplan_maxim_mk
```

## YAML-Filter

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
```

Unter `filters` stehen zur Verfügung:

| Parameter | Wirkung |
|---|---|
| `calendars` | Nur Kalender/Quellen anzeigen, deren Entity-ID, Name oder Quelle einen Eintrag enthält |
| `include_calendars` | Alias für `calendars` |
| `exclude_calendars` | Passende Kalender/Quellen vollständig ausblenden |
| `include` | Nur Termine anzeigen, deren Titel, Beschreibung, Ort, Kalendername oder Quelle einen Suchtext enthält |
| `exclude` | Entsprechende Termine ausblenden |

Alle Textvergleiche erfolgen ohne Beachtung der Groß-/Kleinschreibung.

Zusätzlich zeigt die Karte bei mehreren vorhandenen Quellen interaktive Filter-Chips. Diese wirken nur auf die laufende Karteninstanz und ändern die YAML-Konfiguration nicht.

## Farben

Standardmäßig werden erkannte Quellen unterschiedlich eingefärbt. Sie können überschrieben werden:

```yaml
colors:
  stundenplan: "#1565c0"
  lerngruppen: "#7b1fa2"
  schulkalender: "#ef6c00"
  manuell: "#2e7d32"
  sph: "#00838f"
```

Bei expliziten `calendars` kann alternativ pro Kalender `color` gesetzt werden.

## Eigene Termine

Wenn ein ausgewählter SPH-Kalender die Home-Assistant-Features `CREATE_EVENT` und `DELETE_EVENT` unterstützt, aktiviert die Karte `+ Termin`.

Der Dialog unterstützt:

- Titel,
- Start- und Enddatum,
- Start- und Endzeit,
- Ganztag,
- mehrtägige Termine,
- Ort,
- Beschreibung.

Eigene Termine werden lokal von SPH-HA persistiert. In einem zusammengefassten `calendar.sph_*` werden sie gemeinsam mit Stundenplan-, Lerngruppen- und Schulkalenderterminen angezeigt. Nur lokale SPH-Termine können aus der Detailansicht gelöscht werden; importierte Termine bleiben schreibgeschützt.

Wiederholungsregeln werden für lokale SPH-Termine derzeit nicht unterstützt.

## Darstellungsbeispiel

```yaml
type: custom:sph-kalender-card
title: Schule
view: week
child: mk
start_hour: 7
end_hour: 19
hour_height: 54
month_max_events: 5
locale: de-DE
filters:
  exclude:
    - Schulwoche
colors:
  stundenplan: "#1565c0"
  lerngruppen: "#7b1fa2"
  schulkalender: "#ef6c00"
  manuell: "#2e7d32"
```

## Hinweise

- Fehlen `start_hour` oder `end_hour`, erweitert die Karte den Standardbereich automatisch, wenn sichtbare Termine außerhalb liegen.
- Die Monatsansicht enthält immer vollständige Montag-bis-Sonntag-Wochen und kann daher Tage des vorherigen oder nächsten Monats mit anzeigen.
- Navigation über Zurück, Heute und Weiter verändert nur die aktuelle Kartenansicht.
