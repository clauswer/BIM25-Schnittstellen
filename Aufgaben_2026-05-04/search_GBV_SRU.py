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

    #http://sru.k10plus.de/opac-de-627?version=1.1&operation=searchRetrieve&query=pica.tit%3DMcCarthyism&maximumRecords=10&recordSchema=mods

    try:
        response = requests.get(gbv_sru_url)
    except requests.exceptions as e:
        print(f"Fehler in der Verbindung: {e}")
        sys.exit(1)

    return response.text

# TODO:
# Parse Ergebnisse nach Titel -> Ausgabe der Felder je Titel
# Main: starte Programm -> wonach suchen? -> Suchterme eingeben -> Suche durchführen -> Ergebnisse anzeigen


if __name__ == "__main__":

    print("Test der Funktion, maximumRecords = 1:\n\n")

    for field, value in [("pica.tit","Python in a nutshell"), ("dc.author","Martelli, Alex"), ("pica.isb","0-596-10046-9")]:
        print(f"Suche nach {field}: {value}")
        xml_string = search_gbv_sru(field, value, maximumRecords=1)
        filename = "./tests/test_" + field.replace(".", "-") + ".xml"
        with open(filename, "w") as f:
            f.write(xml_string)
        print(f"Datei gespeichert als {filename}\n")