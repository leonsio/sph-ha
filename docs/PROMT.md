# Aufgabe: Home-Assistant-Integration „Schulportal Hessen (SPH)“

Arbeite direkt im bestehenden Repository:

https://github.com/leonsio/sph-ha

Die Integration ist eine HACS-kompatible Home-Assistant-Custom-Integration für das Schulportal Hessen:

https://start.schulportal.hessen.de/

Bestehender funktionierender Code hat Vorrang vor diesem Dokument. Vor Änderungen immer den aktuellen Repository-Stand analysieren und vorhandene Funktionen erhalten.

## 1. Module

Aktuell existieren folgende fachliche Module:

- Stundenplan
- Schulkalender
- Mein Unterricht
- Lerngruppen

Zusätzlich existieren normale SPH-Lovelace-Karten sowie KFG-spezifische Varianten für das Kaiserin-Friedrich-Gymnasium.

KFG-Sonderfunktionen dürfen normale SPH-Funktionen nicht verändern.

## 2. Architektur

Fachliche Logik gehört in das jeweilige Modul:

```text
custom_components/sph/
├── api/
│   └── gemeinsame Auth-/Session-/HTTP-Logik
├── module/
│   ├── stundenplan/
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   ├── calendar.py
│   │   ├── movable_holidays.py
│   │   └── sensor.py
│   ├── kalender/
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   └── sensor.py
│   ├── meinunterricht/
│   │   ├── client.py
│   │   ├── coordinator.py
│   │   └── sensor.py
│   └── lerngruppen/
│       ├── client.py
│       ├── coordinator.py
│       ├── calendar.py
│       ├── sensor.py
│       ├── services.py
│       └── storage.py
├── static/
├── translations/
├── __init__.py
├── calendar.py
├── config_flow.py
├── const.py
└── sensor.py
```

Nur Funktionen, die von mehreren Modulen benötigt werden, gehören nach `api/`.

## 3. Authentifizierung und Robustheit

Alle SPH-Module verwenden dieselbe authentifizierte Session.

Bei abgelaufener Session:

1. Login erneuern.
2. Ursprünglichen Abruf erneut versuchen.

Temporäre Fehler dürfen vorhandene erfolgreiche Daten nicht unnötig löschen. Dazu zählen insbesondere:

- fehlende Internetverbindung,
- SPH nicht erreichbar,
- HTTP-Fehler,
- abgelaufene Session,
- leere oder fehlerhafte CSV/iCal-Daten,
- geänderte HTML-Struktur,
- einzelne nicht verfügbare Module.

Ein Fehler in einem Modul darf andere Module nicht unbrauchbar machen.

## 4. Aktualisierung und Module

Standard-Aktualisierungsintervall: **60 Minuten**.

In der Konfiguration gibt es eine Mehrfachauswahl **Aktive Module** für:

- Stundenplan
- Schulkalender
- Mein Unterricht
- Lerngruppen

Intern werden aus Kompatibilitätsgründen weiterhin die bisherigen booleschen Modulwerte gespeichert.

Ein deaktiviertes Modul soll keine unnötigen HTTP-Abrufe durchführen.

Wird der Schulkalender deaktiviert, werden dessen Sensor- und Kalender-Entities vollständig aus der Entity Registry entfernt.

## 5. Config Flow

Folgende Werte müssen einstellbar bzw. nachträglich änderbar sein:

- Schulnummer / SchulID
- Benutzername
- Passwort
- Name des Kindes
- Kürzel des Kindes
- Aktualisierungsintervall
- aktive Module
- Stundenplan-Ausgabe
- Schulamtsbezirk für bewegliche Ferientage
- Kalenderarten-Filter

Die Integration wird nach Änderungen automatisch neu geladen.

### Home-Assistant-Selector-Regeln

Bei `translation_key` dürfen Selector-Optionen nur gültige HA-Translationsschlüssel verwenden: `[a-z0-9-_]+`, ohne Leerzeichen/Umlaute und ohne führenden/abschließenden Bindestrich oder Unterstrich.

Bei Anzeigenamen wie `Bad Vilbel`, `Frankfurt am Main` oder `Gießen` stattdessen explizite `value`/`label`-Optionen ohne `translation_key` verwenden oder intern slug-fähige Werte sauber auf Anzeigenamen abbilden.

## 6. Entity-Namen

Name und Kürzel des Kindes fließen in die Entity-ID ein.

Beispiele:

