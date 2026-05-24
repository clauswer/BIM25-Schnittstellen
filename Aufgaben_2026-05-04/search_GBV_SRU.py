#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programm zur Suche im GBV über die SRU-Schnittstelle.
Deren Dokumentation vgl.: https://verbundwiki.gbv.de/display/VZG/SRU 

Mögliche Suchen nach
- Titelstichwörtern
- Autoren
- ISBN

Ausgabe:
ISBN, Autor, Titel, Schlagworte

authors: Beata Lakenberg, Sebastian Scherübl, Claus Werner
license: MIT License
version: 1.0
date: 2026-05-24
"""

import requests
import sys
import xml.etree.ElementTree as ET


def search_gbv_sru(
        searchField:str, 
        searchValue:str, 
        database="opac-de-627", 
        maximumRecords=20,
        recordSchema="marcxml",
        debug=False
        ) -> str:
    """Suche nach Datensätzen mit Werten searchValue im Feld searchField. Ausgabe der Ergebnisse als MARC21-XML.

    Für die Dokumentation der GBV-SRU-Schnittstelle und erlaubten Werten zu den einzelnen Parametern vgl.:
    - für `searchField`: die SRU-Explain-Record der entspr. Datenbank, z. B. https://sru.k10plus.de/opac-de-627
    - für `database`: https://wiki.k10plus.de/spaces/K10PLUS/pages/27361342/SRU#SRU-Datenbanken 
    - für `maximumRecords`:  https://wiki.k10plus.de/spaces/K10PLUS/pages/27361342/SRU#SRU-Suchabfrage 
    - für `recordSchema`: https://wiki.k10plus.de/spaces/K10PLUS/pages/27361342/SRU#SRU-Formate

    Args:
        searchField (str): Das zu durchsuchende Datenfeld
        searchValue (str): Der zu suchende Wert im Suchfeld
        database (str): zu durchsuchende Datenbank (default opac-de-627)
        maximumRecords (int): Maximale Anzahl wiedergegebener Treffer (default 20)
        recordSchema (str): Ausgabeformat (default marcxml)
        debug (bool): Debug-Ausgabe der tatsächlichen URL (default False)

    Returns:
        str: das als `recordSchema` angegebene Ausgabeformat (default MARC21-XML)  
    """

    # Bei der suche Nach Autoren im Schema Nachname, Vorname wird der Name durch das Leerzeichen nach dem Komma nicht erkannt; bei der Suche nach Titeln stört das Leerzeichen zwischen Wörtern nicht. Daher ersetzen von ", " durch "," in searchValue, um die Autoren-Suche zu ermöglichen.
    searchValue = searchValue.replace(", ", ",")  

    params = {"version": "1.1",
              "operation": "searchRetrieve",
              "query": f"{searchField}={searchValue}",
              "maximumRecords": maximumRecords,
              "recordSchema": recordSchema}

    gbv_sru_url = f"https://sru.k10plus.de/{database}"

    try:
        response = requests.get(gbv_sru_url, params=params)
    except requests.exceptions as e:
        print(f"Fehler in der Verbindung: {e}")
        sys.exit(1)

    if debug:
        print(response.url)  # Debug-Ausgabe der tatsächlichen URL

    # Sicherstellen, dass die Antwort als UTF-8 dekodiert wird
    response.encoding = response.apparent_encoding  

    return response.text


def show_display_fields(
        marc_xml:str, 
        anzeigefelder:dict = {
            "ISBN": {"tag": ["020"], "code": ["a"]}, 
            "Autor": {"tag": ["100"], "code": ["a"]}, 
            "Titel": {"tag": ["245"], "code": ["a", "b"]}, 
            "Schlagworte": {"tag": ["650", "689"], "code": ["a"]}
            }
        ) -> None:
    """
    Zeigt die für die Anzeige vorgesehenen Felder für jeden Datensatz aus dem MARC-XML an.

    Aufbau des `anzeigefelder`-Dictionaries: {"Feldbezeichnung": {"tag": ["XXX"], "code": ["Y"]}, ...} mit `tag` als MARC-Feldnummer und Attribut des <datafield>-Elements und `code` als Unterfeldcode und Attribute des <subfied>-Elements.

    default der `anzeigefelder`: {
            "ISBN": {"tag": ["020"], "code": ["a"]}, 
            "Autor": {"tag": ["100"], "code": ["a"]}, 
            "Titel": {"tag": ["245"], "code": ["a", "b"]}, 
            "Schlagworte": {"tag": ["650", "689"], "code": ["a"]}
            }

    Args:
        marc_xml (str): MARC-XML-String
        anzeigefelder (dict): Dictionary mit den anzuzeigenden Feldern und deren MARC-Feldnummern und Unterfeldcodes jeweils in Listen (default s. o.)

    Returns:
        None: Ausgabe der gewünschten Felder und Feldinhalte für jeden Datensatz auf der Konsole
    """ 

    # Counter für Numerieren der angezeigten Ergebnisse
    counter = 1

    # MARC-XML parsen
    root = ET.fromstring(marc_xml)

    # Namespaces im MARC21-XML
    namespaces = {"zs":"http://www.loc.gov/zing/srw/",
                  "marc": "http://www.loc.gov/MARC21/slim"}

    print(f"\nAnzahl der gefundenen Datensätze: {root.find('.//zs:numberOfRecords', namespaces=namespaces).text}\n")

    # Iterieren durch records und auszugebende Felder
    for record in root.findall(".//marc:record", namespaces=namespaces):
        print(f"{counter}. Treffer:")
        counter += 1
        for field in anzeigefelder:

            # Container zum Sammeln von Mehrfachfeldern
            values = []

            for tag in anzeigefelder[field]["tag"]:
                for code in anzeigefelder[field]["code"]:
                    for value in record.findall(f".//marc:datafield[@tag='{tag}']/marc:subfield[@code='{code}']", namespaces=namespaces):
                        values.append(value.text)

            # Ausgabe der Inhalte aller datafields/subfields-Textinhalte zum Feld
            print(f"\t{field}: {", ".join(values)}")

        print("\n")


def choose_search_field(
        auswahl_mapping:list = [("Titel", "pica.tit"), ("Autor:in", "dc.author"), ("ISBN", "pica.isb")]
        ) -> str:
    """Ausgabe des Auswahlmenüs auf dem Terminal und Rückgabe des Suchfelds entsprechend der Benutzereingabe.

    Die Reihenfolge der Felder im auswahl_mapping bestimmt die Nummerierung der Menüoptionen.
    "0" ist immer die Option zum Beenden des Programms.

    default des auswahl_mapping: [("Titel", "pica.tit"), ("Autor:in", "dc.author"), ("ISBN", "pica.isb")]

    Args:
        auswahl_mapping (list): Liste mit Tupeln aus ("Feldbezeichnung", "Suchfeld"); Suchfeld laut https://sru.k10plus.de/opac-de-627 (default s. o.)

    Returns:
        str: das vom Benutzer ausgewählte Suchfeld laut https://sru.k10plus.de/opac-de-627
    """

    feldauswahl = ""

    auswahlwerte = [str(i) for i in range(len(auswahl_mapping) + 1)]

    while feldauswahl not in auswahlwerte:
        print("Bitte Suchfeld auswählen:")

        for index, (feldbezeichnung, suchfeld) in enumerate(auswahl_mapping, start=1):
            print(f"\t{index}: {feldbezeichnung}")

        print("\n\t0: Programmende\n")

        feldauswahl = input("Wahl: ")

        if feldauswahl not in auswahlwerte:
            print(f"\nFALSCHE EINGABE '{feldauswahl}': Bitte Zahl eines Menüpunktes eingeben.")

        if feldauswahl == "0":
            print("Programm wird beendet.")
            sys.exit(0)

    return auswahl_mapping[int(feldauswahl) - 1][1]  # Rückgabe des Suchfelds entsprechend der Benutzereingabe


if __name__ == "__main__":

    # Suchfeld bestimmen
    suchfeld = choose_search_field()

    # Suchterm bestimmen
    suchterm = input("Bitte Suchbegriff eingeben: ")

    # Suche durchführen
    marc_xml_suchergebnis = search_gbv_sru(suchfeld, suchterm, debug=False)

    # Ergebnisse anzeigen
    show_display_fields(marc_xml_suchergebnis)