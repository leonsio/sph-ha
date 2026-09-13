# SPH TRMNL 7.5 DIY

ESPHome-Konfiguration für ein 7,5"-E-Paper-Dashboard mit Daten aus dem
**Schulportal Hessen** über Home Assistant.

Die Konfiguration stellt unter anderem dar:

- Startseite mit Uhrzeit, Wetter, Tagesstundenplan, Hausaufgaben und nächsten Arbeiten
- Wochenstundenplan mit A/B-Wochenlogik
- Wetterseite mit aktueller Wetterlage, 24-Stunden- und Mehrtagesvorhersage
- Batteriestatus und WLAN-Signal
- Seitenauswahl über drei Hardware-Taster

Hauptdatei:

```text
sph-trmnl-7.5-diy.yaml
```

## Voraussetzungen

### Home Assistant

Es wird eine laufende Home-Assistant-Installation mit aktivierter ESPHome-Integration benötigt.

Die ESPHome-Konfiguration liest ihre Daten über die native Home-Assistant-API ein.

### ESPHome

Die Konfiguration ist für einen **ESP32-S3** mit Arduino-Framework ausgelegt und wurde mit einer aktuellen ESPHome-Version entwickelt.

Benötigt werden insbesondere die ESPHome-Komponenten:

- `waveshare_epaper`
- `homeassistant`
- `json`
- `font`
- `sntp`
- `adc`
- `wifi_signal`

Für das Laden der über `gfonts://` eingebundenen Schriften muss der ESPHome-Compiler Internetzugriff besitzen.

## Zwingende Voraussetzung: sph-ha

Für Stundenplan, Hausaufgaben und Leistungskontrollen wird die Home-Assistant-Custom-Integration **sph-ha** benötigt:

https://github.com/leonsio/sph-ha

`sph-ha` bindet das **Schulportal Hessen** in Home Assistant ein und stellt unter anderem die Module **Stundenplan**, **Mein Unterricht** und **Lerngruppen** bereit.

Die Installation erfolgt laut sph-ha-Dokumentation über HACS als benutzerdefiniertes Repository in der Kategorie **Integration**. Anschließend wird unter:

```text
Einstellungen → Geräte & Dienste → Integration hinzufügen
```

die Integration **Schulportal Hessen** eingerichtet.

Für jedes Kind wird in `sph-ha` ein eigener Eintrag angelegt. Unter anderem werden benötigt:

- Schulnummer
- SPH-Benutzername
- SPH-Passwort
- Name des Kindes
- Kürzel des Kindes

Dieses Projekt verwendet die JSON-Sensoren aus `sph-ha`.

Beispiel für:

```yaml
substitutions:
  child_name: maxim
  child_short: mk
```

werden folgende Home-Assistant-Entities erwartet:

```text
sensor.stundenplan_maxim_mk_json
sensor.mein_unterricht_maxim_mk_json
sensor.lerngruppen_maxim_mk_json
```

Die ESPHome-Konfiguration greift jeweils auf das Attribut:

```text
json
```

zu.

Beim Stundenplan wird ausschließlich `eigener_plan` dargestellt. Die vorhandene `wochenkennung` wird weiterhin für die A/B-Wochenlogik verwendet.

## Kind konfigurieren

Name und Kürzel werden nur einmal am Anfang der YAML-Datei definiert:

```yaml
substitutions:
  child_name: maxim
  child_short: mk
```

Für ein anderes Kind müssen nur diese beiden Werte geändert werden.

Die Werte müssen den Bestandteilen der von Home Assistant erzeugten Entity-IDs entsprechen, normalerweise also kleingeschrieben und ohne Leerzeichen.

Beispiel:

```yaml
substitutions:
  child_name: anna
  child_short: ak
```

führt unter anderem zu:

```text
sensor.stundenplan_anna_ak_json
sensor.mein_unterricht_anna_ak_json
sensor.lerngruppen_anna_ak_json
```

## Weitere benötigte Home-Assistant-Entities

Zusätzlich zu `sph-ha` erwartet die aktuelle YAML-Datei folgende Entities.

### Feiertagskalender

```text
calendar.deutschland_he
```

Verwendetes Attribut:

```text
message
```