- `sensor.stundenplan_maxim_mk`
- `sensor.stundenplan_maxim_mk_json`
- `calendar.stundenplan_maxim_mk`
- `sensor.schulkalender_maxim_mk`
- `sensor.schulkalender_maxim_mk_json`
- `calendar.schulkalender_maxim_mk`
- `sensor.mein_unterricht_maxim_mk`
- `sensor.mein_unterricht_maxim_mk_json`
- `sensor.lerngruppen_maxim_mk`
- `sensor.lerngruppen_maxim_mk_json`
- `calendar.lerngruppen_maxim_mk`
- `calendar.bewegliche_ferientage_maxim_mk`

## 7. Stundenplan

Quelle: `stundenplan.php`.

Zu den Unterrichtsdaten gehören:

- Fach/Fachkürzel
- Lehrer
- Raum
- Beginn/Ende
- Stundenindex
- Dauer
- `badge`
- Wochentag
- Schülerklasse
- aktuelle A/B-Wochenkennung

Client-Datenmodell:

```python
{
    "week_badge": ...,
    "all": [...],
    "own": [...],
    "klasse": ...,
}
```

## 8. Stundenplan-Sensoren

Es existieren:

- `sensor.stundenplan_<kind>`
- `sensor.stundenplan_<kind>_json`

Der Block `eigener_plan` bleibt immer erhalten und ist der primäre persönliche Stundenplan.

Der Legacy-Block `tage` bleibt aus Kompatibilitätsgründen strukturell erhalten.

Konfiguration **Stundenplan-Ausgabe**:

- `own`: nur `eigener_plan` befüllen; `tage` als leere Tagesblöcke erhalten.
- `all`: zusätzlich vollständigen SPH-Stundenplan in `tage` ausgeben.

Der JSON-Sensor stellt denselben Payload als kompakten JSON-String im Attribut `json` bereit.

## 9. A/B-Wochen

A/B-Stunden müssen anhand der aktuellen Wochenkennung korrekt gefiltert werden.

Bei gleichen Zeitslots gelten Gegenstück-Regeln:

| Slot | Woche A | Woche B |
|---|---|---|
| A + unmarkiert | A | unmarkiert |
| B + unmarkiert | unmarkiert | B |
| A + B | A | B |
| nur A | A | nichts |
| nur B | nichts | B |
| nur unmarkiert | unmarkiert | unmarkiert |

Diese Logik gilt sowohl für den nativen Stundenplan-Kalender als auch für die KFG-Kompatibilitätslogik.

## 10. Nativer Stundenplan-Kalender

Entity:

- `calendar.stundenplan_<kind>`

Zeitfenster:

- 2 Wochen Vergangenheit
- 8 Wochen Zukunft

Events werden dynamisch erzeugt, nicht dauerhaft materialisiert. Dadurch verschwinden ältere Einträge automatisch aus dem Zeitfenster.

Pro tatsächlichem Schultag wird zusätzlich ein ganztägiger Marker erzeugt:

- `Schulwoche A`
- `Schulwoche B`

Ganztägige `date`-Events und zeitgebundene `datetime`-Events müssen vor Sortierung und Vergleichen auf kompatible timezone-aware Werte normalisiert werden.

## 11. Freie Tage über `calendar.deutschland_he`

Wenn `calendar.deutschland_he` existiert, wird er über `calendar.get_events` abgefragt.

Jeder Tag mit mindestens einem Termin gilt als schulfrei.

An freien Tagen werden unterdrückt:

- Unterricht im nativen Stundenplan-Kalender,
- `Schulwoche A/B`,
- Unterrichtsdaten in der aktuell dargestellten Woche der Stundenplan-Sensoren.

Die Prüfung ist vom normalen SPH-Abruf entkoppelt:

- Retry kurz nach Integration-Start,
- Reaktion auf State-Änderungen,
- zusätzliche Prüfung alle 15 Minuten.

Ändert sich nur die Freie-Tage-Liste, werden vorhandene Stundenplandaten neu veröffentlicht, ohne SPH erneut abzurufen.

## 12. Bewegliche Ferientage

Quelle:

https://schulaemter.hessen.de/schulbesuch/bewegliche-ferientage

Die Liste der Schulamtsbezirke ist statisch im Code hinterlegt.

Die Webseite enthält Termine getrennt nach:

- Schulamtsbezirk
- Schuljahr

Es dürfen nur die Termine des konfigurierten Bezirks und des aktuell relevanten Schuljahres übernommen werden.

Andere Bezirke und andere Schuljahre sind zu verwerfen.

Die Online-Quelle wird nur **einmal pro Tag** aktualisiert.

Bei Fehlern oder leerem Ergebnis:

