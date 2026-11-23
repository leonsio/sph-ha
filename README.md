# Schulportal Hessen für Home Assistant

Home-Assistant-Custom-Integration für Daten aus dem **Schulportal Hessen (SPH)**.

Aktueller Dokumentationsstand: **Version 0.6.1**.

## Funktionen

Die Integration wird pro Kind eingerichtet und umfasst sechs unabhängig aktivierbare Bereiche:

- **Stundenplan** – persönlicher Wochenstundenplan mit A-/B-Wochen, Unterrichtszeiten, Räumen, Lehrkräften und freien Tagen.
- **Schulkalender** – Termine aus dem Schulportal, auf Wunsch nach Kalenderarten gefiltert und mit eigenen lokalen Terminen ergänzt.
- **Mein Unterricht** – Hausaufgaben und Aufgabenübersichten mit Fachnormalisierung sowie eigenen lokalen Ergänzungen.
- **Lerngruppen** – Leistungskontrollen mit Fach, Dauer, Schulstunden und Lehrkraft sowie eigenen lokalen Terminen.
- **Vertretungsplan** – Vertretungen, Entfälle, Raum- und Fachwechsel sowie Hinweise aus dem Schulportal.
- **Nachrichten** – Zähler ungelesener Nachrichten, Event bei neuen Nachrichten und Übersicht mit Link ins Schulportal.

Zusätzlich stellt SPH-HA eigene Lovelace-Karten bereit. Schulspezifische Besonderheiten werden über **Schul-Profile** pro Kind konfiguriert. Profile können sowohl Daten in Sensoren, JSON-Ausgaben und Kalendern als auch notwendige Darstellungsregeln der Karten anpassen.

## Installation über HACS

Repository als **Integration** in HACS hinzufügen:

```text
https://github.com/leonsio/sph-ha
```

Anschließend unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Schulportal Hessen** suchen.

## Einrichtung

Für jedes Kind wird ein eigener Integrationseintrag angelegt. Benötigt werden insbesondere:

- Name und Kürzel des Kindes
- Schulnummer
- Benutzername und Passwort des Schulportal-Hessen-Kontos
- gewünschtes Aktualisierungsintervall
- optional ein Schul-Profil

Weitere Einstellungen können später über die Integrationsoptionen geändert werden.

### Konfigurationsparameter

| Parameter | Beschreibung |
| --- | --- |
| **Name des Kindes** | Anzeigename des Kindes innerhalb der Integration. |
| **Kürzel des Kindes** | Kurzes eindeutiges Kürzel für die Zuordnung des Kindes. |
| **Schulnummer** | Schulnummer des verwendeten Schulportal-Hessen-Zugangs. |
| **Benutzername** | Benutzername des SPH-Kontos. |
| **Passwort** | Passwort des SPH-Kontos. |
| **Schul-Profil** | Optionales, pro Kind gespeichertes Profil für schulspezifische Daten- und Darstellungsanpassungen. Standard ist kein Profil. |
| **Aktualisierungsintervall** | Legt fest, wie häufig die Daten regulär aktualisiert werden. Zulässig sind 5 bis 1440 Minuten, Standard sind 60 Minuten. |
| **Nachrichten: Abrufintervall** | Legt fest, wie häufig der Nachrichten-Posteingang abgerufen wird. Zulässig sind 15 bis 10080 Minuten, Standard sind 1440 Minuten (einmal täglich). |
| **Bezugsstunde für Entfälle** | Legt fest, welche Schulstunde für die Prüfung auf einen Ausfall heute bzw. morgen verwendet wird. |
| **Stundenplan-Ausgabe** | Wahl zwischen dem persönlichen Stundenplan und einer erweiterten Ausgabe, die zusätzlich den vollständigen vom SPH gelieferten Stundenplan enthält. |
| **Gemeinsamen SPH-Kalender verwenden** | Fasst Stundenplan, Schulkalender und Lerngruppen in einer gemeinsamen Kalenderansicht zusammen. Alternativ können die Kalender getrennt verwendet werden. |
| **Schulamtsbezirk für bewegliche Ferientage** | Lädt die für den ausgewählten hessischen Schulamtsbezirk veröffentlichten beweglichen Ferientage und berücksichtigt sie bei schulfreien Tagen. |
| **Kalenderarten** | Filtert die Arten des SPH-Schulkalenders. Bleibt das Feld leer, werden alle Kalenderarten übernommen. |
| **Aktive Module** | Legt fest, welche Bereiche der Integration verwendet werden sollen. |

