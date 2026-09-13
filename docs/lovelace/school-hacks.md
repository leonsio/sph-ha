# Schulprofile für SPH-Lovelace-Karten

Normale SPH-Karten unterstützen schulabhängige Anpassungen über einen optionalen YAML-Parameter:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

Denselben Parameter unterstützen `sph-stundenplan-card`, `sph-stundenplan-tag-card`,
`sph-lerngruppen-card`, `sph-meinunterricht-card` und `sph-kalender-card`.
Der Parameter wird pro Karte gesetzt. Ohne Parameter oder mit `school-hacks: false`
verwendet die Karte ihre normale Darstellung. Die allgemeine Stundenplan-Darstellung
verwendet dabei automatisch den zum Kind gehörenden internen SPH-Vertretungsplan
`sensor.vertretungsplan_<kind>_<kürzel>`.

School-Hacks bleiben Frontend-Optionen. Sensorattribute, native Automationen und
fremde Lovelace-Karten werden dadurch nicht verändert. Native SPH-Kalender beziehen
Vertretungsinformationen ausschließlich aus dem internen SPH-Vertretungsplan-Modul.

## Vertretungsquellen und Priorität

Die drei SPH-Stundenplankarten verwenden eine feste Prioritätslogik:

1. Ist ein School-Hack aktiv, bekommt dessen in der Profil-Datei konfigurierte
   Vertretungsquelle zuerst die Möglichkeit, die Stunde zu verändern.
2. Liefert die schulische Quelle für diese konkrete Stunde keinen Treffer, wird auf
   den internen SPH-Vertretungsplan des Kindes zurückgefallen.
3. Ohne School-Hack wird direkt der interne SPH-Vertretungsplan verwendet.
4. Ein explizit in der Lovelace-Karte gesetzter `vertretungsplan_sensor`
   (`vertretungsplan` / `substitution_sensor`) bleibt autoritativ. Ist dieser Sensor
   nicht vorhanden, wird nicht still auf eine andere Quelle ausgewichen.

Damit können weitere Schulen eigene Dateien unter `school-hacks/` erhalten und dort
ihre jeweils bevorzugte Vertretungsquelle konfigurieren, ohne die allgemeine
SPH-Logik zu verändern.

## KFG-Funktionen

| Funktion | Karten |
| --- | --- |
| A/B-Filter mit unmarkiertem Gegenstück | Alle drei Stundenplankarten |
| Lehrerauflösung aus `sensor.kfg_kollegium`, Attribut `lehrer` | Stundenplan, Lerngruppen, Mein Unterricht |
| Auflösung beschrifteter Lehrerzeilen in Termin-Details | SPH-Kalenderkarte |
| Vertretung, Entfall, Fach- und Raumwechsel | Alle drei Stundenplankarten |
| Nachricht des Tages | Wochenliste und Tageskarte |
| Datum und Wochenkennung | Alle drei Stundenplankarten |

A/B-Regeln: Eine passende markierte Stunde ersetzt das unmarkierte Gegenstück im
selben Zeitslot. Gibt es keine passende markierte Stunde, bleibt das unmarkierte
Gegenstück erhalten. Eine anders markierte A/B-Stunde wird ausgeblendet. Andere
Badges gelten nicht als Wochenkennzeichen. Fehlt die Wochenkennung, erfolgt keine
Wochenfilterung. Die Wochenkennung wird relativ zu `wochenbeginn` fortgeschrieben: A → B → A.
Die Kennung bleibt im Kopf sichtbar. A/B-Badges an einzelnen Stunden werden bei
KFG ausgeblendet; andere Badges bleiben erhalten.

In der KFG-Rasteransicht steht `Schulwoche A/B` einmalig rechtsbündig in einer
eigenen Zeile oberhalb der Tabelle. Die Tagesköpfe zeigen nur Wochentag und Datum.
Die Wochenzeile liegt außerhalb des horizontalen Scrollbereichs und wird beim
automatischen Wochenwechsel mit aktualisiert (`gridWeekHeading: true` im Profil).

### Wechsel auf die nächste Woche

Mit dem KFG-Profil wechseln Wochenliste und Raster am Freitag nach Ende der letzten
laut A/B-Plan aktiven Stunde zur nächsten Woche. Am Samstag und Sonntag wird immer
die kommende Woche gezeigt. Geöffnete Karten prüfen den Wechsel jede Sekunde und
rendern beim Wochenwechsel neu. Datum, Stundenfilter, Vertretungszuordnung,
Kalenderhervorhebungen und Wochenkennung beziehen sich auf dieselbe Zielwoche.
Die Zeitzone aus Home Assistant bestimmt die Umschaltzeit.

Ein unterrichtsfreier Freitag schaltet bereits am Freitag um 00:00 um. Fehlt für
eine aktive Freitagsstunde eine gültige Endzeit, erfolgt der Wechsel sicherheitshalber
am Samstag. Maßgeblich ist der reguläre Stundenplan, nicht ein kurzfristiger Entfall.
Die Tageskarte verwendet für ihren nächsten Unterrichtstag ebenfalls dessen A/B-Woche.
Ohne KFG-Profil bleibt das bisherige Verhalten der Wochenwahl erhalten.