- zuletzt erfolgreiche gespeicherte Daten behalten,
- nicht durch leere Daten ersetzen.

Persistent gespeichert werden nur relevante Daten, z. B.:

```yaml
district: Bad Vilbel
school_year: 2026/2027
events:
  - date: "2027-02-08"
    summary: Rosenmontag
```

Die beweglichen Ferientage werden als eigener nativer Kalender bereitgestellt:

- `calendar.bewegliche_ferientage_<kind>`

Dieser Kalender wird vom Stundenplan genauso als Freie-Tage-Quelle ausgewertet wie `calendar.deutschland_he`.

## 13. Schulkalender

Quelle: `kalender.php`.

Bevorzugt CSV, iCal als Fallback.

Das relevante hessische Schuljahr muss korrekt bestimmt werden.

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

### Kalenderarten-Filter

`calendar_event_types` ist optional:

- leer / `[]` = alle Kategorien übernehmen,
- Werte vorhanden = nur diese Kategorien übernehmen.

Mehrere Werte dürfen komma-, semikolon- oder zeilengetrennt angegeben werden.

Entities:

- `sensor.schulkalender_<kind>`
- `sensor.schulkalender_<kind>_json`
- `calendar.schulkalender_<kind>`

Home Assistant begrenzt State Attributes. Große JSON-Attribute können vom Recorder nicht gespeichert werden; das ist bei der Datenmenge zu berücksichtigen.

## 14. Mein Unterricht

Quelle: `meinunterricht.php`.

Entities:

- `sensor.mein_unterricht_<kind>`
- `sensor.mein_unterricht_<kind>_json`

Typische Felder:

- Datum
- Wochentag
- Fach/Kurs
- Thema/Aufgabe
- Lehrer
- erledigt/nicht erledigt
- interne IDs, soweit verfügbar

Die gemeinsame SPH-Session muss verwendet werden.

## 15. Lerngruppen

Quelle: `lerngruppen.php`.

Leistungskontrollen enthalten typischerweise:

- Datum
- Kurs
- Art
- Schulstunden
- Dauer in Minuten
- Lehrkraft
- Lehrkraft-Kürzel
- Summary
- UID

Die Schülerklasse wird aus dem persönlichen Stundenplan gelesen und als eigenständiges Token aus dem Kursnamen entfernt.

Summary-Beispiel:

```text
Arbeit: Englisch (45 Min)
```

Das Datum gehört bewusst nicht in das Summary.

Stundenangaben sollen mit dem persönlichen Stundenplan zu Start-/Endzeiten aufgelöst werden. Falls das nicht möglich ist, ist ein ganztägiger Termin zulässig.

Entities:

- `sensor.lerngruppen_<kind>`
- `sensor.lerngruppen_<kind>_json`
- `calendar.lerngruppen_<kind>`

## 16. Manuelle Lerngruppen-Termine

Fehlende Leistungskontrollen können lokal ergänzt werden.

Nicht in SPH zurückschreiben.

Persistenz über Home Assistants `Store`, getrennt von SPH-Daten.

Services:

- `sph.lerngruppen_termin_hinzufuegen`
- `sph.lerngruppen_termin_loeschen`

Manuelle Termine müssen SPH-Updates überleben.

Wenn später ein passender SPH-Termin auftaucht, soll der manuelle Termin nur ausgeblendet, nicht gelöscht werden. Verschwindet der SPH-Termin wieder, kann der lokale Termin erneut erscheinen.

Duplikaterkennung basiert auf:

- Datum
- Art
- Fach/Kurs
- Stunden

## 17. Lovelace-Karten

Normale SPH-Karten:

- `sph-stundenplan-card`
- `sph-stundenplan-tag-card`
- `sph-stundenplan-grid-card`
- `sph-lerngruppen-card`

KFG-Karten:

- `kfg-stundenplan-card`
- `kfg-stundenplan-tag-card`
- `kfg-stundenplan-grid-card`

Gemeinsame KFG-Kompatibilitätslogik:

- `kfg-stundenplan-compat.js`

Lovelace-Ressourcen werden automatisch und versioniert registriert. Nicht zusätzlich `add_extra_js_url()` verwenden.

## 18. `sph-lerngruppen-card`

Die Karte zeigt Leistungskontrollen tabellarisch und erlaubt:

- lokale Termine hinzufügen,
- lokale Termine löschen.

Die Karte nutzt intern die SPH-Services.

Home Assistant setzt `hass` häufig neu. Deshalb darf die Karte bei unveränderten Sensordaten nicht ständig den kompletten Shadow DOM ersetzen.

