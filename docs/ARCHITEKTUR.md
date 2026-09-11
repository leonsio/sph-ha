# Schulportal Hessen – Architektur

> Stand Schulprofile: KFG-Anpassungen werden über `school-hacks: kfg` in normalen
> SPH-Karten aktiviert. Die Datei `static/school-hacks/kfg.js` enthält das Schulprofil,
> `static/school-hacks.js` die gemeinsame Logik. Die alten KFG-Karten und ihre
> Kompatibilitätsschicht wurden vollständig entfernt.
> Neue Schulanpassungen in Profilen pflegen, keine eigenen Kartenkopien anlegen.
> Details: [Schulprofile](lovelace/school-hacks.md).


Die Home-Assistant-Integration ist modular aufgebaut. Gemeinsame technische Funktionen liegen unter `api/`. Fachliche Funktionen werden in den jeweiligen Modulen unter `module/` gekapselt. Der aktuelle Stand dieser Dokumentation entspricht Version **0.4.18**.

## Quelltextstruktur

```text
custom_components/sph/
├── __init__.py
├── calendar.py
├── config_flow.py
├── const.py
├── coordinator.py
├── sensor.py
├── services.yaml
├── api/
│   ├── __init__.py
│   └── client.py
├── module/
│   ├── stundenplan/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   ├── calendar.py
│   │   ├── movable_holidays.py
│   │   └── sensor.py
│   ├── kalender/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   └── sensor.py
│   ├── meinunterricht/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   └── sensor.py
│   └── lerngruppen/
│       ├── __init__.py
│       ├── client.py
│       ├── coordinator.py
│       ├── calendar.py
│       ├── sensor.py
│       ├── services.py
│       └── storage.py
├── static/
│   ├── sph-stundenplan-card.js
│   ├── sph-stundenplan-tag-card.js
│   ├── sph-stundenplan-grid-card.js
│   ├── sph-lerngruppen-card.js
│   ├── school-hacks.js
│   └── school-hacks/
│       └── kfg.js
└── translations/
```

## Integrationsebene

Die Dateien direkt unter `custom_components/sph/` bilden die Home-Assistant-Ebene:

- `__init__.py` – Initialisierung, Aufbau der gemeinsamen Laufzeitdaten, Registrierung der Lovelace-Ressourcen, Entity-ID-Migrationen sowie Start/Stop zusätzlicher Hintergrundlogik.
- `config_flow.py` – Einrichtung und Options-Flow.
- `const.py` – integrationsweite Konstanten und Standardwerte.
- `sensor.py` – Dispatcher für die Sensoren der fachlichen Module.
- `calendar.py` – Dispatcher für native Home-Assistant-Kalender.
- `coordinator.py` – Kompatibilitätsschicht für ältere Stundenplan-Imports.

Die Lovelace-Ressourcen werden automatisch mit versionierten URLs registriert. `add_extra_js_url()` wird absichtlich nicht verwendet, um doppelte Custom-Element-Registrierungen zu vermeiden.

## `api/` – gemeinsame technische Funktionen

`api/` enthält technische Funktionen, die mehrere Module verwenden:

- Authentifizierung beim Schulportal Hessen.
- gemeinsame Session-Verwaltung.
- Login-/Session-Erneuerung.
- HTTP-Kommunikation mit SPH.

Die Module teilen sich eine authentifizierte `SphAuthClient`-Instanz. Eine abgelaufene Session wird erneuert und der ursprüngliche Abruf erneut versucht.

## Modulaktivierung

In der Konfiguration gibt es eine Mehrfachauswahl **Aktive Module** für:

- Stundenplan
- Schulkalender
- Mein Unterricht
- Lerngruppen

Intern werden aus Kompatibilitätsgründen weiterhin die bisherigen booleschen Schlüssel gespeichert. Deaktivierte Module sollen keine unnötigen HTTP-Abrufe durchführen.

Beim Schulkalender gilt zusätzlich: Wird das Modul deaktiviert, werden seine Sensor- und Kalender-Entities aus der Entity Registry entfernt. Die anderen Module behalten bei Deaktivierung ihre bisherigen leeren/ruhenden Entities.

## `module/stundenplan/`

Das Stundenplan-Modul verarbeitet `stundenplan.php`.

### Datenmodell

Der Client liefert unter anderem:

```python
{
    "week_badge": ...,
    "all": [...],
    "own": [...],
    "klasse": ...,
}
```

Jede Unterrichtsstunde enthält typischerweise:

- `day`
- `subject`
- `teacher`
- `room`
- `badge`
- `duration`
- `start`
- `end`
- `index`

### Sensor-Ausgabe

Es existieren:

- `sensor.stundenplan_<kind>`
- `sensor.stundenplan_<kind>_json`

Der persönliche Plan bleibt immer unter `eigener_plan` erhalten. Der Legacy-Block `tage` bleibt aus Kompatibilitätsgründen bestehen.

Konfigurationsoption **Stundenplan-Ausgabe**:

- `own` – nur `eigener_plan` wird befüllt; `tage` bleibt strukturell vorhanden, aber inhaltlich leer.
- `all` – zusätzlich wird der vollständige SPH-Stundenplan in `tage` ausgegeben.

Beispielstruktur:

```yaml
kind: Maxim
kind_kürzel: Mk
klasse: 7n
wochenkennung: A
tage:
  - []
  - []
  - []
  - []
  - []
eigener_plan:
  - [...]
  - [...]
  - [...]
  - [...]
  - [...]
freie_tage:
  - "2026-10-03"
freie_tage_kalender: calendar.deutschland_he
```

Der JSON-Sensor stellt denselben Payload kompakt im Attribut `json` bereit.

### Native Stundenplan-Kalender

Entity:

- `calendar.stundenplan_<kind>`

Der Kalender wird dynamisch aus dem aktuellen Wochenstundenplan erzeugt und materialisiert keine dauerhaften Termine.

Zeitfenster:

- 2 Wochen Vergangenheit
- 8 Wochen Zukunft

Dadurch verschwinden ältere Termine automatisch, sobald sie außerhalb dieses Fensters liegen.

A/B-Wochen werden aus der aktuellen SPH-Wochenkennung fortgeschrieben. Die Auswahl der Stunden folgt den gleichen Gegenstück-Regeln wie das KFG-Schulprofil.

Neben Unterrichtsstunden wird pro tatsächlichem Schultag ein ganztägiger Eintrag `Schulwoche A` bzw. `Schulwoche B` erzeugt.

Ganztägige Events (`date`) und Unterrichtsevents (`datetime`) werden vor der Sortierung auf timezone-aware `datetime` normalisiert.

## Freie Tage im Stundenplan

Freie Tage werden zentral im Stundenplan-Coordinator geführt und für Kalender sowie Sensoren verwendet.

### `calendar.deutschland_he`

Wenn `calendar.deutschland_he` existiert, wird dieser Kalender über `calendar.get_events` ausgewertet.

Jeder Tag mit mindestens einem Eintrag gilt als schulfrei. Für diesen Tag werden unterdrückt:

- Unterrichtsstunden im nativen Stundenplan-Kalender.
- `Schulwoche A/B`.
- Unterrichtsdaten im Sensor-Payload der aktuell dargestellten Schulwoche.

Die Freie-Tage-Prüfung ist vom SPH-Polling entkoppelt:

- zusätzlicher Retry kurz nach dem Start,
- Reaktion auf State-Änderungen von `calendar.deutschland_he`,
- periodische Kontrolle alle 15 Minuten.

Wenn sich nur die Liste der freien Tage ändert, werden die vorhandenen Stundenplandaten neu veröffentlicht, ohne `stundenplan.php` erneut abzurufen.

### Bewegliche Ferientage

Datei:

- `module/stundenplan/movable_holidays.py`

Quelle:

- `https://schulaemter.hessen.de/schulbesuch/bewegliche-ferientage`

In der Konfiguration wird ein statisch hinterlegter Schulamtsbezirk ausgewählt. Die Bezirksliste wird nicht bei jedem Start aus dem Internet geladen.

Die Webseite weist bewegliche Ferientage je **Schuljahr** und **Schulamtsbezirk** aus. Es werden ausschließlich die Termine des ausgewählten Bezirks für das aktuell relevante Schuljahr übernommen.

Die Daten werden persistent lokal gespeichert. Gespeichert werden nur die für SPH relevanten Informationen, insbesondere:

```yaml
district: Bad Vilbel
school_year: 2026/2027
events:
  - date: "2027-02-08"
    summary: Rosenmontag
```

