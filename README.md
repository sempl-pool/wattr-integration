# Wattr Pool Controller Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/YariSempl/wattr-integration.svg)](https://GitHub.com/YariSempl/wattr-integration/releases/)

Een Home Assistant custom integration voor Wattr zwembad controllers om waterkwaliteit te monitoren, temperatuur setpoints te regelen en energieverbruik te optimaliseren.

## Features

- **Waterkwaliteit Monitoring**: pH en RX (redox) waarden in real-time
- **Temperatuur Controle**: Watertemperatuur setpoint monitoring en aanpassing
- **Smart Mode**: Automatische energie-optimalisatie in-/uitschakelen  
- **Energie Optimalisatie**: Koppel externe sensoren (zoals energiemeters) om warmtepomp verbruik te verhogen of verlagen

## Installatie

### Via HACS (Aanbevolen)

1. Installeer [HACS](https://hacs.xyz) als je dat nog niet hebt
2. Voeg deze repository toe als custom repository in HACS:
   - Ga naar HACS → Integrations → ⋮ (drie puntjes) → Custom repositories
   - Voeg `YariSempl/wattr-integration` toe als Integration
3. Installeer "Wattr" vanuit HACS
4. Herstart Home Assistant
5. Voeg de integratie toe via Instellingen → Apparaten & Services → Integratie toevoegen → "Wattr"

### Handmatige Installatie

1. Download de `custom_components/wattr` map uit deze repository
2. Kopieer deze naar je `custom_components` directory in je Home Assistant configuratie
3. Herstart Home Assistant

## Configuratie

1. Haal je API key op van https://wattr.sempl.energy/tokenLogin
2. Vind je apparaat serienummer (meestal op het apparaat gedrukt)
3. In Home Assistant: Instellingen → Apparaten & Services → Integratie toevoegen → "Wattr"
4. Voer je API key en device ID in
5. Optioneel: koppel een sensor voor energie-optimalisatie

## Entiteiten

De integratie maakt de volgende entiteiten aan:

### Sensoren
- **Water pH**: Huidige pH niveau van je zwembadwater
- **Water RX**: Redox potentiaal 
- **Water Temperatuur**: Huidige watertemperatuur

### Nummer
- **Water Setpoint**: Stel de gewenste watertemperatuur in (20-35°C)

### Schakelaar
- **Smart Mode**: Zet automatische energie-optimalisatie aan/uit

## Energie Optimalisatie

Wanneer je een sensor koppelt (zoals je energiemeter) tijdens de setup, kan de integratie automatisch:
- **Verhogen** van warmtepomp verbruik wanneer overtollige energie beschikbaar is
- **Verlagen** van verbruik wanneer energie duur of beperkt is

Configureer de verhoog/verlaag drempelwaarden in de Wattr mobiele app.

## Support

Voor problemen met deze integratie, [open een issue](https://github.com/YariSempl/wattr-integration/issues) op GitHub.

Voor vragen over je Wattr apparaat zelf, neem contact op met [Wattr support](https://wattr.sempl.energy).

## Changelog

### v1.0.0
- Eerste release
- Ondersteuning voor pH, RX en temperatuur sensoren
- Temperatuur setpoint controle
- Smart mode schakelaar
- Energie optimalisatie via gekoppelde sensoren