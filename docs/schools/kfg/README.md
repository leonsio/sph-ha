# KFG – Kaiserin-Friedrich-Gymnasium Bad Homburg

Dieses Dokument beschreibt ausschließlich die schulspezifischen Anpassungen für das Profil:

```yaml
school-hacks: kfg
```

Das Profil ist für das **Kaiserin-Friedrich-Gymnasium (KFG) in Bad Homburg** vorgesehen.

Allgemeine SPH-Funktionen und die technische School-Hacks-Architektur sind separat dokumentiert:

- [SPH-HA Hauptdokumentation](../../../README.md)
- [Allgemeine School-Hacks-Dokumentation](../../lovelace/school-hacks.md)

## Aktivierung

Die KFG-Anpassungen werden auf den normalen SPH-Karten aktiviert. Separate `custom:kfg-*` Karten werden nicht mehr verwendet.

### Wochenliste

```yaml
type: custom:sph-stundenplan-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

### Tagesansicht

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

### Rasteransicht

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

## Voraussetzungen

### SPH-Integration

Erforderlich ist ein normaler Stundenplan-Sensor des Kindes, beispielsweise:

```text
sensor.stundenplan_maxim_mk
```

Für die KFG-Regeln werden insbesondere folgende Attribute verwendet:

- `klasse`
- `wochenkennung`
- `wochenbeginn`
- `eigener_plan`
- `eigener_grundplan`
- `freie_tage`

### KFG-Kollegium

Für die Auflösung von Lehrerkürzeln erwartet das Profil:

```text
sensor.kfg_kollegium
```

Attribut:

```text
lehrer
```

Fehlt die Zuordnung für ein Kürzel, bleibt das vorhandene Kürzel erhalten.

### KFG-Vertretungsplan

Das Profil ist für die zusätzliche KFG-Vertretungsplan-Integration ausgelegt:

```text
https://github.com/leonsio/kfg-vertretungsplan
```

Bevorzugte Sensoren:

```text
sensor.vertretungsplan_<klasse>
sensor.vertretungsplan
```

Beispiel für Klasse `7n`:

```text
sensor.vertretungsplan_7n
```

## Priorität der Vertretungsdaten

Für KFG gilt in den Stundenplankarten:

1. Explizit in der Karte gesetzter `vertretungsplan_sensor` / `vertretungsplan` / `substitution_sensor`.
2. Klassenspezifischer KFG-Sensor `sensor.vertretungsplan_<klasse>`.
3. KFG-Fallback `sensor.vertretungsplan`.
4. Interner SPH-Vertretungsplan des Kindes, wenn die KFG-Quelle für die konkrete Stunde keinen Treffer liefert.

Damit bleibt der **KFG-Vertretungsplan die bevorzugte Quelle**. Der interne SPH-Vertretungsplan ergänzt nur fehlende Treffer.

Ein explizit konfigurierter Sensor bleibt autoritativ und löst keinen stillen automatischen Wechsel auf eine andere Quelle aus.

Beispiel:

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
vertretungsplan_sensor: sensor.vertretungsplan_7n
```

## A/B-Wochen

Das KFG-Profil verwendet:

```javascript
weekBadges: ["A", "B"]
unbadgedFallback: true
hideWeekBadges: true
```

### Gegenstück-Regel

Existieren für denselben Zeitslot eine A-/B-markierte und eine unmarkierte Variante, wird die zur Zielwoche passende markierte Stunde bevorzugt.

Beispiel:

```text
Woche A → A-Stunde sichtbar
Woche B → B-Stunde sichtbar
```

Eine unmarkierte Gegenstunde bleibt nur dann sichtbar, wenn für die Zielwoche keine passende markierte Variante den Slot ersetzt.

Andere Badges gelten nicht automatisch als Wochenkennzeichen.

### Anzeige der Wochenkennung

A/B-Badges werden beim KFG nicht an jeder Unterrichtsstunde wiederholt.

In der Rasteransicht erscheint stattdessen einmalig oberhalb der Tabelle rechtsbündig:

```text
Schulwoche A
```

bzw.

```text
Schulwoche B
```

## Wechsel auf die nächste Woche

Das Profil verwendet:

```javascript
advanceWeekAfterFriday: true
```

Wochenliste und Rasteransicht wechseln:

- am Freitag nach Ende der letzten für die aktuelle A/B-Woche aktiven Unterrichtsstunde auf die nächste Woche,
- am Samstag und Sonntag auf die kommende Woche.

Die A/B-Kennung wird dabei ebenfalls fortgeschrieben:

```text
A → B
B → A
```

Ein unterrichtsfreier Freitag kann bereits ab Freitag 00:00 zur Folgewoche führen. Fehlen gültige Endzeiten für aktive Freitagsstunden, erfolgt der sichere Wechsel erst am Samstag.

