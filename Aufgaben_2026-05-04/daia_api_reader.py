#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programm zur Überprüfung der Verfügbarkeit von Medien an der SUB Göttingen via DAIA-Schnittstelle.
...
authors: Beata Lakenberg, Sebastian Scherübl, Claus Werner
license: MIT License
version: 1.0
date: 2026-05-24
"""

import requests
import sys
import xml.etree.ElementTree as ET


def output_xml(xml_found: list[dict]) -> None:
    """Gibt gefundene Exemplare aus.

    Args:
        xml_found (list[dict]): Liste mit Exemplardaten (label, epn, availability)
    """

    # jedes gefundene Exemplar einzeln ausgeben
    for i, item in enumerate(xml_found, start=1):

        print(f"\n{i}. Exemplar")

        # Signatur
        print("Signatur:", item["label"])

        # Eindeutige ID
        print("EPN:", item["epn"])

        # Verfügbarkeit als Liste ausgeben
        print("Verfügbarkeit:", ", ".join(item["availability"]))

    return


def find_variables_xml(xml_dataset: str) -> list[dict]:
    """Extrahiert Exemplardaten

    Args:
        xml_dataset (str): XML-Antwort der DAIA-Abfrage

    Returns:
        list[dict]: Liste mit Exemplardaten (label, epn, availability)
    """

    # XML-String in Baumstruktur umwandeln
    root = ET.fromstring(xml_dataset)

    # Ergebnisliste für alle Exemplare
    items = []

    # alle items durchlaufen
    for item in root.findall(".//{*}item"):

        # Signatur
        label = item.findtext(".//{*}label")

        # eindeutige ID
        epn = item.get("id")

        # Liste für Verfügbarkeitsinfos
        availability = []

        # available
        for i in item.findall(".//{*}available"):
            service = i.get("service")  # loan, presentation, interloan
            availability.append(f"{service}: available")

        # unavailable
        for j in item.findall(".//{*}unavailable"):
            service = j.get("service")
            availability.append(f"{service}: unavailable")

        # alles pro Exemplar speichern
        items.append({
            "label": label,
            "epn": epn,
            "availability": availability
        })

    return items


def load_xml(base_url: str, params: dict) -> str | None:
    """Lädt XML-Daten von der DAIA-API.

    Bei Verbindungsproblemen oder HTTP-Fehlern wird None zurückgegeben.

    Args:
        base_url (str): Basis-URL
        params (dict): Parameter der Abfrage

    Returns:
        str oder None: XML als Text oder None bei Fehler
    """

    try:
        # Request an DAIA-Server
        response_xml = requests.get(base_url, params=params)

    except Exception as e:
        print("\nFehler bei der Verbindung:")
        print(e)
        return None

    # Problem mit Server abfangen
    if response_xml.status_code != 200:
        print("Fehler: Anfrage fehlgeschlagen (Status:", response_xml.status_code, ")")
        return None

    # Encoding setzen z.B. wegen Umlauten
    response_xml.encoding = "utf-8"

    # XML als Text zurückgeben
    return response_xml.text


def build_sru_url(ppn: str, isil: str) -> tuple[str, dict]:
    """Erzeugt Basis-URL und Parameter für die DAIA-Schnittstelle.
    Args:
        ppn (str): eingegebene PPN
        isil (str): ISIL
    Returns:
        (base_url, params)(tuple)
    """

    # Basis-URL der DAIA Schnittstelle
    base_url = f"http://daia.gbv.de/isil/{isil}"

    # Parameter für die Anfrage
    params = {
        "id": f"ppn:{ppn}",
        "format": "xml"
    }

    return base_url, params


def main():
    """Hauptprogramm von Eingabe, Funktionsaufruf, Prüfung der Rückgabewerte und Ausgabe
    """

    print("Willkommen zur Verfügbarkeitsprüfung der SLUB Göttingen")

    print("\nHinweis: PPN muss insgesamt 9 oder 10 Zeichen/Ziffern haben. An der letzten Stelle darf eine Zahl, ein 'X' oder 'x' sein")

    # ISIL
    sigel_goettingen = "DE-7"

    # Eingabe
    ppn = input("Geben sie die gesuchte PPN ein:")

    # nur Zahlen bzw. auf letzter Stelle 'X' oder 'x' und richtige Länge erlauben
    if len(ppn) not in (9, 10):
        print("Fehler: PPN ist falsch! Bitte beachte den vorherigen Hinweis!")
        return
        # Letzte Stelle darf Ziffer oder 'X', 'x' sein
    if not ppn[:-1].isdigit() or not (ppn[-1].isdigit() or ppn[-1] == 'X' or ppn[-1] == 'x'):
        print("Fehler: PPN ist falsch! Bitte beachte den vorherigen Hinweis!.")
        return

    # URL und Parameter erstellen
    base_url, params = build_sru_url(ppn, sigel_goettingen)

    print("\nErzeugte URL:")
    print(requests.Request("GET", base_url, params=params).prepare().url)

    # XML von Server laden
    xml_dataset = load_xml(base_url, params)

    # wenn Anfrage fehlgeschlagen ist, abbrechen
    if xml_dataset is None:
        print("Zugriffsproblem.")
        return

    # XML auswerten
    xml_found = find_variables_xml(xml_dataset)

    # keine Exemplare gefunden
    if not xml_found:
        print("Keine Exemplare gefunden.")
        return

    # Ergebnisse ausgeben
    output_xml(xml_found)


# Programmstart
if __name__ == "__main__":
    main()
