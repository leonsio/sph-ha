# School Hacks

School Hacks ergänzen die allgemeinen SPH-Lovelace-Karten um schulabhängige Regeln. Sie sind **Profile**, keine eigenen Kartenvarianten.

Beispiel:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

## Ziel

Eine Schule kann eigene Regeln definieren, ohne `sph-*` Karten zu kopieren oder den allgemeinen Backend-Payload umzubauen.

Ein Schulprofil kann beispielsweise festlegen:

- A/B-Wochenlogik,
- Badge-Verhalten,
- automatische Wochenumschaltung,
- Lehrerauflösung,
- bevorzugte Vertretungsquelle,
- Übersetzung schulspezifischer Vertretungsarten,
- Verarbeitung von Hinweisen/Nachricht des Tages.

## Unterstützte Karten

Der Parameter `school-hacks` kann von den allgemeinen SPH-Karten verwendet werden, soweit die jeweilige Anpassung dort relevant ist. Besonders wichtig sind die drei Stundenplankarten:

- `custom:sph-stundenplan-card`
- `custom:sph-stundenplan-tag-card`
- `custom:sph-stundenplan-grid-card`

Weitere Karten können gemeinsame Funktionen wie Lehrerauflösung oder Beschreibungstransformation verwenden.

## Profil laden

Ein Profilname verweist auf:

```text
custom_components/sph/static/school-hacks/<name>.js
```

Beispiel:

```text
school-hacks: kfg
→ custom_components/sph/static/school-hacks/kfg.js
```

Zulässige Profilnamen bestehen aus Kleinbuchstaben, Ziffern, Bindestrich und Unterstrich.

Ein unbekanntes oder nicht ladbares Profil erzeugt einen sichtbaren Kartenfehler, statt unbemerkt mit falschen Annahmen weiterzulaufen.

## Allgemeine Vertretungsquellen-Priorität

Seit Version 0.5.0 ist die Quellwahl für Vertretungsdaten bewusst gestaffelt.

### Ohne School Hack

Allgemeine Stundenplankarten verwenden den zum Kind passenden internen SPH-Vertretungsplan:

```text
sensor.vertretungsplan_<kind>_<kürzel>
```

Der passende Sensor wird über die Attribute des Stundenplans (`kind`, `kind_kürzel`) zugeordnet.

### Mit School Hack

Für jede Unterrichtsstunde gilt:

1. **Explizite Kartenquelle** – `vertretungsplan_sensor`, `vertretungsplan` oder `substitution_sensor`.
2. **Bevorzugte Schulquelle** – aus der `substitution`-Konfiguration des aktiven Schulprofils.
3. **Interner SPH-Vertretungsplan** – Fallback, wenn die Profilquelle für diese konkrete Stunde keinen Treffer liefert.

Ein explizit gesetzter Sensor ist autoritativ. Wenn er nicht existiert, wird nicht stillschweigend auf eine andere schulische Quelle gewechselt.

Damit können School Hacks ihre eigene Datenquelle bevorzugen, während allgemeine SPH-Daten weiterhin als Fallback zur Verfügung stehen.

## Profilformat

Beispiel für eine weitere Schule:

```javascript
export default {
  weekBadges: ["A", "B"],
  unbadgedFallback: true,
  hideWeekBadges: true,
  gridWeekHeading: true,
  advanceWeekAfterFriday: true,
  teachers: {
    entity: "sensor.beispiel_kollegium",
    attribute: "lehrer",
    descriptionLabels: ["lehrer", "lehrkraft", "verantwortlich"]
  },
  substitution: {
    classPrefix: "sensor.beispiel_vertretungsplan_",
    fallback: "sensor.beispiel_vertretungsplan",
    news: true,
    labels: {
      Vertr: "Vertretung",
      Entf: "Entfall"
    }
  }
};
```

### Wochenoptionen

