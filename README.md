# Schulportal Hessen für Home Assistant

Home-Assistant-Custom-Integration für Daten aus dem **Schulportal Hessen (SPH)**.

Aktueller Dokumentationsstand: **Version 0.5.0**.

## Funktionen

Die Integration wird pro Kind eingerichtet und umfasst fünf unabhängig aktivierbare Bereiche:

- **Stundenplan** – persönlicher Wochenstundenplan mit A-/B-Wochen, Unterrichtszeiten, Räumen, Lehrkräften und freien Tagen.
- **Schulkalender** – Termine aus dem Schulportal, auf Wunsch nach Kalenderarten gefiltert und mit eigenen lokalen Terminen ergänzt.
- **Mein Unterricht** – Hausaufgaben und Aufgabenübersichten mit Fachnormalisierung sowie eigenen lokalen Ergänzungen.
- **Lerngruppen** – Leistungskontrollen mit Fach, Dauer, Schulstunden und Lehrkraft sowie eigenen lokalen Terminen.
- **Vertretungsplan** – Vertretungen, Entfälle, Raum- und Fachwechsel sowie Hinweise aus dem Schulportal.

Zusätzlich stellt SPH-HA eigene Lovelace-Karten für Stundenplan, Kalender, Lerngruppen, Mein Unterricht und Vertretungen bereit. Schulspezifische Anpassungen können über **School Hacks** ergänzt werden, ohne separate Kartenvarianten pflegen zu müssen.

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

Weitere Einstellungen können später über die Integrationsoptionen geändert werden.

### Konfigurationsparameter

| Parameter | Beschreibung |
| --- | --- |
| **Name des Kindes** | Anzeigename des Kindes innerhalb der Integration. |
| **Kürzel des Kindes** | Kurzes eindeutiges Kürzel für die Zuordnung des Kindes. |
| **Schulnummer** | Schulnummer des verwendeten Schulportal-Hessen-Zugangs. |
| **Benutzername** | Benutzername des SPH-Kontos. |
| **Passwort** | Passwort des SPH-Kontos. |
| **Aktualisierungsintervall** | Legt fest, wie häufig die Daten regulär aktualisiert werden. Zulässig sind 5 bis 1440 Minuten, Standard sind 60 Minuten. |
| **Bezugsstunde für Entfälle** | Legt fest, welche Schulstunde für die Prüfung auf einen Ausfall heute bzw. morgen verwendet wird. |
| **Stundenplan-Ausgabe** | Wahl zwischen dem persönlichen Stundenplan und einer erweiterten Ausgabe, die zusätzlich den vollständigen vom SPH gelieferten Stundenplan enthält. |
| **Gemeinsamen SPH-Kalender verwenden** | Fasst Stundenplan, Schulkalender und Lerngruppen in einer gemeinsamen Kalenderansicht zusammen. Alternativ können die Kalender getrennt verwendet werden. |
| **Schulamtsbezirk für bewegliche Ferientage** | Lädt die für den ausgewählten hessischen Schulamtsbezirk veröffentlichten beweglichen Ferientage und berücksichtigt sie bei schulfreien Tagen. |
| **Kalenderarten** | Filtert die Arten des SPH-Schulkalenders. Bleibt das Feld leer, werden alle Kalenderarten übernommen. |
| **Aktive Module** | Legt fest, welche Bereiche der Integration verwendet werden sollen. |

Änderungen an den Optionen werden gespeichert und die Integration anschließend automatisch neu geladen.

## Stundenplan

Der persönliche Stundenplan berücksichtigt die vom Schulportal gemeldete A-/B-Woche und kann schulfreie Tage aus Home Assistant sowie die konfigurierten beweglichen Ferientage berücksichtigen.

Vertretungen aus dem SPH-Vertretungsplan können direkt in den Stundenplan-Darstellungen berücksichtigt werden. Dazu gehören unter anderem Entfälle, Vertretungslehrkräfte, Raumänderungen und Fachwechsel.

Für die Kalenderansicht wird der Stundenplan über mehrere Wochen fortgeschrieben. Dabei werden A-/B-Wochen automatisch weitergeführt und bekannte Vertretungen auf die jeweiligen Unterrichtstermine angewendet.

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

Die Informationen werden nicht nur in der eigenen Vertretungsplan-Karte verwendet, sondern können auch in Stundenplan- und Kalenderdarstellungen einfließen.

## Lovelace-Karten

SPH-HA bringt eigene Karten für folgende Ansichten mit:

- Wochenstundenplan als Liste
- Tagesstundenplan
- Wochenstundenplan als Raster
- Mein Unterricht
- Lerngruppen und Leistungskontrollen
- Kalender mit Tag-, Woche- und Monatsansicht
- Vertretungsplan

Die Karten werden automatisch registriert. Die vollständige Dokumentation einschließlich Screenshots und Konfigurationsbeispielen befindet sich unter [docs/lovelace](docs/lovelace/README.md).

## School Hacks

School Hacks ergänzen die allgemeinen Lovelace-Karten um schulspezifische Darstellungs- und Zuordnungsregeln. Dadurch müssen keine separaten Kartenvarianten pro Schule gepflegt werden.

Derzeit vorhanden:

- [`kfg` – Kaiserin-Friedrich-Gymnasium Bad Homburg](docs/schools/kfg/README.md)

Allgemeine Beschreibung und Anleitung für weitere Schulen: [School Hacks](docs/lovelace/school-hacks.md).

## Robustheit

Bei vorübergehenden Abruffehlern bleiben zuletzt erfolgreich geladene Daten soweit möglich erhalten. Lokal angelegte Hausaufgaben, Leistungskontrollen und eigene Kalendertermine bleiben unabhängig von der Erreichbarkeit des Schulportals gespeichert.

## Dokumentation

- [Entitäten, Sensoren und Services](docs/ENTITAETEN_UND_SERVICES.md)
- [Lovelace-Karten](docs/lovelace/README.md)
- [School Hacks](docs/lovelace/school-hacks.md)
- [Schulspezifische Profile](docs/schools/README.md)
- [Architektur](docs/ARCHITEKTUR.md)

## Hinweis

Dieses Projekt ist ein unabhängiges Community-Projekt und steht nicht in offizieller Verbindung mit dem Schulportal Hessen.