Wenn der Feiertagskalender in der eigenen Home-Assistant-Installation anders heißt, muss die `entity_id` in der YAML angepasst werden.

### Sonnenaufgang und Sonnenuntergang

```text
sensor.sun_next_rising
sensor.sun_next_setting
```

Die Sensoren müssen ISO-8601-Zeitstempel liefern.

Falls diese Entities in der eigenen Home-Assistant-Konfiguration nicht vorhanden sind, müssen entsprechende Sensoren angelegt oder die Entity-IDs in der YAML geändert werden.

### Wetter-Hilfssensor

Die aktuelle Konfiguration erwartet:

```text
sensor.maxim_epaper_wetter
```

mit folgenden Attributen:

```text
condition
daily_json
hourly_json
outdoor_temperature
outdoor_humidity
pressure
wind_speed
apparent_temperature
indoor_temperature
indoor_humidity
```

Dieser Sensor gehört **nicht** zu `sph-ha` und muss in Home Assistant separat vorhanden sein.

Vor einer allgemeinen Verwendung des Projekts sollte entweder ein entsprechender Template-/Hilfssensor angelegt oder die Wetterquelle in `sph-trmnl-7.5-diy.yaml` an die eigene Home-Assistant-Konfiguration angepasst werden.

## Hardware

Die aktuelle YAML ist auf folgende Hardwarebelegung ausgelegt:

- ESP32-S3
- 7,5"-Waveshare-E-Paper, 800 × 480 Pixel
- ESPHome-Modell: `7.50inV2p`
- Landscape, Rotation `0`

### Display / SPI

| Funktion | GPIO |
|---|---:|
| SPI CLK | GPIO7 |
| SPI MOSI | GPIO9 |
| E-Paper CS | GPIO44 |
| E-Paper DC | GPIO10 |
| E-Paper RESET | GPIO38 |
| E-Paper BUSY | GPIO4 |

`BUSY` wird mit `inverted: true` verwendet.

### Taster

Die Taster arbeiten mit `INPUT_PULLUP` und schalten beim Drücken gegen GND.

| Funktion | GPIO |
|---|---:|
| Startseite | GPIO2 |
| Wochenplan | GPIO3 |
| Wetterseite | GPIO5 |

### Batterie

| Funktion | GPIO |
|---|---:|
| Batteriespannung ADC | GPIO1 |
| Battery Enable | GPIO6 |

Die Spannung wird in der YAML über eine hinterlegte Kalibrierung in Prozent umgerechnet. Diese Kennlinie kann je nach verwendetem Akku und Board angepasst werden müssen.

## Schriftarten

Die YAML verwendet sowohl automatisch über Google Fonts geladene Schriften als auch lokale TTF-Dateien.

### Automatisch über ESPHome geladen

Folgende Varianten von **Inter** werden über `gfonts://` eingebunden:

```text
Inter 600
Inter 700
```

Dafür müssen keine lokalen Dateien im Repository gespeichert werden. Beim Kompilieren benötigt ESPHome jedoch Internetzugriff.

### Lokal benötigte Schriftdateien

Folgende Dateien werden direkt aus dem Verzeichnis `fonts/` geladen:

```text
NotoSans-Bold.ttf
NotoSansMono-ExtraBold.ttf
MaterialDesignIconsDesktop.ttf
```

Wenn sich die YAML-Datei unter:

```text
/config/esphome/sph-trmnl-7.5-diy.yaml
```

befindet, müssen die Dateien hier liegen:

```text
/config/esphome/fonts/NotoSans-Bold.ttf
/config/esphome/fonts/NotoSansMono-ExtraBold.ttf
/config/esphome/fonts/MaterialDesignIconsDesktop.ttf
```

Empfohlene Verzeichnisstruktur:

```text
/config/esphome/
├── sph-trmnl-7.5-diy.yaml
├── secrets.yaml
└── fonts/
    ├── NotoSans-Bold.ttf
    ├── NotoSansMono-ExtraBold.ttf
    └── MaterialDesignIconsDesktop.ttf
```

Bezugsquellen:

- Noto Sans / Noto Sans Mono: https://fonts.google.com/noto
- Material Design Icons: https://pictogrammers.com/library/mdi/