Nicht benötigte Inhalte und andere Bezirke werden verworfen.

Die Online-Quelle wird nur einmal täglich aktualisiert. Bei HTTP-Fehler, Parserfehler oder leerer Antwort bleiben die zuletzt erfolgreich gespeicherten Daten erhalten.

Die Termine werden über einen eigenen nativen Home-Assistant-Kalender bereitgestellt:

- `calendar.bewegliche_ferientage_<kind>`

Dieser Kalender wird vom Stundenplan genauso als Freie-Tage-Quelle verwendet wie `calendar.deutschland_he`.

Die Schulbezirksnamen werden als echte Werte gespeichert. Da Namen wie `Bad Vilbel` oder `Gießen` keine gültigen Home-Assistant-Translationsschlüssel sind, verwendet der Config Flow für diese Auswahl explizite `value`/`label`-Paare statt eines `translation_key`.

## `module/kalender/`

Das Modul kapselt den SPH-Schulkalender.

- `client.py` – Abruf und Parsing.
- `coordinator.py` – DataUpdateCoordinator.
- `sensor.py` – strukturierter und JSON-Sensor.

Bevorzugte Quelle ist der CSV-Export von `kalender.php`, mit iCal-Fallback.

Normalisierte Felder:

- `start`
- `end`
- `all_day`
- `summary`
- `description`
- `location`
- `art`
- `verantwortlich`
- `uid`

Der Coordinator begrenzt auf das aktuell relevante hessische Schuljahr.

### Kalenderarten-Filter

`calendar_event_types` ist optional.

- leer / `[]` = keine Filterung, alle SPH-Kalendereinträge übernehmen.
- befüllt = nur die angegebenen Kategorien übernehmen.

Mehrere Werte können komma-, semikolon- oder zeilengetrennt angegeben werden.

### Entities

- `sensor.schulkalender_<kind>`
- `sensor.schulkalender_<kind>_json`
- `calendar.schulkalender_<kind>`

Der Legacy-Sensor begrenzt seine Termin-Vorschau; der JSON-Sensor enthält die vollständigen gefilterten Daten. Große JSON-Attribute können die Recorder-Grenze von Home Assistant überschreiten und werden dann nicht historisiert.

## `module/meinunterricht/`

Das Modul verarbeitet `meinunterricht.php` und stellt aktuelle Unterrichts-/Hausaufgabeninformationen bereit.

Entities:

- `sensor.mein_unterricht_<kind>`
- `sensor.mein_unterricht_<kind>_json`

Typische Felder:

- Datum
- Tag
- Fach/Kurs
- Aufgabe
- Erledigt-Status
- Lehrer-/interne IDs, soweit verfügbar

## `module/lerngruppen/`

Das Modul verarbeitet `lerngruppen.php` und Leistungskontrollen.

### SPH-Daten

Der Client liest Lerngruppen und Leistungskontrollen und verbindet diese über die interne Lerngruppen-ID.

Typische Felder:

- `datum`
- `kurs`
- `art`
- `stunden`
- `stunden_text`
- `dauer_minuten`
- `lehrkraft`
- `lehrkraft_kürzel`
- `summary`
- `uid`

Die Schülerklasse wird aus dem persönlichen Stundenplan ermittelt und als eigenständiges Token aus dem Kursnamen entfernt.

Das Summary lautet z. B.:

```text
Arbeit: Englisch (45 Min)
```

Das Datum ist bewusst nicht Teil des Summarys.

Die Stundenangaben werden nach Möglichkeit über den Stundenplan in konkrete Start-/Endzeiten umgesetzt; andernfalls entsteht ein ganztägiger Termin.

### Manuelle Termine

Manuelle Leistungskontrollen werden nicht in SPH zurückgeschrieben. Sie werden lokal persistent mit Home Assistants `Store` gespeichert.

Services:

- `sph.lerngruppen_termin_hinzufuegen`
- `sph.lerngruppen_termin_loeschen`

SPH- und manuelle Daten werden zusammengeführt. Ein manueller Termin wird bei einem passenden späteren SPH-Termin nur ausgeblendet, nicht gelöscht. Verschwindet der SPH-Termin wieder, kann der lokale Termin erneut erscheinen.

Duplikaterkennung basiert konservativ auf:

- Datum
- Art
- Kurs/Fach
- Stunden

### Entities

