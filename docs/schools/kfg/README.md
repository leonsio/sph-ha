# Schul-Profil `kfg`

Das Profil `kfg` enthält die Besonderheiten des **Kaiserin-Friedrich-Gymnasiums Bad Homburg**.

## Aktivierung

Das Profil wird direkt beim Integrationseintrag des Kindes ausgewählt:

**Einstellungen → Geräte & Dienste → Schulportal Hessen → Konfigurieren → Schul-Profil → Kaiserin-Friedrich-Gymnasium Bad Homburg**

Intern wird gespeichert:

```text
school_profile: kfg
```

Die Auswahl gilt nur für dieses Kind.

## Profilpaket

Alle KFG-spezifischen Laufzeitdateien liegen gemeinsam unter:

```text
custom_components/sph/school_profiles/kfg/
├── __init__.py
├── profile.py
└── frontend/
    └── lovelace.js
```

`profile.py` liefert Profil-ID, Anzeigename, Beschreibung, Frontend-Einstiegspunkt und die serverseitige KFG-Logik. `frontend/lovelace.js` enthält ausschließlich KFG-spezifische Darstellungsregeln.

Das Profil wird durch die allgemeine School-Profile-Discovery automatisch gefunden. Der Core enthält keine KFG-spezifische Registrierung.

## Datenebene

Das KFG-Profil wird serverseitig auf die veröffentlichten SPH-Daten angewandt. Aktuell werden insbesondere unterstützt:

- Auflösung von Lehrerkürzeln
- KFG-spezifische Bezeichnungen für Vertretungsarten
- Profilkennzeichnung in Sensor-/JSON-Payloads
- dieselbe Lehrerauflösung in nativen Kalendern
- dieselbe Lehrerauflösung in Mein Unterricht und Lerngruppen
- KFG-spezifische Beschreibungstexte, soweit sie Lehrerfelder enthalten

Die vorhandene Sensorstruktur bleibt erhalten.

## `sensor.kfg_kollegium`

Für die Auflösung von Lehrerkürzeln verwendet ausschließlich dieses Profil:

```text
sensor.kfg_kollegium
```

Erwartetes Attribut:

```text
lehrer
```

Beispiel:

```yaml
lehrer:
  FRA: Franziska Beispiel
  BÄR: Bernd Beispiel
```

Der Sensor ist **keine allgemeine Abhängigkeit von SPH-HA** und wird von keinem anderen Schul-Profil vorausgesetzt.

Wenn sich `sensor.kfg_kollegium` ändert, veröffentlicht SPH-HA die betroffenen Profil-Ausgaben erneut, damit Sensoren und Kalender die aktualisierte Zuordnung übernehmen.

Fehlt die Entity oder ein Kürzel, bleibt der vorhandene SPH-Wert unverändert.

## Vertretungsarten

| KFG-Code | Anzeige |
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

Im Vertretungsplan-Sensor wird der lesbare Wert in `art_lang` bereitgestellt. Der Rohcode `art` bleibt erhalten.

## Stundenplanquelle

Das KFG-Profil wählt keinen eigenen Stundenplan aus. Die Integrationseinstellung **Stundenplan-Ausgabe** bleibt maßgeblich.

Bei persönlicher Ausgabe wird `eigener_plan` profiliert. Bei vollständiger Ausgabe werden `eigener_plan` und `tage` profiliert. `eigener_grundplan` wird nicht als Profilquelle verwendet und nicht durch das Profil verändert.

## Vertretungen und Wochenplan

Konkrete Vertretungen besitzen ein Datum. Sie werden deshalb nicht dauerhaft in den wiederverwendeten Wochenplan geschrieben.

Die Zusammenführung erfolgt in datumsbezogenen Kontexten:

- Stundenplan-Kalender
- kombinierter SPH-Kalender
- Stundenplan-Lovelace-Karten

Der Vertretungsplan-Sensor enthält die veröffentlichten Änderungen als eigene Datenquelle.

## Lovelace

Die Karten erkennen `school_profile: kfg` automatisch über die zugehörigen Sensoren.

Normalerweise reicht daher:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
```

Für Tests oder einen gezielten Override kann angegeben werden:

```yaml
school-profile: kfg
```

Mit

```yaml
school-profile: false
```

kann die Profil-Darstellung einer einzelnen Karte deaktiviert werden.

## KFG-spezifische UI-Regeln

Das Frontend-Profil befindet sich unter:

```text
custom_components/sph/school_profiles/kfg/frontend/lovelace.js
```

Es definiert aktuell:

- A/B-Wochen als Wochenlogik
- A/B-Badges nicht an jedem einzelnen Unterrichtseintrag anzeigen
- Schulwoche einmal oberhalb der Grid-Ansicht anzeigen
- nach Ende der letzten Freitagsstunde auf die nächste Schulwoche wechseln
- Fortschreibung A → B beziehungsweise B → A
- KFG-Vertretungsbezeichnungen
- Hinweise/Nachrichten des Vertretungsplans
- visuelle Kennzeichnung von Vertretung, Entfall, Fachwechsel, Tausch und weiteren Änderungsarten

## Entwicklungsregel

Das KFG-Profil enthält nur KFG-spezifische Abweichungen. Allgemeine Fachnormalisierung, generisches Vertretungsmatching, Kalendererzeugung und andere schulübergreifende Funktionen gehören in den Core.

## Entwickler

Die vollständige API und Anleitung für eigene Schul-Profile befindet sich unter:

[Schul-Profile entwickeln](../../SCHOOL_PROFILES_DEVELOPMENT.md)