## Tagesansicht

Die Tageskarte verwendet den tatsächlich relevanten Schultag:

- während des Unterrichtstags den aktuellen Tag,
- nach Ende der letzten aktiven Stunde den nächsten Unterrichtstag,
- am Wochenende den nächsten Unterrichtstag,
- unterrichtsfreie Tage werden übersprungen.

A/B-Woche, Vertretungen und Nachricht des Tages beziehen sich immer auf das tatsächlich ausgewählte Datum.

## Lehrerauflösung

Das Profil verwendet:

```javascript
teachers: {
  entity: "sensor.kfg_kollegium",
  attribute: "lehrer"
}
```

Die Suche ist nicht von Groß-/Kleinschreibung abhängig.

Beispielsweise können `DRG`, `Drg` oder `drg` demselben Kollegiums-Eintrag zugeordnet werden.

Die Lehrerauflösung kann unter anderem verwendet werden in:

- Stundenplankarten,
- Lerngruppenkarte,
- Mein-Unterricht-Karte,
- beschrifteten Lehrerzeilen der SPH-Kalenderkarte.

## KFG-Vertretungsarten

Das Profil löst unter anderem folgende Kürzel auf:

| Kürzel | Darstellung |
|---|---|
| `Betr` | Betreuung |
| `Vertr` | Vertretung |
| `Entf` | Entfall |
| `Taus` | Tausch |
| `Freis` | Freistunde |
| `Raum` | Raumänderung |
| `Statt-Vertretung` | Statt-Vertretung |
| `Paus` | Pausenaufsicht |
| `SES` | Sonderunterricht |
| `Vtr. ohne Lehrer` | Vertretung ohne Lehrer |

## Vertretungszuordnung

Eine KFG-Vertretung wird nur auf eine passende persönliche Unterrichtsstunde angewendet.

Berücksichtigt werden insbesondere:

- Klasse,
- Datum,
- Schulstunde bzw. Stundenbereich,
- ursprüngliches Fach.

Damit werden Änderungen anderer Lerngruppen nicht pauschal auf das Kind übertragen.

### Entfall

Entfall, Ausfall oder Freistunde werden als ausgefallene Stunde dargestellt.

### Fachwechsel

Bei einem Fachwechsel wird das neue Fach angezeigt und das ursprüngliche Fach kann als `statt ...` erscheinen.

### Raumänderung

Ein neuer Raum ersetzt den regulären Stundenplanraum.

### Vertretungslehrkraft

Wenn ein Vertretungslehrer vorhanden ist, wird dessen Kürzel über `sensor.kfg_kollegium` aufgelöst, soweit eine Zuordnung vorhanden ist.

## Nachricht des Tages

Das KFG-Profil aktiviert:

```javascript
news: true
```

Nachrichten aus dem KFG-Vertretungsplan werden anhand von **Datum und Wochentag** dem dargestellten Tag zugeordnet. Dadurch wird nicht versehentlich die Nachricht eines gleichnamigen Wochentags aus einer anderen Woche verwendet.

Wenn die bevorzugte KFG-Quelle keine passende Nachricht liefert, kann die allgemeine Stundenplankarte auf Hinweise des internen SPH-Vertretungsplans zurückfallen.

## Native Kalender

Die KFG-School-Hacks wirken ausschließlich im Frontend.

Der native:

```text
calendar.stundenplan_<kind>_<kürzel>
```

verwendet **nicht** die KFG-Vertretungsplan-Sensoren. Für serverseitig generierte Kalendertermine wird ausschließlich der interne SPH-Vertretungsplan verwendet.

Das verhindert, dass die Kalenderinhalte davon abhängen, welche Lovelace-Karte oder welches Schulprofil gerade geöffnet ist.

## Profilkonfiguration

Die aktuelle Profilimplementierung liegt unter:

```text
custom_components/sph/static/school-hacks/kfg.js
```

Schulspezifische Änderungen sollen ausschließlich dort bzw. im gemeinsamen Adapter vorgenommen werden. Neue separate KFG-Karten sollen nicht wieder eingeführt werden.

## Fehler- und Fallback-Verhalten

- Fehlt `sensor.kfg_kollegium`, bleiben Lehrerkürzel erhalten.
- Fehlt die klassenspezifische KFG-Vertretungsquelle, wird der KFG-Fallback geprüft.
- Liefert die KFG-Quelle keinen Treffer für eine konkrete Stunde, kann der interne SPH-Vertretungsplan ergänzen.
- Ein explizit konfigurierter, aber fehlender Vertretungssensor wird nicht automatisch ersetzt.
- Ohne Vertretungsdaten bleibt der reguläre SPH-Stundenplan sichtbar.
