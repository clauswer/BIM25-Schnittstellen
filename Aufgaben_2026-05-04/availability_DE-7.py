#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programm um Verfügbarkeit eines Mediums anhand seiner PPN in der SUB Göttingen anzugeben

Abfrage: PPN - Bsp.: 225564580

Ausgabe der Anzahl der verfügbaren Exemplare je Service-Typ (presentation, loan, remote, interloan, openaccess).

authors: Beata Lakenberg, Sebastian Scherübl, Claus Werner
license: MIT License
version: 1.0
date: 2026-05-23
"""

import requests
import sys


def get_daia(ppn:str) -> dict:
    """Abfrage der Verfügbarkeit eines Mediums anhand seiner PPN in der SUB Göttingen. Ausgabe als JSON.

    Args:
        ppn (str): Die PPN des Mediums

    Returns:
        dict: DAIA-Informationen als JSON-Dict
    """
    
    url = f"https://paia.gbv.de/DE-7/daia?id=ppn:{ppn}&format=json"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Überprüfen, ob die Anfrage erfolgreich war
    except requests.exceptions.RequestException as e:
        print(f"Fehler in der Verbindung: {e}")
        sys.exit(1)

    response_json = response.json()

    if len(response_json["document"]) == 0:
        print(f"Keine Dokumente mit PPN {ppn} gefunden.")
        sys.exit(0)

    return response.json()



def count_availability(daia_document_json:dict) -> dict:
    """Zählt die Anzahl der verfügbaren Exemplare eines Mediums anhand einer DAIA-JSON-Antwort.

    Gibt die Anzahl der verfügbaren Exemplare je Service (vgl. https://gbv.github.io/daia/daia.html#services) zurück.

    Args:
        daia_document_json (dict): ein document-Object (vgl. dazu https://gbv.github.io/daia/daia.html#documents) aus der DAIA-Antwort als JSON-Dictionary
    Returns:
        dict: Ein Dictionary mit der Anzahl der verfügbaren Exemplare pro Service.
    """

    services_counts = {"presentation": 0, "loan": 0, "remote": 0, "interloan": 0, "openaccess": 0}

    for item in daia_document_json["item"]:
        for available in item["available"]:
            service_type = available["service"]
            services_counts[service_type] += 1

    return services_counts

def print_availability(ppn:str) -> None:
    """Gibt die Verfügbarkeit eines Mediums anhand seiner PPN in der SUB Göttingen aus.
    
    Args:
        ppn (str): Die PPN des Mediums
    
    Returns:
        None: Gibt die Verfügbarkeit des Mediums auf dem Terminal zurück.
    """

    daia_json = get_daia(ppn)


    for document in daia_json["document"]:
        try:
            print("\nVerfügbarkeit von:", document["about"], "\n")
        except KeyError:
            print("\nVerfügbarkeit von:", document["id"], "\n")

        availability_dict = count_availability(document)

        for service in availability_dict:
            print(service, ": ", availability_dict[service])


if __name__ == "__main__":
    ppn = input("Bitte geben Sie die PPN des Mediums ein: ")
    print_availability(ppn)