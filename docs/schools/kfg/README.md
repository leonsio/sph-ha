# Schul-Profil `kfg`

Das Profil `kfg` enthält die Besonderheiten des **Kaiserin-Friedrich-Gymnasiums Bad Homburg**.

Ab SPH-HA 0.6.0 ersetzt es die bisherige KFG-Konfiguration über `school-hacks: kfg`.

## Aktivierung

Das Profil wird direkt beim Integrationseintrag des Kindes ausgewählt:

**Einstellungen → Geräte & Dienste → Schulportal Hessen → Konfigurieren → Schul-Profil → Kaiserin-Friedrich-Gymnasium Bad Homburg**

Intern wird gespeichert:

```text
school_profile: kfg
```

Die Auswahl gilt nur für dieses Kind.

## Datenebene

Das KFG-Profil wird serverseitig auf die veröffentlichten SPH-Daten angewandt. Dadurch sind KFG-spezifische Anpassungen nicht mehr ausschließlich in Lovelace sichtbar.

Aktuell werden insbesondere unterstützt:

- Auflösung von Lehrerkürzeln
- KFG-spezifische Bezeichnungen für Vertretungsarten
- Profilkennzeichnung in Sensor-/JSON-Payloads
- dieselbe Lehrerauflösung in nativen Kalendern
- dieselbe Lehrerauflösung in Mein Unterricht und Lerngruppen
- KFG-spezifische Beschreibungstexte, soweit sie Lehrerfelder enthalten

Die vorhandene Sensorstruktur bleibt dabei erhalten.

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

Das Profil übernimmt die bisherigen KFG-Zuordnungen aus dem School-Hacks-Profil:

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

Im Vertretungsplan-Sensor wird dafür der vorhandene Datensatz um bzw. über `art_lang` lesbar aufbereitet. Der Rohcode `art` bleibt erhalten.

## Stundenplanquelle

Das KFG-Profil wählt keinen eigenen Stundenplan aus.

Die vorhandene Integrationseinstellung **Stundenplan-Ausgabe** bleibt vollständig maßgeblich. Insbesondere wird `eigener_grundplan` nicht als alternative Profilquelle verwendet.

Das ist relevant, wenn ein umfangreicher Schulplan parallele Angebote enthält, die nicht alle für das Kind gelten.

## Vertretungen und Wochenplan

Konkrete Vertretungen besitzen ein Datum. Sie werden deshalb nicht dauerhaft in den wiederverwendeten Wochenplan eingebrannt.

Dadurch wird verhindert, dass beispielsweise eine Vertretungslehrkraft aus dieser Woche beim Anzeigen einer späteren Woche fälschlich weiterverwendet wird.

Die Zusammenführung erfolgt in datumsbezogenen Kontexten:

- Stundenplan-Kalender
- kombinierter SPH-Kalender
- Stundenplan-Lovelace-Karten

Der Vertretungsplan-Sensor selbst enthält die veröffentlichten Änderungen natürlich weiterhin als eigene Datenquelle.

## Lovelace

Die Karten erkennen `school_profile: kfg` automatisch über die zugehörigen Sensoren.

Normalerweise reicht daher:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
```

Ein zusätzlicher Parameter ist nicht erforderlich.

### Expliziter Override

Für Tests kann weiterhin angegeben werden:

```yaml
school-profile: kfg
```

Der alte Parameter

```yaml
school-hacks: kfg
```

bleibt in 0.6.0 als Kompatibilitätsalias erhalten.

## KFG-spezifische UI-Regeln

Die bisherigen KFG-Lovelace-Anpassungen wurden in das Frontend-Profil übernommen:

```text
custom_components/sph/static/school-profiles/kfg.js
```

Dazu gehören aktuell:

- A/B-Wochen als Wochenlogik
- A/B-Badges nicht an jedem einzelnen Unterrichtseintrag anzeigen
- Schulwoche einmal oberhalb der Grid-Ansicht anzeigen
- nach Ende der letzten Freitagsstunde auf die nächste Schulwoche wechseln
- korrekte Fortschreibung A → B bzw. B → A
- KFG-Vertretungsbezeichnungen
- Hinweise/Nachrichten des Vertretungsplans
- visuelle Kennzeichnung von Vertretung, Entfall, Fachwechsel, Tausch usw.

## Dateien

Serverseitige Datenlogik:

```text
custom_components/sph/school_profiles/kfg.py
```

Frontend-Darstellung:

```text
custom_components/sph/static/school-profiles/kfg.js
```

Legacy-Bridges:

```text
custom_components/sph/static/school-hacks.js
custom_components/sph/static/school-hacks/kfg.js
```

Die Legacy-Dateien existieren nur für die Übergangsphase und verweisen auf die neue School-Profile-Implementierung.

## Ziel für die weitere Entwicklung

Das KFG-Profil soll mit der Zeit kleiner werden. Bei jeder neuen Regel ist zu prüfen, ob sie tatsächlich nur am KFG benötigt wird.

Beispiele für allgemeine Logik, die nicht dauerhaft im KFG-Profil bleiben sollte:

- allgemeine Fachnormalisierung
- allgemeines Matching eines SPH-Vertretungseintrags auf Datum/Stunde/Klasse
- Erzeugung von Kalenderterminen
- allgemeine A/B-Wochenberechnung, sofern sie sich schulübergreifend vereinheitlichen lässt

Nur echte KFG-Abweichungen bleiben im Profil.

## Entwickler

Die vollständige API und Anleitung für eigene Schul-Profile befindet sich unter:

[Schul-Profile entwickeln](../../SCHOOL_PROFILES_DEVELOPMENT.md)
