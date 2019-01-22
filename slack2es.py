#!/usr/bin/env python
import click
from elasticsearch import Elasticsearch
from datetime import datetime
import json
import os.path, os
import copy

@click.command()
@click.option('--es-url', default='http://localhost:9200/')
@click.argument('folder', type=click.Path(exists=True))
def slack2es(es_url, folder):
    es = Elasticsearch(es_url)
    channel = os.path.basename(folder)
    
    for file in os.listdir(folder):
        index(es, channel, folder, file)
    print('Done!')

def index(es, channel, folder, filename):
    print('indexing {}'.format(filename))
    with open(os.path.join(folder, filename)) as file:
        data = json.load(file)

    for message in data:
        attachments = message.get('attachments', [])
        reactions = message.get('reactions', [])
        ts = float(message['ts'])*1000
        message['ts'] = int(ts)

        for msg_attachment in [{**attachment, 'channel': channel, 'type': 'attachment', 'ts': message['ts'], 'msg_text': message['text'], 'msg_user': message.get('username')} for attachment in attachments]:
            es.index(index='slack', doc_type='slack', 
                    body=msg_attachment)
        
        for reaction in [{**reaction, 'type': 'reaction', 'channel': channel, 'ts': message['ts'], 'msg_text': message['text'], 'msg_user': message.get('username')} for reaction in reactions]:
            es.index(index='slack', doc_type='slack', 
                    body=reaction)      

        es.index(index='slack', doc_type='slack', 
            body={**message, 'type': 'message', 'channel': channel}
            )

    print('Done indexing {}'.format(filename))


if __name__ == "__main__":
    slack2es()
