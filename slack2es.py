#!/usr/bin/env python
import click
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datetime import datetime
import json
import os.path, os
import copy
import itertools

@click.command()
@click.option('--es-url', default='http://localhost:9200/')
@click.argument('folder', type=click.Path(exists=True))
def slack2es(es_url, folder):
    es = Elasticsearch(es_url)
    channel = os.path.basename(folder)
    
    for file in os.listdir(folder):
        index(es, channel, folder, file)
    print('Done!')


def fix_ts(message):
    ts = float(message['ts'])*1000
    return {**message, 'ts': int(ts)}


def to_reaction_doc(channel, reaction, message):
    return {**reaction, 'type': 'reaction', 'channel': channel, 'ts': message['ts'], 'msg_text': message['text'], 'msg_user': message.get('username')}


def reaction_id(channel, reaction):
    return '-'.join(['reaction', channel, str(reaction['ts']), reaction['name']])


def to_message_doc(channel, message):
    return {**message, 'channel': channel}


def message_id(channel, message):
    return '-'.join([channel, str(message['ts'])])


def index(es, channel, folder, filename):
    print('indexing "{}"'.format(filename))
    with open(os.path.join(folder, filename)) as file:
        data = json.load(file)

    messages = [fix_ts(msg) for msg in data]
    reactions = itertools.chain.from_iterable([to_reaction_doc(channel, reaction, message) for reaction in message.get('reactions', [])] for message in messages)
    bulk(es, ({'_index': 'slack', '_type': 'slack', '_source': reaction, '_id': reaction_id(channel, reaction)} for reaction in reactions))
    bulk(es, ({'_index': 'slack', '_type': 'slack', '_source': to_message_doc(channel, message), '_id': message_id(channel, message)} for message in messages))
    print('Done indexing {}'.format(filename))


if __name__ == "__main__":
    slack2es()