Änderungen an den Optionen werden gespeichert und die Integration anschließend automatisch neu geladen.

## Stundenplan

Der persönliche Stundenplan berücksichtigt die vom Schulportal gemeldete A-/B-Woche und kann schulfreie Tage aus Home Assistant sowie die konfigurierten beweglichen Ferientage berücksichtigen.

Vertretungen aus dem SPH-Vertretungsplan können in datumsbezogenen Stundenplan-Darstellungen und Kalendern berücksichtigt werden. Dazu gehören unter anderem Entfälle, Vertretungslehrkräfte, Raumänderungen und Fachwechsel.

Die Auswahl der Stundenplanquelle bleibt unabhängig vom Schul-Profil. Ein Profil verarbeitet die veröffentlichte Konfiguration, wählt aber keine alternative Stundenplanquelle.

## Schulkalender

Der Schulkalender lädt die Termine des aktuellen hessischen Schuljahres. Kalenderarten können gefiltert werden; ohne Filter werden alle verfügbaren Arten übernommen.

Zusätzlich können eigene lokale Termine angelegt werden. Diese bleiben unabhängig von Aktualisierungen des Schulportals erhalten.

## Mein Unterricht

Hausaufgaben und Aufgaben werden nach Fächern zusammengefasst. Unterschiedliche Kursbezeichnungen werden soweit möglich auf ein gemeinsames Fach normalisiert, ohne die ursprüngliche Kursinformation zu verlieren.

Eigene Hausaufgaben können lokal ergänzt und gemeinsam mit den Daten aus dem Schulportal dargestellt werden.

## Lerngruppen

Leistungskontrollen werden mit Datum, Art, Fach/Kurs, Dauer und – soweit vorhanden – den zugehörigen Schulstunden dargestellt.

Wenn sich die angegebenen Schulstunden dem persönlichen Stundenplan zuordnen lassen, können daraus konkrete Start- und Endzeiten abgeleitet werden. Eigene Leistungskontrollen lassen sich ebenfalls lokal ergänzen.

## Vertretungsplan

Der Vertretungsplan zeigt veröffentlichte Änderungen für die kommenden Schultage. Unterstützt werden unter anderem:

- Vertretungen
- Entfälle
- Raumänderungen
- Fachwechsel
- Vertretungslehrkräfte
- Hinweise des Tages

Die Informationen werden in der Vertretungsplan-Karte sowie in datumsbezogenen Stundenplan- und Kalenderdarstellungen verwendet.

## Nachrichten

Das Modul ist standardmäßig deaktiviert und wird unter **Aktive Module** eingeschaltet. Es liest den Posteingang des Schulportals (ohne ausgeblendete Unterhaltungen) und stellt bereit:

- einen Sensor mit der Anzahl ungelesener Unterhaltungen,
- ein Event, sobald Unterhaltungen neu ungelesen sind – also neue Nachrichten oder neue Antworten in bereits gelesenen Unterhaltungen,
- eine Lovelace-Karte mit Absender, Betreff und Datum der ungelesenen Nachrichten und einem Link ins Schulportal.

Das Modul arbeitet nur lesend: Nachrichten werden weder als gelesen markiert noch versendet. Der Nachrichtentext wird nicht abgerufen.

Da das Schulportal in jeder Abfrage die vollständigen Empfängerlisten mitliefert, ist eine Antwort schnell rund ein Megabyte groß. Das Modul verwendet deshalb ein eigenes, standardmäßig tägliches Abrufintervall. Zusätzlich wird nach jedem Start von Home Assistant einmal abgerufen – erst wenn Home Assistant vollständig gestartet ist, damit Automationen keine Meldung verpassen. Ein sofortiger Abruf ist jederzeit über `homeassistant.update_entity` für den Nachrichtensensor möglich.