Der Sensor liefert zusätzlich `eigener_grundplan` ohne die Maskierung aktueller
freier Tage und `wochenbeginn` als Bezugsdatum des erfolgreich abgerufenen A/B-Werts.
`eigener_plan` bleibt kompatibel. Freie Tage werden anhand des Zieldatums angewendet.
Während eines fehlgeschlagenen Abrufs bleibt das Bezugsdatum erhalten. Bei älteren
Sensoren ohne die neuen Attribute dient die aktuelle Kalenderwoche als Bezug.

Lehrerkürzel werden ohne Beachtung der Groß-/Kleinschreibung aufgelöst. Unbekannte
Kürzel bleiben erhalten. Vertretungen werden vor der Namensauflösung anhand der
Original-Fachkürzel, Klasse, Datum und Stunde zugeordnet.

### KFG-Vertretungsquelle

Das KFG-Profil verwendet weiterhin bevorzugt:

1. `sensor.vertretungsplan_<klasse>`
2. `sensor.vertretungsplan`
3. interner `sensor.vertretungsplan_<kind>_<kürzel>` nur als Fallback, wenn die
   KFG-Quelle für die konkrete Stunde keinen Treffer enthält.

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
vertretungsplan_sensor: sensor.vertretungsplan_7n
```

## Native Kalender

Der native Stundenplan-Kalender und der kombinierte SPH-Kalender verwenden keine
Frontend-School-Hacks. Sie gleichen die regulären Stunden serverseitig mit dem
internen SPH-Vertretungsplan ab. Dadurch erscheinen Änderungen auch in
Home-Assistant-Kalendern und nicht nur in Lovelace.

Bei einer passenden Änderung werden unter anderem berücksichtigt:

- Entfall (`Entfall: <Fach>`)
- Vertretung und andere Änderungsarten im Summary
- Fachwechsel mit ursprünglichem Fach in der Beschreibung
- Vertretungslehrkraft
- geänderter Raum

Die UID des regulären Stundenplan-Eintrags bleibt stabil, damit eine nachträglich
bekannt gewordene Vertretung denselben Kalendertermin aktualisiert statt einen
zweiten unabhängigen Termin zu erzeugen.

## Umstieg

Bei bestehenden Karten `type: custom:kfg-…` durch `type: custom:sph-…` ersetzen
und `school-hacks: kfg` ergänzen. Alle übrigen YAML-Einstellungen bleiben erhalten.
Die alten KFG-Typen und ihre JavaScript-Dateien wurden vollständig entfernt.
Bestehende Dashboard-Konfigurationen müssen vor der Nutzung umgestellt werden.
Veraltete, automatisch registrierte KFG-Ressourcen werden beim Neustart entfernt.
Bei manuell gepflegten YAML-Ressourcen die bisherigen KFG-Einträge selbst löschen.

Nach Installation der geänderten Dateien Home Assistant neu starten, damit die
versionierten Ressourcen aktualisiert werden, anschließend das Dashboard neu laden.
Die gemeinsamen Module werden über JavaScript-Imports geladen. Es sind keine
weiteren manuell eingetragenen Lovelace-Ressourcen notwendig.

## Weitere Schulen

Jede Schule erhält genau eine Datei unter
`custom_components/sph/static/school-hacks/<name>.js`.
`school-hacks: <name>` lädt diese Datei automatisch. Schulnamen bestehen aus
Kleinbuchstaben, Ziffern, Bindestrich und Unterstrich. Unbekannte oder nicht ladbare
Profile zeigen einen Fehler in der Karte, statt unbemerkt Standarddaten darzustellen.

Beispiel `school-hacks/beispiel.js`:

```javascript
export default {
  weekBadges: ["A", "B"],
  unbadgedFallback: true,
  hideWeekBadges: true,
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
    labels: { Vertr: "Vertretung", Entf: "Entfall" }
  }
};
```

`teachers` und `substitution` sind optional. Definiert eine Schule `substitution`,
wird genau diese Quelle gegenüber dem internen SPH-Vertretungsplan bevorzugt.
`classPrefix` ermöglicht klassenspezifische Sensoren; `fallback` ist der allgemeine
Sensor dieser Schule. Wenn beide keinen passenden Eintrag für die Stunde liefern,
kann der gemeinsame Adapter anschließend den internen SPH-Vertretungsplan nutzen.

Die schulischen Vertretungsdaten müssen dem bisher unterstützten KFG-Sensorschema
entsprechen. Ein neues Datenformat erfordert eine Erweiterung des gemeinsamen
Adapters. Die Profile sollten im Repository gepflegt werden, damit sie über HACS
ausgeliefert werden.

## Architektur und Tests

- `school-hacks.js`: gemeinsames Laden, Filtern, Lehrerauflösung und schulische Vertretungsquelle.
- `substitution-adapter.js`: Quellenpriorität und Fallback auf den internen SPH-Vertretungsplan.
- `school-hacks/kfg.js`: ausschließlich KFG-Einstellungen.
- `module/vertretung/apply.py`: serverseitiger Abgleich für native Stundenplan-Kalender.
- `sph-*-card.js`: ein Renderer pro Kartenart mit optionalen gemeinsamen Hilfsfunktionen.

```bash
node --test tests/*.test.mjs
python -m unittest discover -s tests -p 'test_*.py'
```

Die Tests prüfen A/B-Gegenstücke, Namensauflösung, Vertretungsquellen und deren
Priorität, Datums-/Stundenabgleich, Originalkürzel, Escaping, Profilwechsel sowie
den serverseitigen Abgleich für Kalendertermine.
