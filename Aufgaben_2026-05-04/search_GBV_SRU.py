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
# TODO: lxml statt xml nutzen?

anzeigefelder = {"Titel": {"tag": "245", "code": "a"}, "Autor": {"tag": "100", "code": "a"}, "ISBN": {"tag": "020", "code": "a"}, "Schlagworte": {"tag": "650", "code": "a"}}


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


def show_display_fields(marc_xml:str, anzeigefelder:dict) -> None:
    """
    Zeigt die für die Anzeige vorgesehenen Felder für jeden Datensatz aus dem MARC-XML an.

    Aufbau des `anzeigefelder`-Dictionaries: {"Feldbezeichnung": {"tag": "XXX", "code": "Y"}, ...} mit `tag` als MARC-Feldnummer und Attribut des <datafield>-Elements und `code` als Unterfeldcode und Attribute des <subfied>-Elements.

    Args:
        marc_xml (str): MARC-XML-String
        anzeigefelder (dict): Dictionary mit den anzuzeigenden Feldern und deren MARC-Feldnummern und Unterfeldcodes

    Returns:
        None: Ausgabe der gewünschten Felder für jeden Datensatz auf der Konsole
    """

    # MARC-XML parsen
    root = ET.fromstring(marc_xml)

    namespaces = {"zs":"http://www.loc.gov/zing/srw/",
                  "marc": "http://www.loc.gov/MARC21/slim"}
    
    for record in root.findall(".//marc:record", namespaces=namespaces):
        for field in anzeigefelder:
           
            tag = anzeigefelder[field]["tag"]
            code = anzeigefelder[field]["code"]
            values = []
           
            for datafield in record.findall(f".//marc:datafield[@tag='{tag}']", namespaces=namespaces):
                subfield_text = datafield.find(f"marc:subfield[@code='{code}']", namespaces=namespaces).text
                values.append(subfield_text) #TODO: kommen Subfields in einem datafield sicher nur 1x pro code vor?

            # Ausgabe der Inhalte aller datafields/subfields-Textinhalte zum Feld
            print(f"\t{field}: {", ".join(values)}")

        print("\n")



# TODO:
# Main: starte Programm -> wonach suchen? -> Suchterme eingeben -> Suche durchführen -> Ergebnisse anzeigen


if __name__ == "__main__":


    for field, value in [("pica.tit","Python in a nutshell"), ("dc.author","Martelli, Alex"), ("pica.isb","9798341653597")]:
        print(f"Suche nach {field}: {value}")
        
        xml_string = search_gbv_sru(field, value, maximumRecords=1)
        
        show_display_fields(xml_string, anzeigefelder)
            

        