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
    # TODO:
    # statt `opac-de-627` als Datenbank `gvk` nehmen für GVK-GBV-Katalog (vgl. https://uri.gbv.de/database/) ?
    # Sortierung: s. https://wiki.k10plus.de/spaces/K10PLUS/pages/27361342/SRU#SRU-Sortierung

    # TODO: searchField auf die Werte `pica.tit` für Titelstichwörter, `dc.author` für Autoren (oder pica.per? pica.psw?) und `pica.isb` für ISBN begrenzen

    gbv_sru_url = f"https://sru.k10plus.de/{database}?version=1.1&operation=searchRetrieve&query={searchField}%3D{searchValue}&maximumRecords={maximumRecords}&recordSchema={recordSchema}"

    try:
        response = requests.get(gbv_sru_url)
    except requests.exceptions as e:
        print(f"Fehler in der Verbindung: {e}")
        sys.exit(1)

    return response.text


# TODO: Funktion als Methode einer MARC21Record-Klasse implementieren, um die Notlösung mit den Tupeln für Marcxml-Record und Namespaces zu vermeiden; ist nicht sehr übersichtlich, aber für die Zwecke dieses Programms ausreichend
# -> zuerst eine Methode, um einen string zu einem MARC21-XML-Record zu parsen; muss nichts aufregends sein, könnte aber später für Fehlerbehandlung nützlich sein, z. B. um ungültige XML-Strings abzufangen

def parse_marcxml(marcxml_string:str) -> tuple[ET.Element, dict]:
    """Parst einen MARC21-XML-String und gibt das Wurzelelement zurück.

    Args:
        marcxml_string (str): Ein String im MARC21-XML-Format
    Returns:
        Tuple aus:
            ET.Element: Das Wurzelelement des geparsten MARC21-XML-Strings
            dict: Ein Dictionary mit den definierten Namespaces für die Suche in den XML-Elementen
    """
    try:
        root = ET.fromstring(marcxml_string)
        # Definiere die Namespaces
        namespaces = {
            'zs': 'http://www.loc.gov/zing/srw/',
            'marc': 'http://www.loc.gov/MARC21/slim'
        }
        return (root, namespaces)
    
    except ET.ParseError as e:
        print(f"Fehler beim Parsen des MARC21-XML-Strings: {e}")
        sys.exit(1)


def get_field_from_marcxml(marc_tuple:tuple, tag:str, code:str) -> list[str]:
    """Extrahiert die Werte eines bestimmten Feldes aus einem MARC21-XML-Record.

    Args:
        marc_tuple (tuple): Ein Tuple aus einem MARC21-XML-Record als ElementTree-Element und einem Dictionary mit den definierten Namespaces für die Suche in den XML-Elementen
        tag (str): tag-Attribut für datafield-Element, z. B. 100 für Autor, 245 für Titel, 650 für Schlagworte
        code (str): code-Attribut für subfield-Element

    Returns:
        list[str]: Eine Liste von Werten des angegebenen Feldes
    """

    marcxml = marc_tuple[0]
    namespaces = marc_tuple[1]

    values = []
    for datafield in marcxml.findall(f".//marc:datafield[@tag='{tag}']", namespaces=namespaces):
        for subfield in datafield.findall(f"marc:subfield[@code='{code}']", namespaces=namespaces):
            values.append(subfield.text)
    return values


# TODO:
# Main: starte Programm -> wonach suchen? -> Suchterme eingeben -> Suche durchführen -> Ergebnisse anzeigen


if __name__ == "__main__":


    for field, value in [("pica.tit","Python in a nutshell"), ("dc.author","Martelli, Alex"), ("pica.isb","9798341653597")]:
        print(f"Suche nach {field}: {value}")
        
        xml_string = search_gbv_sru(field, value, maximumRecords=1)
        
        marc_tuple = parse_marcxml(xml_string)

        marcxml = marc_tuple[0]
        namespaces = marc_tuple[1]

        for record in marcxml.findall(".//marc:record", namespaces=namespaces):
            print(f"ISBN: {", ".join(get_field_from_marcxml(marc_tuple, "020", "a"))}")
            print(f"Autor: {", ".join(get_field_from_marcxml(marc_tuple, "100", "a"))}")
            print(f"Titel: {", ".join(get_field_from_marcxml(marc_tuple, "245", "a"))}")
            print(f"Schlagworte: {", ".join(get_field_from_marcxml(marc_tuple, "650", "a"))}")
            print("\n")

            

        