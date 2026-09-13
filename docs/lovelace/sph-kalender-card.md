# SPH Kalender

Kartentyp: `custom:sph-kalender-card`

## Funktion

Die Karte zeigt die von SPH-HA bereitgestellten Home-Assistant-Kalender in Tag-, Wochen- oder Monatsansicht. Sie verwendet Home Assistants `calendar/event/subscribe` und erhält Terminänderungen live über WebSocket.

Unterstützt werden:

- Ganztagstermine
- zeitgebundene Termine
- mehrtägige Termine
- überlappende Termine
- mehrere SPH-Kalenderquellen
- lokale eigene Termine
- Filter und Quellfarben

## Vertretungen im Stundenplan-Kalender

Seit 0.5.0 werden Unterrichtstermine des nativen `calendar.stundenplan_*` serverseitig mit dem internen SPH-Vertretungsplan abgeglichen.

Dabei können Kalendertermine unter anderem enthalten bzw. widerspiegeln:

- Entfall/Ausfall
- Vertretungsart
- Fachwechsel
- ursprüngliches Fach
- Vertretungslehrkraft
- Raumänderung

Die UID des regulären Unterrichtstermins bleibt stabil. Eine Vertretung erzeugt daher nicht unnötig einen zweiten unabhängigen Stundenplaneintrag.

**Wichtig:** Diese Kalenderanpassung verwendet ausschließlich das interne SPH-Vertretungsplan-Modul. Frontend-School-Hacks und deren externe Vertretungsquellen werden nicht in der serverseitigen Kalendergenerierung ausgeführt.

## Automatische Kalenderauswahl

Ohne `calendars:` gilt:

1. Existiert ein `calendar.sph_*`, wird der zusammengefasste SPH-Kalender verwendet.
2. Andernfalls werden verfügbare `calendar.schulkalender_*`, `calendar.stundenplan_*` und `calendar.lerngruppen_*` verwendet.
3. `calendar.bewegliche_ferientage_*` wird nicht automatisch eingeblendet.

Bei mehreren Kindern kann `child` die Suche eingrenzen.

## Konfiguration

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-kalender-card` |
| `title` | String | `SPH Kalender` | Kartentitel |
| `view` | `day`, `week`, `month` | `week` | Startansicht |
| `date` | `YYYY-MM-DD` | heute | Navigationsdatum |
| `locale` | String | `de-DE` | Datums-/Zeitformat |
| `child` | String | leer | Kind/Kürzel für automatische Auswahl |
| `calendars` | Liste | automatisch | Explizite Kalenderquellen |
| `filters` | Objekt | leer | YAML-Filter |
| `colors` | Objekt | Standardfarben | Farben pro Quelle |
| `start_hour` | Zahl | `7`/automatisch | Frühester sichtbarer Stundenwert |
| `end_hour` | Zahl | `18`/automatisch | Letzter sichtbarer Stundenwert |
| `hour_height` | Zahl | `52` | Pixelhöhe pro Stunde |
| `month_max_events` | Zahl | `4` | Direkt sichtbare Termine pro Tag im Monat |
| `school-hacks` | String/false | false | Optionales Profil für reine Darstellungsanpassungen |

## Minimalbeispiel

```yaml
type: custom:sph-kalender-card
view: week
child: mk
```

## Explizite Kalenderquellen

```yaml
type: custom:sph-kalender-card
view: week
calendars:
  - entity: calendar.schulkalender_maxim_mk
    name: Schulkalender
    source: schulkalender
  - entity: calendar.stundenplan_maxim_mk
    name: Stundenplan
    source: stundenplan
  - entity: calendar.lerngruppen_maxim_mk
    name: Lerngruppen
    source: lerngruppen
```

Kurzform:

```yaml
calendars:
  - calendar.schulkalender_maxim_mk
  - calendar.stundenplan_maxim_mk
```

## Filter

```yaml
filters:
  calendars:
    - stundenplan
    - lerngruppen
    - schulkalender
    - manuell
  exclude:
    - Schulwoche
```

Unterstützt werden:

- `calendars` / `include_calendars`
- `exclude_calendars`
- `include`
- `exclude`

Textvergleiche erfolgen ohne Beachtung der Groß-/Kleinschreibung.

## Eigene Termine

Wenn die ausgewählte SPH-Kalenderquelle `CREATE_EVENT` und `DELETE_EVENT` unterstützt, zeigt die Karte `+ Termin` an.

Lokale Termine können Titel, Start/Ende, Ganztag, Ort und Beschreibung enthalten. Nur lokal angelegte SPH-Termine sind löschbar. Wiederholungsregeln werden derzeit nicht unterstützt.

## School Hacks

School Hacks können in der Kalenderkarte Darstellungsdetails beeinflussen, etwa die Auflösung beschrifteter Lehrerzeilen. Sie ändern **nicht** die serverseitigen Kalenderdaten.

Allgemein: [School Hacks](school-hacks.md).

## Hinweise

- Navigation in der Karte verändert nur die lokale Kartenansicht.
- Die Monatsansicht zeigt vollständige Montag-bis-Sonntag-Wochen.
- Sichtbare Quellen können zusätzlich über interaktive Filter-Chips ein-/ausgeblendet werden.
