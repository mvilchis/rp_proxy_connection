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

VARIABLES_MX = [f.key for f in mx_client.get_fields().all()]
VARIABLES_IO = [f.key for f in io_client.get_fields().all()]
VALID_GROUPS_MX= [group.name for group in mx_client.get_groups().all()]
VALID_GROUPS_IO= [group.name for group in io_client.get_groups().all()]

app = FlaskAPI(__name__)


def migrate_contact(tel, flow=None, to=None):

    if not to or to == "datos":
        origin_client = io_client
        dest_client = mx_client
        group_sufix = "ow"
        old_sufix = "tw"
        VALID_GROUPS = VALID_GROUPS_MX
        VARIABLES  = VARIABLES_MX
    if to == "io":
        origin_client = mx_client
        dest_client = io_client
        group_sufix = "tw"
        old_sufix = "ow"
        VALID_GROUPS = VALID_GROUPS_IO
        VARIABLES = VARIABLES_IO

    contacts = origin_client.get_contacts(urn=['tel:+52'+tel]).all()
    if contacts:
        contact = contacts[0].serialize()
        uuid = contact["uuid"]
        fields_to_migrate = {}
        for var in VARIABLES:
            if var in contact["fields"]:
                fields_to_migrate[var] = contact["fields"][var]


        #Now we 'll check if must change sufix tw to ow
        groups = []
        for g in contact["groups"]:
            if g["name"][-2:] == old_sufix: #Change to one way
                ow_name = g["name"][:-2]
                ow_name += group_sufix
                groups+= [ow_name] if ow_name in VALID_GROUPS else []
            else:
                groups += [g["name"]] if g["name"] in VALID_GROUPS else []
        try:
            new_contact = dest_client.create_contact( name = contact["name"],
                                                   urns = contact["urns"],
                                                   fields = fields_to_migrate,
                                                   groups = groups
                                                  )
        except:
            new_contacts = dest_client.get_contacts(urn=contact["urns"]).all()
            if to == "io" and new_contacts: #Then could exist but without variables
                new_contact = new_contacts[0]
                dest_client.update_contact(new_contact, name = contact["name"],
                                                   urns = contact["urns"],
                                                   fields = fields_to_migrate,
                                                   groups = groups
                                                  )
            if new_contacts:
                new_contact = new_contacts[0]
            else:
                new_contact = ""
        ### If we migrate then the campaigns must be updated
        old_groups = [g["name"]for g in contact["groups"] if g["name"][-2:] != group_sufix]
        origin_client.update_contact(contacts[0], groups = old_groups)
        if flow and new_contact:
            dest_client.create_flow_start(flow=flow, contacts=[new_contact.uuid],)


def create_thread(tel,flow=None, to=None):
    thread = Thread(target = migrate_contact, args = (tel,flow,to ))
    thread.start()
    return


#######################    API METHODS   ##########################

@app.route("/", methods=['GET', 'POST'])
def receive_uuid():
    """
    Migrate a contact from datos to io and io to datos
    Try to create the contact or update with the new values of variables
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        flow = request.args.get('flow')  if request.args.get('flow') else None
        to = request.args.get('to')  if request.args.get('to') else None
        create_thread(tel,flow, to)
        return jsonify({"ok":"ok"})


@app.route("/create_empty", methods=['GET', 'POST'])
def create_empty_contact():
    """
    Create an empty contact on io and add to unconfirmed group
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        try:
            io_client.create_contact(urns =["tel:+52"+tel],
                                     groups = ["cc9543a2-33ca-43cd-a3b7-4839b694605a"])
            return jsonify({"creado":"Si"}),201
        except:
            pass
        return jsonify({"creado":"No"}),404


@app.route("/search_contact",methods=['GET'])
def search_contact():
    """
    List or create notes.
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        contact = io_client.get_contacts(urn=['tel:+52'+tel]).all()
        if contact:
            return jsonify({"existe":"Si"}),201
        return jsonify({"existe":"No"}),404


@app.route("/start_flow",methods=['GET'])
def start_flow():
    """
    List or create notes.
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        flow = request.args.get('flow')
        to_rp = request.args.get('to')
        if to_rp == "io":
            client = io_client
        elif to_rp == "datos":
            client = mx_client
        else:
            return jsonify({}),404
        contact = client.get_contacts(urn=['tel:+52'+tel]).all()
        if contact:
            client.create_flow_start(flow=flow, contacts=[contact[0].uuid],)
            return jsonify({"Inicio_flow":"Si"}),201
        return jsonify({"Inicio_flow":"No"}),404


@app.route("/cancel",methods=['GET'])
def cancel_subscription():
    """
    Remove contact from all groups and
    add it to altopd
    parameters:
        tel: celnumber of contact
        to: site to remove from group
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        to_rp = request.args.get('to')
        if to_rp == "io":
            client = io_client
            group = "68e4077e-c794-4b76-9a61-afaa96180d36"
        elif to_rp == "datos":
            client = mx_client
            group = "08353c98-0f6a-41b1-9958-485a22e8dd91"
        else:
            return jsonify({}),404
        contact = client.get_contacts(urn=['tel:+52'+tel]).all()
        if contact:
            client.update_contact(contact=contact, groups=[group])
            return jsonify({}),201
        return jsonify({}),404



if __name__ == "__main__":
    #Cambiar ip a 0.0.0.0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True,host="0.0.0.0", port= int(os.getenv('WEBHOOK_PORT', 5000)))
