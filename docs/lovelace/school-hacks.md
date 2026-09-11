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
verwendet die Karte ihre normale Darstellung. Dies ist eine Frontend-Option;
Sensorattribute, native Kalender, Automationen und fremde Lovelace-Karten werden
nicht verändert.

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
Wochenfilterung. Die Wochenkennung stammt weiterhin vom Stundenplansensor; das
Profil berechnet keinen eigenen zukünftigen A/B-Kalender.

Lehrerkürzel werden ohne Beachtung der Groß-/Kleinschreibung aufgelöst. Unbekannte
Kürzel bleiben erhalten. Vertretungen werden vor der Namensauflösung anhand der
Original-Fachkürzel, Klasse, Datum und Stunde zugeordnet.

Die Vertretungssensor-Auswahl bleibt:

1. Explizites `vertretungsplan_sensor` (auch `vertretungsplan` / `substitution_sensor`).
2. `sensor.vertretungsplan_<klasse>`.
3. `sensor.vertretungsplan`.

Ein explizit konfigurierter, fehlender Sensor führt nicht zum Ausweichen auf eine
andere Klasse.

```yaml
type: custom:sph-stundenplan-tag-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
vertretungsplan_sensor: sensor.vertretungsplan_7n
```

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

`teachers` und `substitution` sind optional. Ohne `weekBadges` wird nicht gefiltert.
Die Vertretungsdaten müssen dem bisher unterstützten KFG-Sensorschema entsprechen;
ein neues Datenformat erfordert eine Erweiterung des gemeinsamen Adapters.
Die Profile sollten im Repository gepflegt werden, damit sie über HACS ausgeliefert
werden. Bei Änderungen an Frontend-Modulen die Ressourcen- und Importversionen
zusammen aktualisieren.

## Architektur und Tests

- `school-hacks.js`: gemeinsames Laden, Filtern, Lehrerauflösung und Vertretungsabgleich.
- `school-hacks/kfg.js`: ausschließlich KFG-Einstellungen.
- `sph-*-card.js`: ein Renderer pro Kartenart mit optionalen gemeinsamen Hilfsfunktionen.

```bash
node --test tests/school-hacks.test.mjs
```

Die Tests prüfen A/B-Gegenstücke, Namensauflösung, Vertretungsquellen, Datumsabgleich,
Originalkürzel, Escaping, asynchronen Profilwechsel und die echten Stundenplan-Renderer
mit einer minimalen DOM-Testumgebung. Ein Live-Test in Home Assistant bleibt zusätzlich
sinnvoll, insbesondere für Scrollen und Kalender-WebSocket-Abonnements.