- `sensor.lerngruppen_<kind>`
- `sensor.lerngruppen_<kind>_json`
- `calendar.lerngruppen_<kind>`

### Lovelace-Karte

`custom:sph-lerngruppen-card` zeigt die Termine tabellarisch und erlaubt Hinzufügen/Löschen lokaler Termine.

Da Home Assistant den `hass`-Setter häufig aufruft, darf die Karte nicht bei jedem Update ihren gesamten Shadow DOM neu erzeugen. Scrollposition, Dialogzustand und Formularzustand werden erhalten, damit horizontales Scrollen und der Hinzufügen-Dialog stabil bleiben.

## Lovelace-Karten

Normale SPH-Karten:

- `sph-stundenplan-card`
- `sph-stundenplan-tag-card`
- `sph-stundenplan-grid-card`
- `sph-lerngruppen-card`

Schulprofile: `school-hacks: kfg` aktiviert die gemeinsamen Anpassungen.
Die KFG-Einstellungen liegen in `static/school-hacks/kfg.js`.

KFG-spezifische Funktionen gelten nur bei aktiviertem Schulprofil.

### KFG Vertretungsplan-Sensor

Reihenfolge:

1. explizit konfiguriertes `vertretungsplan_sensor`
2. automatisch aus `attributes.klasse` abgeleitet: `sensor.vertretungsplan_<klasse>`
3. Legacy-Fallback `sensor.vertretungsplan`

Diese Auswahl gilt sowohl für Vertretungen als auch für `Nachricht des Tages`.

### Grid-Scrollverhalten

Die Grid-Karten ersetzen bei Updates nicht den gesamten Shadow DOM. Stattdessen wird der Inhalt des bestehenden `.table-wrap` aktualisiert, damit Safari/iOS die horizontale Scrollposition nicht zurücksetzt.

## Datenfluss

```text
Home Assistant
      │
      ▼
custom_components/sph/__init__.py
      │
      ├────────► api/ ───────────── gemeinsame Anmeldung / Session
      │
      ├────────► module/stundenplan/
      │              ├── SPH-Stundenplan
      │              ├── freie Tage aus calendar.deutschland_he
      │              ├── bewegliche Ferientage
      │              ├── Sensoren
      │              └── nativer Kalender
      │
      ├────────► module/kalender/
      │              ├── CSV/iCal
      │              ├── Sensoren
      │              └── nativer Kalender
      │
      ├────────► module/meinunterricht/
      │              └── Sensoren
      │
      └────────► module/lerngruppen/
                     ├── SPH-Leistungskontrollen
                     ├── lokaler Store
                     ├── Services
                     ├── Sensoren
                     └── nativer Kalender
```

## Robustheitsprinzipien

- Temporäre HTTP-/Parser-/Session-Fehler dürfen erfolgreiche Altdaten nicht unnötig überschreiben.
- Module sollen möglichst unabhängig voneinander ausfallen können.
- Der Stundenplan behält den letzten erfolgreichen SPH-Datenstand bei temporären Abruffehlern.
- Bewegliche Ferientage behalten ihren persistenten Cache bei nicht erreichbarer oder leerer Quelle.
- Manuelle Lerngruppen-Termine liegen getrennt von SPH-Daten und überleben normale SPH-Updates.
- Frontend-Komponenten sollen bei regelmäßigen HA-Updates Benutzerzustände wie Scrollposition oder geöffnete Dialoge nicht verlieren.

## Grundprinzip für weitere Entwicklung

Neue Funktionen sollen dort implementiert werden, wo sie fachlich hingehören:

1. **Stundenplan / freie Tage / bewegliche Ferientage:** `module/stundenplan/`
2. **SPH-Schulkalender:** `module/kalender/`
3. **Mein Unterricht:** `module/meinunterricht/`
4. **Lerngruppen / Leistungskontrollen:** `module/lerngruppen/`
5. **Von mehreren Modulen benötigte SPH-Technik:** `api/`
6. **Home-Assistant-Setup, Config Flow, Plattform-Dispatcher:** Ebene `custom_components/sph/`

Bei Erweiterungen eines bestehenden Moduls sollen zuerst dessen Client, Coordinator, Sensor-/Kalender-Implementierung und vorhandene persistente Datenhaltung geprüft werden, bevor neue Logik auf Integrationsebene ergänzt wird.