Die Schriftdateien sind nicht Bestandteil dieses Projekts. Vor einer Weitergabe oder Aufnahme von Font-Dateien in das Repository müssen die jeweiligen Lizenzbedingungen beachtet werden.

## WLAN und secrets.yaml

Die YAML verwendet:

```yaml
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
```

Daher muss mindestens folgende Datei vorhanden sein:

```yaml
# /config/esphome/secrets.yaml

wifi_ssid: "MEIN-WLAN"
wifi_password: "MEIN-WLAN-PASSWORT"
```

## Sicherheit bei einem öffentlichen Repository

Die veröffentlichte YAML enthält keine WLAN-Passwörter oder API-Schlüssel direkt im Quelltext. Folgende Werte werden über `secrets.yaml` eingebunden:

```yaml
wifi_ssid: "..."
wifi_password: "..."
api_encryption_key: "..."
fallback_ap_password: "..."
```

Als Vorlage liegt `secrets.yaml.example` im Repository. Diese Datei kann lokal nach `secrets.yaml` kopiert und mit den eigenen Werten befüllt werden.

`secrets.yaml` mit echten Zugangsdaten darf nicht in ein öffentliches Git-Repository eingecheckt werden.

## Installation

1. **sph-ha installieren und einrichten.**
   Prüfen, dass die drei benötigten JSON-Sensoren für das gewünschte Kind vorhanden sind.

2. **ESPHome installieren.**
   ESPHome kann beispielsweise als Home-Assistant-Add-on verwendet werden.

3. **YAML kopieren.**
   `sph-trmnl-7.5-diy.yaml` nach `/config/esphome/` kopieren.

4. **Schriftarten installieren.**
   Die drei lokalen TTF-Dateien nach `/config/esphome/fonts/` kopieren.

5. **secrets.yaml konfigurieren.**
   WLAN-Zugangsdaten eintragen und für ein öffentliches Repository auch API-Key und Fallback-Passwort auslagern.

6. **Kind konfigurieren.**
   Am Anfang der YAML `child_name` und `child_short` einstellen.

7. **Home-Assistant-Entities prüfen.**
   Insbesondere:
   - sph-ha JSON-Sensoren
   - Wetter-Hilfssensor
   - Sonnenaufgang/-untergang
   - Feiertagskalender

8. **Hardware-Pins prüfen.**
   Bei abweichender Hardware die GPIO-Belegung vor dem Flashen anpassen.

9. **Konfiguration validieren und kompilieren.**
   In ESPHome zunächst die YAML validieren und anschließend installieren.

10. **Erstinstallation flashen.**
    Bei einem neuen ESP32-S3 empfiehlt sich die erste Installation über USB. Danach können Updates per OTA erfolgen.

## Aktualisierungsverhalten

Die Anzeige wird bewusst nicht bei jeder Änderung eines Home-Assistant-Sensors vollständig neu aufgebaut.

Aktuell gilt:

- Uhr auf der Startseite: jede Minute
- kompletter Inhalt der Startseite: alle 30 Minuten
- Wetterseite: alle 30 Minuten, wenn sichtbar
- Wochenplan: stündlich, wenn sichtbar
- Seitenwechsel: sofortige Aktualisierung
- vollständiger E-Paper-Refresh: `full_update_every: 120`

Die Home-Assistant-Werte werden zwischen den Display-Updates weiterhin über die API aktualisiert und beim nächsten Seitenaufbau verwendet.

## Stundenplanlogik

Die Stundenplananzeige nutzt:

```text
sensor.stundenplan_<name>_<kürzel>_json
```

und daraus:

```text
eigener_plan
wochenkennung
```

Beibehalten werden unter anderem:

- A/B-Wochen
- Wechsel der Wochenkennung beim Sprung in die Folgewoche
- Wochenende → nächste Schulwoche
- Freitag nach Ende der letzten Unterrichtsstunde → nächste Schulwoche
- Auswahl des nächsten Schultags auf der Startseite
- A/B-Badges einzelner Unterrichtsstunden
- parallele Unterrichtseinträge

## Hinweise

Dieses Projekt ist ein eigenständiges ESPHome-Projekt und keine offizielle Erweiterung des Schulportal Hessen.

Die Schulportal-Daten werden über das separate Projekt `sph-ha` bereitgestellt:

https://github.com/leonsio/sph-ha
