#!/usr/bin/env/python

"""
    event2vivo.py -- Make VIVO RDF for an event

"""

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDFS, RDF, XSD
import logging

__event__ = "Michael Conlon"
__copyright__ = "Copyright 2016 (c) Michael Conlon"
__license__ = "Apache License 2.0"
__version__ = "0.02"

#   Constants

date_prefix = 'http://openvivo.org/a/date'
event_prefix = 'http://openvivo.org/a/event'
vcard_prefix = 'http://openvivo.org/a/vcard'

VIVO = Namespace('http://vivoweb.org/ontology/core#')
BIBO = Namespace('http://purl.org/ontology/bibo/')
OBO = Namespace('http://purl.obolibrary.org/obo/')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')

# Setup logging

logging.basicConfig()

#   Helper functions


def make_event(data_line):
    """
    Given a line of data from a tab separated data file, return a dict containing the data for the event
    :param data_line:
    :return: dict
    """
    return dict(zip(['tag', 'label', 'url', 'start', 'end'], data_line.strip('\n').split('\t')))


def make_event_rdf(event):
    """
    Given an event (JSON), create VIVO RDF for the event

    :param event: a dict containing the event's data
    :return: triples added to graph
    """

    g = Graph()

    print event
    event_uri = URIRef(event_prefix + event['tag'])
    g.add((event_uri, RDF.type, BIBO.Conference))
    g.add((event_uri, RDFS.label, Literal(event['label'])))\

    #   Make a vcard for the event.  The vcard has the URL of the event

    vcard_uri = URIRef(str(event_uri) + '-vcard')
    g.add((event_uri, OBO.ARG_2000028, vcard_uri))
    g.add((vcard_uri, OBO.ARG_2000029, event_uri))
    g.add((vcard_uri, RDF.type, VCARD.Kind))
    url_uri = URIRef(str(vcard_uri) + '-url')
    g.add((vcard_uri, VCARD.hasURL, url_uri))
    g.add((url_uri, RDF.type, VCARD.URL))
    g.add((url_uri, VIVO.rank, Literal('1', datatype=XSD.integer)))
    g.add((url_uri, RDFS.label, Literal('Conference Home Page')))
    g.add((url_uri, VCARD.url, Literal(event['url'], datatype=XSD.anyURI)))

    # make datetime interval for the event

    dti_uri = URIRef(str(event_uri) + '-dti')
    g.add((dti_uri, RDF.type, VIVO.dateTimeInterval))
    g.add((event_uri, VIVO.dateTimeInterval, dti_uri))
    g.add((dti_uri, VIVO.start, URIRef(date_prefix + event['start'])))
    g.add((dti_uri, VIVO.end, URIRef(date_prefix + event['end'])))

    return g


#   Main starts here

if __name__ == '__main__':
    events_graph = Graph()
    count = 0
    f = open('events.txt', 'rU')
    for line in f:
        conference_event = make_event(line)
        if conference_event is not None:
            count += 1
            if count % 10 == 0:
                print count
            event_graph = make_event_rdf(conference_event)
            events_graph += event_graph
    f.close()
    print "Write", len(events_graph), "triples to file"
    triples_file = open('events.rdf', 'w')
    print >>triples_file, events_graph.serialize(format='n3')
    triples_file.close()
