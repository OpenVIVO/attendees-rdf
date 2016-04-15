#!/usr/bin/env/python

"""
    attendees2vivo.py -- Read Attendee data, make VIVO RDF

    Perhaps this is a "sufficient" draft -- including the features needed for OpenVIVO.

    If the person has an orcid, we make a person entity, otherwise we make a named vcard entity

"""

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDFS, RDF, XSD
import logging

__attendee__ = "Michael Conlon"
__copyright__ = "Copyright 2016 (c) Michael Conlon"
__license__ = "Apache License 2.0"
__version__ = "0.02"

#   Constants

uri_prefix = 'http://openvivo.org/a/doi'
date_prefix = 'http://openvivo.org/a/date'
attendee_prefix = 'http://openvivo.org/a/orcid'
vcard_prefix = 'http://openvivo.org/a/vcard'
orcid_prefix = 'http://orcid.org/'

VIVO = Namespace('http://vivoweb.org/ontology/core#')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
OBO = Namespace('http://purl.obolibrary.org/obo/')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')

# Setup logging

logging.basicConfig()

#   Helper functions


def make_attendee(data_line):
    attendee = dict(zip(['full_name', 'company', 'orcid', 'optout'], data_line.split('\t')))
    
    attendee['optout'] = attendee['optout'].strip('\n')
    if attendee['optout'] != 'No':
        return None

    name_parts = [x.strip('.') for x in attendee['full_name'].split(' ')]
    if len(name_parts) == 1:
        attendee['family_name'] = name_parts[0]
        attendee['given_name'] = ''
        attendee['additional_name'] = ''
    elif len(name_parts) == 2:
        attendee['given_name'] = name_parts[0]
        attendee['additional_name'] = ''
        attendee['family_name'] = name_parts[1]
    elif len(name_parts) == 3:
        attendee['given_name'] = name_parts[0]
        attendee['additional_name'] = name_parts[1]
        attendee['family_name'] = name_parts[2]
    else:
        attendee['given_name'] = name_parts[0]
        attendee['additional_name'] = name_parts[1]
        attendee['family_name'] = name_parts[2:]

    attendee['full_name'] = attendee['family_name'] + ', ' + attendee['given_name'] + ' ' + attendee['additional_name']
    attendee['full_name'].strip()

    attendee['orcid'] = attendee['orcid'].strip()
    attendee['orcid'] = attendee['orcid'].replace('http://orcid.org/', '')
    attendee['orcid'] = attendee['orcid'].replace('orcid.org/', '')
    attendee['orcid'] = attendee['orcid'].strip('/')
    if len(attendee['orcid']) > 0 and attendee['orcid'][0] != '0':
        raise ValueError(attendee)

    return attendee


def make_attendee_rdf(attendee, event_uri):
    """
    Given an attendee, make a person if they have an orcid, otherwise make a vcard

    :param attendee: a dict containing the attendee's data
    :return: triples added to graph
    """

    g = Graph()

    if 'orcid' in attendee and len(attendee['orcid']) > 0:
        print attendee['orcid']

        attendee_uri = URIRef(attendee_prefix + attendee['orcid'])
        g.add((attendee_uri, RDF.type, FOAF.Person))
        g.add((attendee_uri, RDFS.label, Literal(attendee['full_name'].strip())))

        orcid_uri = URIRef(orcid_prefix + attendee['orcid'])
        g.add((orcid_uri, RDF.type, OWL.Thing))
        g.add((attendee_uri, VIVO.orcidId, orcid_uri))

        #   Make a vcard for the attendee.  The vcard has the name of the attendee

        vcard_uri = URIRef(str(attendee_uri) + '-vcard')
        g.add((attendee_uri, OBO.ARG_2000028, vcard_uri))
        g.add((vcard_uri, RDF.type, VCARD.Individual))
        name_uri = URIRef(str(vcard_uri) + '-name')
        g.add((name_uri, RDF.type, VCARD.Name))
        g.add((vcard_uri, VCARD.hasName, name_uri))
        if len(attendee['given_name']) > 0:
            g.add((name_uri, VCARD.givenName, Literal(attendee['given_name'])))
        if len(attendee['family_name']) > 0:
            g.add((name_uri, VCARD.familyName, Literal(attendee['family_name'])))
        if len(attendee['additional_name']) > 0:
            g.add((name_uri, VCARD.additionalName, Literal(attendee['additional_name'])))

        # Link attendee to the conference through a role

        role_uri = URIRef(str(attendee_uri) + '-' + str(event_uri))
        g.add((role_uri, RDF.type, VIVO.ResearcherRole))
        g.add((role_uri, RDFS.label, Literal("Registrant")))
        g.add((attendee_uri, OBO.RO_0000053, role_uri))
        g.add((role_uri, OBO.BFO_0000054, event_uri))

    return g


#   Main starts here

if __name__ == '__main__':
    attendees_graph = Graph()
    event_uri = URIRef('http://openvivo.org/a/eventFORCE2016')
    count = 0
    orcid_count = 0
    f = open('attendees.txt', 'rU')
    for line in f:
        conference_attendee = make_attendee(line)
        if conference_attendee is not None:
            count += 1
            if count % 10 == 0:
                print count
            attendee_graph = make_attendee_rdf(conference_attendee, event_uri)
            print len(attendee_graph)
            if len(attendee_graph) > 0:
                orcid_count += 1
                attendees_graph += attendee_graph
    f.close()
    print orcid_count, "Attendees with ORCiD"
    print "Write", len(attendees_graph), "triples to file"
    triples_file = open('attendees.rdf', 'w')
    print >>triples_file, attendees_graph.serialize(format='n3')
    triples_file.close()
