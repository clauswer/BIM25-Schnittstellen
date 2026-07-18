#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Skript für Abfragen der OAI-PMH-Schnittstelle des OPUS Repository der TH Wildau.
Die Ergebnisse werden im oai_dc-Format (default) in einer Datei gesichert.

Für Parameter s.:
$python3 opus-wildau-oai-harvesting.py --help

authors: Beata Lakenberg, Sebastian Scherübl, Claus Werner
license: MIT License
version: 1.0
date: 2026-07-18
"""

import argparse
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import requests
import sys
import os
from typing import Union
from lxml import etree


@dataclass
class Oai_pmh_tools:
    """
    Methoden zum Parsen und Bearbeiten von XML-Daten aus OAI-Schnittstellen.
    """

    _namespaces = {'def': 'http://www.openarchives.org/OAI/2.0/'}

    def _find_element(oai_pmh_xml:str, element:str) -> Union[etree._Element, None]:
        """
        Private Methode zum Suchen nach beliebigen Elementen in der OAI-PMH-XML.

        Parameter:
            oai_pmh_xml (str): Die OAI-PMH-XML

        Returns:
            Gesuchtes Element oder None, wenn nicht vorhanden
        """

        root = etree.fromstring(oai_pmh_xml)
        return root.find(f".//def:{element}", namespaces=Oai_pmh_tools._namespaces)



    @staticmethod
    def resumptionToken_text(oai_pmh_xml:str) -> Union[str, None]:
        """
        Gibt den Text des resumptionToken-Elements zurück.

        Wird kein resumptionToken-Element gefunden, wird das Programm beendet. 

        Parameter:
            oai_pmh_xml (str): Die OAI-PMH-XML

        Returns:
            resumptionToken (str) oder None, wenn keiner vorhanden
        """

        try:
            root = etree.fromstring(oai_pmh_xml)
            return root.findtext(".//def:resumptionToken", namespaces=Oai_pmh_tools._namespaces)
        except Exception as e:
            print(f"Ein Fehler trat auf beim Parsen der xml nach dem resumptionToken:\n{e}")
            sys.exit(1)
    

    
    @staticmethod
    def find_error_element(oai_pmh_xml:str) -> Union[etree._Element, None]:
        """
        Sucht nach dem Error-Element in der OAI-PMH-XML.

        Parameter:
            oai_pmh_xml (str): Die OAI-PMH-XML

        Returns:
            error-Element als etree._Element-Objekt oder None, wenn nicht vorhanden
        """
        
        return Oai_pmh_tools._find_element(oai_pmh_xml, "error")



    @staticmethod
    def add_records(source_root_element:etree._Element, target_root_element:etree._Element) -> etree._Element:
            """
            Ergänzt die records eines OAI-PMH-XML unter dem ListRecords-Element einer anderen OAI-PMH-XML.

            Parameter:
                source_root_element (etree._Element): Quelle mit den zu ergänzenden record-Elementen
                target_root_element (etree._Element): Ziel mit dem ListRecords-Element, das mit den records ergänzt werden soll.

            Returns:
                etree._Element: das nun ergänzte target_root_elemen
            """
            
            listRecords_element = target_root_element.find(".//def:ListRecords", namespaces=Oai_pmh_tools._namespaces)
            for record in source_root_element.iterfind(".//def:record", namespaces=Oai_pmh_tools._namespaces):
                listRecords_element.append(record)

            return target_root_element

            

@dataclass
class Document_harvester:
    """
    Klasse für das Harvesting der OPUS OAI-Schnittstelle der TH Wildau.

    Parameter:
        from_date (str): Startdatum der Abfrage im Format YYYY-MM-DD
        until_date (str): Enddatum der Abfrage im Format YYYY-MM-DD
        metadata_format (str): Gewünschtes Lieferformat: oai_dc, marc21, epicur oder xMetaDissPlus
        url (str): Base-URL für die Abfrage
        querystring (str): Die gesamte URL für die Abfrage
        resumptionToken (str | None): resumptionToken für mehrteilige Antworten
        responses (list(requests.Responses)): Liste der Abfrageergebnisse als requests.Response-Objekte
    """

    # Attributes
    _from_date: str = field(init=True)
    _until_date: str = field(init=True)
    _metadata_format: str = field(init=True)
    _url: str = field(init=True)
    _querystring: str = field(init=False, default="")
    _resumptionToken: Union[str, None] = field(init=False, default="")    

    #  Getter und Setter
    @property
    def from_date(self):
        return self._from_date
    
    @property
    def until_date(self):
        return self._until_date
    
    @property
    def metadata_format(self):
        return self._metadata_format
    
    @property
    def url(self):
        return self._url

    @property
    def querystring(self):
        return self._querystring
    
    @querystring.setter
    def querystring(self, value):
        self._querystring = value

    @property
    def resumptionToken(self):
        return self._resumptionToken
    
    @resumptionToken.setter
    def resumptionToken(self, value):
        self._resumptionToken = value

    # Erstellen des querystrings beim Initiierung
    def __post_init__(self):
        self.querystring = f"{self.url}?verb=ListRecords&metadataPrefix={self.metadata_format}&from={self.from_date}&until={self.until_date}"     

    # Private Methoden
    def _update_resumptionToken(self, oai_pmh_xml:str) -> None:
        """
        Durchsucht eine OAI-PMH-Antwort nach dem resumptionToken. 
        Ist einer vorhanden, wird das Property resumptionToken aktualisiert.
        Ist keiner vorhanden, wird resumptionToken-Property = None gesetzt.

        Parameter:
            oai_pmh_xml (str): Die OAI-PMH-XML
        
        Returns:
            None
        """   

        self.resumptionToken = Oai_pmh_tools.resumptionToken_text(oai_pmh_xml)



    def _remove_resumptionToken_element(self, oai_pmh_root_element:etree._Element) -> etree._Element:
        """
        Entfernt das resumptionToken-Element aus der oai-pmh-xml

        Parameter:
            oai_pmh_root_element (etree._Element): das gesamte OAI-PMH-XML als lxml.etree._Element
        
        Returns:
            etree._Element: das gesamte OAI-PMH-XML ohne resumptionToken-Element
        """
        # TODO: Code dieser Funktion auch in eine Oai_pmh_tools-Methode packen?

        try:                
            namespaces = {'def': 'http://www.openarchives.org/OAI/2.0/'}

            resumptionToken_element = oai_pmh_root_element.find(".//def:resumptionToken", namespaces=namespaces)

            if resumptionToken_element is not None:
                listRecords_element = oai_pmh_root_element.find(".//def:ListRecords", namespaces=namespaces)
                listRecords_element.remove(resumptionToken_element)
            
            return oai_pmh_root_element
                       
        except Exception as e:
            print(f"Ein Fehler beim Entfernen des resumptionToken-Elements aus der xml:\n{e}")
            sys.exit(1)



    def _check_oai_pmh_error(self, oai_pmh_xml:str) -> None:
        """
        Prüft auf das Vorhandensein eines error-Elements in einer OAI-PMH-XML.
        
        Sollte eines vorhanden sein, wird sein Code und Text auf der Konsole ausgegeben und das Programm beendet.

        Parameter:
            oai_pmh_xml (str): String der OAI-PMH-XML
        
        Returns:
            None
        """   

        error_element = Oai_pmh_tools.find_error_element(oai_pmh_xml)

        if error_element is not None:
            print(f"\nFehler in der Abfrage der Schnittstelle:\n{error_element.get('code')}\n{error_element.text}")
            print(f"Abfrage war:\n{self.querystring}")
            sys.exit(1)



    def _fetch(self, parameter: dict) -> str:
        """
        Abfrage an die OAI-PMH-Schnittstelle via URL.

        _fetch() ruft den querystring auf und gibt den request.content als string zurück.
    
        Parameter:
            parameter (dict): Paramtere für die Abfrage an die OAI-PMH-Schnittstelle
        
        Returns:
            OAI-PMH-XML als String
        """

        try:
            response = requests.get(self.url, params=parameter)
        except Exception as e:
            print(f"\nFehler in der Verbindung:\n{e}")
            sys.exit(1)

        print(f"abgerufene URL: {response.url}")

        if response.status_code != 200:
            print(f"Fehler in der Abfrage:\nStatus-Code {response.status_code}")
            print(response.content)
            sys.exit(1)

        return response.content
    

    # Öffentliche Methoden
    def fetch_via_dates(self) -> str:
        """
        Abfrage an die OAI-PMH-Schnittstelle via URL für die Datums-Abfrage (from_date und until_date)

        Gibt den request.content als string zurück.
    
        Parameter:
            Keine
        
        Returns:
            OAI-PMH-XML als String
        """

        params = {
            "verb": "ListRecords",
            "metadataPrefix": self.metadata_format,
            "from": self.from_date,
            "until": self.until_date
        }

        return self._fetch(params)



    def fetch_via_resumptionToken(self) -> str:
            """
            Abfrage an die OAI-PMH-Schnittstelle via URL mittels resumptionToken.

            Gibt den request.content als string zurück.
        
            Parameter:
                Keine
            
            Returns:
                OAI-PMH-XML als String
            """

            params = {
                    "verb": "ListRecords",
                    "resumptionToken": self.resumptionToken
            }

            return self._fetch(params)



    def write(self, filename: Union[str, os.PathLike]) -> None:
        """
        Schreibt fetch-Ergebnisse in eine XML-Datei.
        
        Ergänzt die records in der XML, solange es einen resumptionToken in der Antwort gibt. 

        Die resumptionTokens werden vor dem Sichern in der Datei entfernt.

        Parameter:
            filename (str oder os.PathLike): Dateiname für die Abfrageergebnisse
        
        Returns:
            None
        """
        
        # Erster Aufruf von fetch() und Anlegen der xml-Datei
        print("Lade Daten.")
        xml_string = self.fetch_via_dates()

        #Update resumptionToken-Schalter
        self._update_resumptionToken(xml_string)

        #Parsen des xml-String mit lxml
        root = etree.fromstring(xml_string)

        # Entferne resumptionToken aus XML
        root = self._remove_resumptionToken_element(root)
        
        # Sichern der XML in Datei
        print(f"Sichere Daten unter: {filename}")
        tree = etree.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True, pretty_print=True)

        # Vorgehen wiederholen, bis es keinen resumptionToken mehr gibt
        while self.resumptionToken is not None and self.resumptionToken != "":

            print("ResumptionToken vorhanden. Lade weitere Datensätze.")

            new_xml_string = self.fetch_via_resumptionToken()

            #Update resumptionToken-Schalter
            self._update_resumptionToken(new_xml_string)

            #Parsen des xml-String mit lxml
            root_new_records = etree.fromstring(new_xml_string)

            # Entferne resumptionToken aus XML-String
            root_new_records = self._remove_resumptionToken_element(root_new_records)

            # Ergänzen der neuen Records im bereits angelegten file
            print(f"Ergänze Datensätze in Datei {filename}")

            # Laden und Parsen des files mit lxml
            tree_in_file = etree.parse(filename)
            root_in_file = tree_in_file.getroot()

            Oai_pmh_tools.add_records(root_new_records, root_in_file)

            # Sichern der XML in Datei
            tree_in_file.write(filename, encoding="utf-8", xml_declaration=True, pretty_print=True)
        
        print(f"Sichern der gesamte Abfrage in Datei {filename} beendet.")



def main() -> None:
    """
    Hauptmethode zum Ablauf des Programmes. 

    In der main() werden auch die Argumente aus der Konsole gealden und für die Übergabe an den Document_harvester aufbereitet.

    Parameter:
        keine

    Returns:
        None
    """

    # Parameter laden
    parser = argparse.ArgumentParser(description="OPUS OAI-Harvesting")

    parser.add_argument("-w", "--week", action="store_true", help="Abruf der Daten der letzten Woche")
    parser.add_argument("-m", "--month", action="store_true", help="Abruf der Daten des letzten Monats")
    parser.add_argument("-f", "--from_date", type=str, help="Startdatum im Format YYYY-MM-DD")
    parser.add_argument("-u", "--until_date", type=str, help="Enddatum im Format YYYY-MM-DD")
    parser.add_argument("--url", type=str, default="https://opus4.kobv.de/opus4-th-wildau/oai", help="OPUS OAI URL (default: https://opus4.kobv.de/opus4-th-wildau/oai)")
    parser.add_argument("--format", type=str, default="oai_dc", choices=["oai_dc", "marc21", "epicur", "xMetaDissPlus"], help="Metadatenformat für Ausgabe (default: oai_dc)")

    args = parser.parse_args()

    wochentage_list = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # from_ dateund until_date für Abruf der Daten der letzten Woche
    if args.week:
        today = datetime.today()
        today_weekday = today.weekday()  # Montag = 0, Sonntag = 6
        from_date = today - timedelta(days=today_weekday + 7)  # Datum des letzten Montags
        until_date = from_date + timedelta(days=6)  # Datum des letzten Sonntags

    # from_date und until_date für Abruf der Daten des letzten Monats
    elif args.month:    

        today = datetime.today()

        if today.month > 1:
            last_month = today.month - 1
        else: 
            last_month = 12

        if last_month == 12:
            last_months_year = today.year - 1
        else:
            last_months_year = today.year
        
        from_date = datetime(last_months_year, last_month, 1)
        until_date = datetime(last_months_year, last_month + 1, 1) - timedelta(days=1) # Datum des letzten Tages des letzten Monats wird berechnet durch das Datum des ersten Tages des aktuellen Monats minus 1 Tag, da letzte Tag unterschiedliche sein kann (28, 29, 30, 31).

    # Für extra angegebene Start- und Enddaten
    elif args.from_date and args.until_date:

        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d")
            until_date = datetime.strptime(args.until_date, "%Y-%m-%d")
        except ValueError:
            print("Ungültiges Datumsformat oder ungültiges Datum. Bitte verwenden Sie YYYY-MM-DD.")
            exit(1)


    else:
        print("Bitte verwenden Sie einen der folgenden Parameter:\n--week\n--month\n--from_date YYYY-MM-DD UND --until_date YYYY-MM-DD")
        exit(1)


    from_date = from_date.date()
    until_date = until_date.date()

    print(f"Abruf der Daten von {wochentage_list[from_date.weekday()]}, {from_date} bis {wochentage_list[until_date.weekday()]}, {until_date}")

    harvesting = Document_harvester(from_date, until_date, args.format, args.url)
    print(f"Abfrage-URL:\n{harvesting.querystring}")
    #harvesting.fetch()
    harvesting.write("test.xml")

if __name__ == "__main__":
    main()
