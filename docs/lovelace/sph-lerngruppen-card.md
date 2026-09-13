# SPH Lerngruppen

Kartentyp: `custom:sph-lerngruppen-card`

## Funktion

Die Karte zeigt Leistungskontrollen aus dem SPH-Lerngruppen-Modul. Angezeigt werden Datum, Art, Fach/Kurs, Dauer, Schulstunden, Lehrkraft und Quelle.

Neben SPH-Daten können lokale Termine angelegt werden. Nur lokal erstellte Termine sind über die Karte löschbar.

## Screenshot

![SPH Lerngruppen – Leistungskontrollen](images/lernkontrollen.webp)

## Zeitzuordnung

Schulstunden wie `3`, `3,4` oder `3-4` werden im Backend normalisiert. Wenn der persönliche Stundenplan für diese Stunden Zeiten enthält, erzeugt das Modul zeitgebundene Kalendertermine; andernfalls bleibt der Termin ganztägig.

## School Hacks

Ein Schulprofil kann beispielsweise Lehrerkürzel auflösen:

```yaml
type: custom:sph-lerngruppen-card
entity: sensor.lerngruppen_maxim_mk
school-hacks: kfg
```

Allgemein: [School Hacks](school-hacks.md).

## Entity-Auswahl

1. `entity` oder `sensor`.
2. Bei `child`: passender `sensor.lerngruppen_*` über `kind_kürzel`.
3. Sonst erster passender strukturierter Lerngruppen-Sensor.

JSON-Sensoren mit `_json` werden nicht als Kartenquelle verwendet.

## Konfiguration

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-lerngruppen-card` |
| `title` | String | `Lerngruppen – Leistungskontrollen` | Kartentitel |
| `entity` | Entity-ID | automatisch | Strukturierter Lerngruppen-Sensor |
| `sensor` | Entity-ID | automatisch | Alias |
| `child` | String | leer | Kind/Kürzel |
| `school-hacks` | String/false | false | Optionales Schulprofil |

## Eigene Termine

`+ Termin hinzufügen` öffnet einen Dialog für:

- Datum
- Art
- Fach/Kurs
- optionale Dauer in Minuten
- optionale Schulstunden
- optionale Lehrkraft

Services:

```text
sph.lerngruppen_termin_hinzufuegen
sph.lerngruppen_termin_loeschen
```

Lokale Termine werden persistent gespeichert und mit SPH-Terminen zusammengeführt. Ein passender späterer SPH-Termin kann den lokalen Eintrag in der Anzeige verdrängen, ohne den lokalen Datensatz zu löschen.

## Hinweise

- Importierte SPH-Termine sind schreibgeschützt.
- Die Tabelle ist horizontal scrollbar.
- Dialogzustand, Eingabewerte, Fokus und Scrollposition werden bei Sensorupdates möglichst erhalten.