| Feld | Zweck |
|---|---|
| `weekBadges` | Gültige Wochenbadges, z. B. `A`, `B` |
| `unbadgedFallback` | Unmarkierte Gegenstunde verwenden, wenn keine passende markierte Stunde vorhanden ist |
| `hideWeekBadges` | Wochenbadge nicht direkt an jeder Stunde anzeigen |
| `gridWeekHeading` | Schulwoche einmalig oberhalb der Rasteransicht anzeigen |
| `advanceWeekAfterFriday` | Wochenansicht nach Ende der letzten Freitagsstunde auf nächste Woche schalten |

### Lehrerauflösung

```javascript
teachers: {
  entity: "sensor.beispiel_kollegium",
  attribute: "lehrer",
  descriptionLabels: ["lehrer", "lehrkraft"]
}
```

Die Auflösung erfolgt ohne Beachtung der Groß-/Kleinschreibung. Unbekannte Kürzel bleiben erhalten.

### Vertretungsquelle

```javascript
substitution: {
  classPrefix: "sensor.beispiel_vertretungsplan_",
  fallback: "sensor.beispiel_vertretungsplan",
  news: true,
  labels: { ... }
}
```

`classPrefix` ermöglicht eine klassenbezogene Primärquelle. Aus der Klasse `7n` wird beispielsweise:

```text
sensor.beispiel_vertretungsplan_7n
```

`fallback` wird verwendet, wenn keine klassenspezifische Profilquelle existiert.

`labels` übersetzt schulspezifische Kürzel in lesbare Bezeichnungen.

## Internes SPH-Vertretungsformat

Das allgemeine Backend-Modul verwendet ein eigenes normalisiertes Format mit Feldern wie:

- `datum`
- `klasse`
- `stunde` / `stunden`
- `fach`
- `fach_alt`
- `vertreter`
- `raum`
- `art`
- `art_lang`
- `entfall`

`static/substitution-adapter.js` verbindet dieses Format mit den Stundenplankarten.

School-Hack-Quellen dürfen ein eigenes Schema besitzen, solange der gemeinsame School-Hacks-Adapter dieses Schema unterstützt.

## Native Kalender

School Hacks sind Frontend-Profile. Sie werden **nicht** bei der serverseitigen Kalendererzeugung ausgeführt.

Der native Stundenplan-Kalender verwendet ausschließlich den internen SPH-Vertretungsplan. Dadurch bleiben Kalenderdaten deterministisch und unabhängig davon, welches Dashboard geöffnet ist.

## Neue Schule hinzufügen

Für eine neue Schule sind grundsätzlich folgende Schritte vorgesehen:

1. `custom_components/sph/static/school-hacks/<name>.js` anlegen.
2. Nur schulspezifische Einstellungen darin speichern.
3. Bei neuem Vertretungsschema den gemeinsamen Adapter erweitern, statt Karten zu kopieren.
4. Regressionstests für Profil und Datenquellen ergänzen.
5. `docs/schools/<name>/README.md` mit den schulbezogenen Besonderheiten anlegen.
6. Schule in `docs/schools/README.md` verlinken.

## Vorhandene Schulen

- [`kfg` – Kaiserin-Friedrich-Gymnasium Bad Homburg](../schools/kfg/README.md)

## Umstieg von alten KFG-Karten

Alte Kartentypen wie `custom:kfg-stundenplan-card` werden nicht mehr gepflegt.

Stattdessen:

```yaml
type: custom:sph-stundenplan-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

bzw. für Tages- und Rasteransicht die entsprechenden `custom:sph-*` Typen.

## Tests

Die Regressionstests decken insbesondere ab:

- Laden und Abschalten von Profilen,
- A/B-Gegenstücke,
- Lehrerauflösung,
- Profil-Vertretungsquelle,
- internen SPH-Fallback,
- explizite No-Fallback-Quelle,
- Datums-/Stunden-/Fachzuordnung,
- Renderer der Stundenplankarten.
