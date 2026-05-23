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
version: 0.9
date: 2026-05-04
"""

import requests
import sys
import xml.etree.ElementTree as ET


def search_gbv_sru(
        searchField:str, 
        searchValue:str, 
        database="opac-de-627", 
        maximumRecords=20,
        recordSchema="marcxml"
        ) -> str:
    """Suche nach Datensätzen mit Werten searchValue im Feld searchField. Ausgabe der Ergebnisse als MARC21-XML.

    Für die Dokumentation der GBV-SRU-Schnittstelle nud erlaubten Werten zu den einzelnen Parametern vgl.:
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

    Returns:
        str: das als `recordSchema` angegebene Ausgabeformat (default MARC21-XML)  
    """

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

    return response.text


def show_display_fields(marc_xml:str, anzeigefelder:dict = {"ISBN": {"tag": "020", "code": "a"}, "Autor": {"tag": "100", "code": "a"}, "Titel": {"tag": "245", "code": "a"}, "Schlagworte": {"tag": "650", "code": "a"}}) -> None:
    """
    Zeigt die für die Anzeige vorgesehenen Felder für jeden Datensatz aus dem MARC-XML an.

    Aufbau des `anzeigefelder`-Dictionaries: {"Feldbezeichnung": {"tag": "XXX", "code": "Y"}, ...} mit `tag` als MARC-Feldnummer und Attribut des <datafield>-Elements und `code` als Unterfeldcode und Attribute des <subfied>-Elements.

    default der `anzeigefelder`: {"Titel": {"tag": "245", "code": "a"}, "Autor": {"tag": "100", "code": "a"}, "ISBN": {"tag": "020", "code": "a"}, "Schlagworte": {"tag": "650", "code": "a"}}

    Args:
        marc_xml (str): MARC-XML-String
        anzeigefelder (dict): Dictionary mit den anzuzeigenden Feldern und deren MARC-Feldnummern und Unterfeldcodes (default s. o.)

    Returns:
        None: Ausgabe der gewünschten Felder für jeden Datensatz auf der Konsole
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
           
            tag = anzeigefelder[field]["tag"]
            code = anzeigefelder[field]["code"]

            # Container zum Sammeln von Mehrfachfeldern
            values = []
           
            for datafield in record.findall(f".//marc:datafield[@tag='{tag}']", namespaces=namespaces):
                subfield_text = datafield.find(f"marc:subfield[@code='{code}']", namespaces=namespaces).text
                values.append(subfield_text)

            # Ausgabe der Inhalte aller datafields/subfields-Textinhalte zum Feld
            print(f"\t{field}: {", ".join(values)}")

        print("\n")


if __name__ == "__main__":

    menu = """
Bitte Suchfeld auswählen:
\t1: Titel
\t2: Autor
\t3: ISBN

\t0: Programmende\n
Wahl: """

    # Mapping der Benutzereingaben mit den Suchfeldern der GBV-SRU-Schnittstelle
    auswahl_mapping = {"1": "pica.tit", "2": "dc.author", "3": "pica.isb"}

    feldauswahl = ""

    while feldauswahl not in ["0", "1", "2", "3"]:
        
        feldauswahl = input(menu)
 
        if feldauswahl not in ["0", "1", "2", "3"]:
            print(f"\nFALSCHE EINGABE '{feldauswahl}': Bitte Zahl eines Menüpunktes eingeben.")

        if feldauswahl == "0":
            print("Programm wird beendet.")
            sys.exit(0)

    suchfeld = auswahl_mapping[feldauswahl]

    suchterm = None

    while suchterm is None:
        suchterm = input("Bitte Suchbegriff eingeben: ")

    marc_xml_suchergebnis = search_gbv_sru(suchfeld, suchterm)

    show_display_fields(marc_xml_suchergebnis)