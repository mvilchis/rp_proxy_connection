#! /usr/bin/env python
# -*- coding: utf-8 -*-
from elasticsearch import Elasticsearch
import os
import re
NUMBERS = {'primero':1, 'segundo':2, 'tercero':3, 'cuarto':4, 'uno':1, 'dos':2, 'tres':3, 'cuatro':4, 'cinco':5, 'seis':6, 'siete':7, 'ocho':8, 'nueve':9, 'diez':10, 'once':11, 'doce':12, 'trece':13, 'catorce':14, 'quince':15, 'dieciseis':16, 'diecisiete':17, 'dieciocho':18, 'diecinueve':19, 'veinte':20, 'ventiuno':21, 'veintidos':22, 'veintitres':23, 'veinticuatro':24, 'veinticinco':25, 'veintiseis':26, 'veintisiete':27, 'veintiocho':28, 'veintinueve':29, 'treinta':30, 'treinta y uno':31}
ARTICLES = ['de', 'el', 'la', 'del']
MONTHS = {'ene':1, 'feb': 2, 'mar':3, 'abr': '4', 'may':'5', 'jun': 6, 'jul': 7, 'agto': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic':12  }

REQUEST_STRING= "es.search(index= 'fechas', body = {'query' : {'fuzzy': {'name': {'value':'%s', 'fuzziness':5}}}})"
DAY=0
MONTH=1
YEAR = 2
ERROR = "error"
ERROR_DATE = "fecha no valida"
HITS_KEY = 'hits'
SOURCE_KEY = '_source'
elastic_port = int(os.getenv('ELASTIC_PORT'))
elastic_ip = os.getenv('ELASTIC_IP')
elasticsearch_url = "{ip}:{port}"
es = Elasticsearch([elasticsearch_url.format(ip=elastic_ip, port=elastic_port)])
## Method that intent search the pattern used, first will search locally,
## if not find a pattern then ask to elasticsearch server
def search_item(item):
    global es
    if not item.isdigit():
        if item in NUMBERS.keys():
            final_item = NUMBERS[item]
        elif item in MONTHS.keys():
            final_item = MONTHS[item]
        else:
            ##Check the hit
            result = es.search(index= 'fechas', body = {'query' :     {'fuzzy': {'name': {'value':str(item), 'fuzziness':8}}}})
            hits = result[HITS_KEY][HITS_KEY]
            if hits:
                final_item = hits[0][SOURCE_KEY]['number']
            else:
                final_item = ERROR
    else:
        final_item = item
    return final_item


def parse_list(date_list):
    if len(date_list) >= 3:
        if len(date_list) == 3:
           ## we assume (3 feb 2016) or (3 02 16) or (tres febrero dosmildieciseis)
           day = search_item(date_list[DAY])
           month = search_item(date_list[MONTH])
           year = search_item(date_list[YEAR])
           if day != ERROR and month != ERROR and year != ERROR:
              if year <= 99:
                  if year <= 50:
                      year += 2000
                  else:
                      year += 1900
              return str(day) + "/"+str(month) +"/"+ str(year)
           else:
              return ERROR_DATE
        else : #Then there are some articles
            date_string = ""
            items_found = 0
            for i in date_list:
               if i in ARTICLES:
                   continue
               else:
                   item_found = search_item(i)
                   if item_found != ERROR:
                       items_found += 1
                       date_string += str(item_found) + "/"
            if items_found == 3:
                return date_string[:-1]
            else:
                return ERROR_DATE


def parse_date(date):
    date = str(date)
    #Try to find wich char was used to divide the date
    date_list = re.split(' +',date.lower())
    if len(date_list)>= 3:
        return parse_list(date_list)
    else :
        date_list = re.split('-+',date.lower())
        if len(date_list)>= 3:
            return parse_list(date_list)
        else:
            date_list = re.split('/+',date.lower())
            if len(date_list) >= 3:
                return parse_list(date_list)
            else:
                date_list = date.lower().split('.')
                if len(date_list) >= 3:
                    return parse_list(date_list)
                else:
                    date_list = re.split('&+',date.lower())
                    if len(date_list) >= 3:
                        return parse_list(date_list)
                    else:
                        date_list = re.split('_+',date.lower())
                        if len(date_list) >= 3:
                            return parse_list(date_list)

    return ERROR_DATE