Betreff und Absender stehen nicht in den Sensorattributen; die Karte lädt sie bei Bedarf über eine WebSocket-Schnittstelle. Die Event-Entität enthält Absender und Betreff für aussagekräftige Benachrichtigungen, schließt diese Attribute aber von der Recorder-Datenbank aus. Das Bus-Event `sph_neue_nachricht` speichert Home Assistant dagegen wie alle Events in der Datenbank; wer das nicht möchte, schließt es aus:

```yaml
recorder:
  exclude:
    event_types:
      - sph_neue_nachricht
```

## Lovelace-Karten

SPH-HA bringt eigene Karten für folgende Ansichten mit:

- Wochenstundenplan als Liste
- Tagesstundenplan
- Wochenstundenplan als Raster
- Mein Unterricht
- Lerngruppen und Leistungskontrollen
- Kalender mit Tag-, Woche- und Monatsansicht
- Vertretungsplan
- Nachrichten

Die Karten werden automatisch registriert. Die vollständige Dokumentation einschließlich Screenshots und Konfigurationsbeispielen befindet sich unter [docs/lovelace](docs/lovelace/README.md).

## 7,5"-ePaper-Display

Die von SPH-HA bereitgestellten Informationen können alternativ zu Lovelace auch auf einem **7,5"-ePaper-Display** dargestellt werden. Im Ordner [`epaper`](epaper/README.md) befindet sich eine Beispielkonfiguration für ESPHome, die unter anderem Stundenplan, Hausaufgaben, anstehende Arbeiten und weitere Informationen auf einem 800 × 480 Pixel großen ePaper-Display anzeigt.

## Schul-Profile

Schul-Profile bündeln ausschließlich die Besonderheiten einer Schule. Sie werden pro Kind ausgewählt und können serverseitig Werte in Sensoren, JSON-Ausgaben und Kalendern sowie optional UI-Regeln für Lovelace anpassen.

Die bestehende Sensorstruktur bleibt dabei grundsätzlich erhalten. Profilierte Payloads enthalten zusätzlich das Metadatum `school_profile`.

Derzeit vorhanden:

- [`kfg` – Kaiserin-Friedrich-Gymnasium Bad Homburg](docs/schools/kfg/README.md)

Benutzerdokumentation: [Schul-Profile](docs/SCHOOL_PROFILES.md)

Entwicklerdokumentation: [Schul-Profile entwickeln](docs/SCHOOL_PROFILES_DEVELOPMENT.md)

## Robustheit

Bei vorübergehenden Abruffehlern bleiben zuletzt erfolgreich geladene Daten soweit möglich erhalten. Lokal angelegte Hausaufgaben, Leistungskontrollen und eigene Kalendertermine bleiben unabhängig von der Erreichbarkeit des Schulportals gespeichert.

## Dokumentation

- [Entitäten, Sensoren und Services](docs/ENTITAETEN_UND_SERVICES.md)
- [Lovelace-Karten](docs/lovelace/README.md)
- [7,5"-ePaper-Beispiel](epaper/README.md)
- [Schul-Profile](docs/SCHOOL_PROFILES.md)
- [Schul-Profile für Entwickler](docs/SCHOOL_PROFILES_DEVELOPMENT.md)
- [Schulspezifische Profile](docs/schools/README.md)
- [Architektur](docs/ARCHITEKTUR.md)

## Danksagung und Inspiration

Ein besonderer Dank geht an das Projekt [lanis-mobile](https://github.com/lanis-mobile). Das Repository diente als Inspirationsquelle und enthält hilfreiche Beispiele für mögliche technische Implementierungen und Anbindungen rund um das [Schulportal Hessen](https://schulportal.hessen.de).

SPH-HA ist ein eigenständiges Projekt und übernimmt daraus keine offizielle Verbindung oder Unterstützung durch das Schulportal Hessen.

## Hinweis

Dieses Projekt ist ein unabhängiges Community-Projekt und steht nicht in offizieller Verbindung mit dem Schulportal Hessen.
