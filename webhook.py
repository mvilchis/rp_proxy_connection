from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions
import os
import ast
from flask import jsonify
from threading import Thread
from temba_client.v2 import TembaClient
import json

TOKEN_IO=os.getenv('TOKEN_IO', "")
TOKEN_MX=os.getenv('TOKEN_MX', "")
# Cliente io
io_client = TembaClient('rapidpro.io',TOKEN_IO)
#Cliente gob.mx
mx_client = TembaClient('rapidpro.datos.gob.mx', TOKEN_MX)

VARIABLES = [f.key for f in mx_client.get_fields().all()]
VALID_GROUPS= [group.name for group in mx_client.get_groups().all()]

app = FlaskAPI(__name__)


def migrate_contact(uuid,flow=None):
    contacts = io_client.get_contacts(uuid=uuid).all()
    if contacts:
        contact = contacts[0].serialize()
        fields_to_migrate = {}
        for var in VARIABLES:
            fields_to_migrate[var] = contact["fields"][var]
        groups = [g["name"] for g in contact["groups"] if g["name"] in VALID_GROUPS]
        try:
            mx_contact = mx_client.create_contact( name = contact["name"],
                                                   urns = contact["urns"],
                                                   fields = fields_to_migrate,
                                                   groups = groups
                                                  )
        except:
            mx_contacts = mx_client.get_contacts(urn=contact["urns"]).all()
            if mx_contacts:
                mx_contact = mx_contacts[0]
        if flow:
            mx_client.create_flow_start(flow=flow, contacts=[mx_contact.uuid],)


def create_thread(uuid,flow=None):
    thread = Thread(target = migrate_contact, args = (uuid,flow ))
    thread.start()
    return

@app.route("/", methods=['GET', 'POST'])
def receive_uuid():
    """
    List or create notes.
    """
    if request.method == 'GET':
        uuid = request.args.get('uuid')
        flow = request.args.get('flow')  if request.args.get('flow') else None
        create_thread(uuid,flow)
        return jsonify({"ok":"ok"})


@app.route("/search_contact",methods=['GET'])
def search_contact():
    """
    List or create notes.
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        contact = io_client.get_contacts(urn=['tel:+52'+tel]).all()
        if contact:
            return jsonify({"existe":"Si"})
        return jsonify({"existe":"No"})


if __name__ == "__main__":
    #Cambiar ip a 0.0.0.0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True,host="0.0.0.0", port= int(os.getenv('WEBHOOK_PORT', 5000)))
