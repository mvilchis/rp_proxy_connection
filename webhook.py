from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions
import os
import ast, re
from flask import jsonify
from threading import Thread
from temba_client.v2 import TembaClient
import json
from Constants import *

app = FlaskAPI(__name__)


def migrate_contact(tel, flow=None, to=None):

    if not to or to == DATOS_SITE:
        origin_client = io_client
        dest_client = mx_client
        group_sufix = ONE_WAY
        old_sufix = TWO_WAY
        VALID_GROUPS = VALID_GROUPS_MX
        VARIABLES = VARIABLES_MX
    if to == IO_SITE:
        origin_client = mx_client
        dest_client = io_client
        group_sufix = TWO_WAY
        old_sufix = ONE_WAY
        VALID_GROUPS = VALID_GROUPS_IO
        VARIABLES = VARIABLES_IO

    contacts = origin_client.get_contacts(urn=['tel:+52' + tel]).all()
    if contacts:
        contact = contacts[0].serialize()
        uuid = contact["uuid"]
        fields_to_migrate = {}
        for var in VARIABLES:
            if var in contact["fields"] and contact["fields"][var]:
                fields_to_migrate[var] = contact["fields"][var]
                is_date = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T',
                                   fields_to_migrate[var])
                rare_format = re.match(r'-[0-9]{2}:[0-9]{2}',
                                       fields_to_migrate[var][-6:])
                if is_date and rare_format:
                    fields_to_migrate[var] = fields_to_migrate[var][:-6]

        #Now we 'll check if must change sufix tw to ow
        groups = []
        for g in contact["groups"]:
            if g["name"][-2:] == old_sufix:  #Change to one way
                ow_name = g["name"][:-2]
                ow_name += group_sufix
                groups += [ow_name] if ow_name in VALID_GROUPS else []
            else:
                groups += [g["name"]] if g["name"] in VALID_GROUPS else []
        try:
            new_contact = dest_client.create_contact(
                name=contact["name"],
                urns=contact["urns"],
                fields=fields_to_migrate,
                groups=groups)
        except:
            new_contacts = dest_client.get_contacts(urn=contact["urns"]).all()
            if to == IO_SITE and new_contacts:  #Then could exist but without variables
                new_contact = new_contacts[0]
                dest_client.update_contact(
                    new_contact,
                    name=contact["name"],
                    urns=contact["urns"],
                    fields=fields_to_migrate,
                    groups=groups)
            if new_contacts:
                new_contact = new_contacts[0]
            else:
                new_contact = ""
        ### If we migrate then the campaigns must be updated
        old_groups = [
            g["name"] for g in contact["groups"]
            if g["name"][-2:] != group_sufix
        ]
        origin_client.update_contact(contacts[0], groups=old_groups)
        if flow and new_contact:
            dest_client.create_flow_start(
                flow=flow,
                contacts=[new_contact.uuid],
            )


def create_thread(tel, flow=None, to=None):
    thread = Thread(target=migrate_contact, args=(tel, flow, to))
    thread.start()
    return


def migrate_fb_task(phone_contact, uuid):
    fb_contact = mx_client.get_contacts(uuid=uuid).all()
    if phone_contact and fb_contact:
        contact = phone_contact[0].serialize()
        fields_to_migrate = {}
        for var in VARIABLES_MX:
            if var in contact["fields"] and contact["fields"][var]:
                fields_to_migrate[var] = contact["fields"][var]
        #Add to tw variables
        groups = []
        for g in contact["groups"]:
            if g["name"][-2:] == "ow":  #Add to two way
                ow_name = g["name"][:-2]
                ow_name += "tw"
                groups += [ow_name]
                groups += [g["name"]]
            else:
                groups += [g["name"]]
        mx_client.update_contact(
            fb_contact[0],
            fields=fields_to_migrate,
            groups=[g["name"] for g in contact["groups"]])


def create_thread_fb(phone_contact, uuid):
    thread = Thread(target=migrate_fb_task, args=(phone_contact, uuid))
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
        flow = request.args.get('flow') if request.args.get('flow') else None
        to = request.args.get('to') if request.args.get('to') else None
        create_thread(tel, flow, to)
        return jsonify({"ok": "ok"})


@app.route("/birth", methods=["GET"])
def change_group_birth():
    phone_contact = request.args.get('tel')
    payload = {
        "backend": "Telcel",
        "sender": phone_contact,
        "ts": "1",
        "message": TRIGGER_DATOS_CHANGE_BIRTH,
        "id": "758af0a175f8a86"
    }
    r = requests.get(RP_URL, params = payload)
    if r.ok:
        return json.dumps({"request":"done"})
    json.dumps({ "error": "error" }), 400


@app.route("/migrate_fb", methods=['GET', 'POST'])
def migrate_fb_contact():
    """
    Create an empty contact on io and add to unconfirmed group
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        uuid = request.args.get('uuid')
        try:
            phone_contact = mx_client.get_contacts(urn=['tel:+52' + tel]).all()
            if phone_contact:
                create_thread_fb(phone_contact, uuid)
                return jsonify({"Migrado": "Si"}), 201
        except:
            pass
        return jsonify({"Migrado": "No"}), 404


@app.route("/create_empty", methods=['GET', 'POST'])
def create_empty_contact():
    """
    Create an empty contact on io and add to unconfirmed group
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        try:
            io_client.create_contact(
                urns=["tel:+52" + tel],
                groups=["cc9543a2-33ca-43cd-a3b7-4839b694605a"])
            return jsonify({"creado": "Si"}), 201
        except:
            pass
        return jsonify({"creado": "No"}), 404


@app.route("/search_contact", methods=['GET'])
def search_contact():
    """
    List or create notes.
    """
    if request.method == 'GET':
        tel = request.args.get('tel')
        contact = io_client.get_contacts(urn=['tel:+52' + tel]).all()
        if contact:
            return jsonify({"existe": "Si"}), 201
        return jsonify({"existe": "No"}), 404


@app.route("/start_flow", methods=['GET'])
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
            return jsonify({}), 404
        contact = client.get_contacts(urn=['tel:+52' + tel]).all()
        if contact:
            client.create_flow_start(
                flow=flow,
                contacts=[contact[0].uuid],
            )
            return jsonify({"Inicio_flow": "Si"}), 201
        return jsonify({"Inicio_flow": "No"}), 404


@app.route("/cancel", methods=['GET'])
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
            return jsonify({}), 404
        contact = client.get_contacts(urn=['tel:+52' + tel]).all()
        if contact:
            client.update_contact(contact=contact, groups=[group])
            return jsonify({}), 201
        return jsonify({}), 404


if __name__ == "__main__":
    #Cambiar ip a 0.0.0.0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(
        debug=True, host="0.0.0.0", port=int(os.getenv('WEBHOOK_PORT', 5000)))