Bei einem echten Rendern müssen möglichst erhalten bleiben:

- horizontale Scrollposition,
- geöffneter Dialog,
- Formularwerte,
- Fokus,
- Cursor-/Auswahlposition.

## 19. Grid-Scrollverhalten

Die SPH- und KFG-Grid-Karten dürfen beim Update nicht den kompletten Shadow Root ersetzen, wenn dadurch die horizontale Scrollposition verloren geht.

Bestehende `.table-wrap`-Elemente sollen aktualisiert werden, ohne sie selbst zu ersetzen.

Dies ist insbesondere für Safari/iOS wichtig.

## 20. KFG Vertretungsplan

Vertretungssensor-Auswahl:

1. explizit gesetztes `vertretungsplan_sensor`,
2. automatisch `sensor.vertretungsplan_<klasse>`,
3. Fallback `sensor.vertretungsplan`.

Ein explizit gesetzter Sensor darf nicht heimlich durch einen anderen Sensor ersetzt werden, wenn er fehlt.

Vertretungen müssen zuerst anhand der Originalkürzel zugeordnet werden und erst danach in lesbare Fach-/Lehrernamen umgewandelt werden.

## 21. KFG Lehrerauflösung

`sensor.kfg_kollegium` kann Lehrer-Kürzel auflösen.

Die Zuordnung muss case-insensitiv sein.

## 22. Vertretungsarten

Lesbare Namen:

- Betr → Betreuung
- Vertr → Vertretung
- Entf → Entfall
- Taus → Tausch
- Freis → Freistunde
- Raum → Raumänderung
- Statt-Vertretung → Statt-Vertretung
- Paus → Pausenaufsicht
- SES → Sonderunterricht
- Vtr. ohne Lehrer → Vertretung ohne Lehrer

Entfall soll visuell als entfallen erkennbar sein.

## 23. Nachricht des Tages

Die KFG-Wochen- und Tageskarte können `Nachricht des Tages` aus dem gewählten Vertretungsplan-Sensor anzeigen.

Nur anzeigen, wenn tatsächlich Inhalt vorhanden ist.

Die Grid-Karte zeigt diese Nachricht nicht.

## 24. Titel

Wenn in YAML kein `title:` angegeben wurde, darf kein künstlicher Standardtitel erzeugt werden.

## 25. Versions- und Frontend-Regeln

Bei Backend-Änderungen `manifest.json` angemessen erhöhen.

`CARD_VERSION` nur erhöhen, wenn statische Lovelace-JavaScript-Dateien geändert wurden oder ein Cache-Bust erforderlich ist.

Keine unnötige CARD_VERSION-Erhöhung bei reinen Backend-/Dokumentationsänderungen.

## 26. Home-Assistant- und HACS-Validierung

Vor einem Release prüfen:

- HACS validation
- Home Assistant / Hassfest validation
- JSON/Translations
- manifest
- services
- config_flow
- Python-Syntax
- JavaScript-Syntax bei Frontend-Änderungen

Ein grüner HACS-Check reicht nicht aus; Hassfest muss ebenfalls erfolgreich sein.

Insbesondere Übersetzungsschlüssel für Selector-Optionen müssen den Home-Assistant-Regeln entsprechen.

## 27. Coding-Regeln

- Keine monolithische `client.py`.
- Fachlogik in das passende Modul.
- Gemeinsame SPH-Technik nach `api/`.
- Keine manuellen YAML-Strings für strukturierte Daten.
- Benutzer- und Portalwerte korrekt serialisieren/escapen.
- Bestehende erfolgreiche Daten bei temporären Fehlern behalten.
- Keine Regressionsänderungen an funktionierenden Karten oder Sensoren.
- Große Frontend-Dateien nur gezielt verändern.
- Bei Dateischreiboperationen immer aktuellen Stand/SHA verwenden.

## 28. Vorgehensweise für Coding-KI

Vor Änderungen:

1. aktuellen Repository-Stand lesen,
2. aktuelle Version prüfen,
3. betroffene Module bestimmen,
4. relevante Architektur-/README-Dokumentation lesen,
5. bestehende Implementierung als maßgeblich betrachten.

Nach Änderungen:

1. Imports und Syntax prüfen,
2. Entity-Namen prüfen,
3. Datenkompatibilität prüfen,
4. Home-Assistant-/HACS-Validierung beachten,
5. Diff kontrollieren,
6. aussagekräftige Commits erstellen.

Bei Fehlern aus GitHub Actions zuerst die konkrete fehlgeschlagene Job-/Step-Ausgabe lesen und die Ursache minimal beheben.
