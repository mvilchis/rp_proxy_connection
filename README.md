# Webhook
## Connection between rapidpro.datos.gob.mx and app.rapidpro.io
Use TOKEN_MX and TOKEN_IO as environment variables.


The webhook expose three directions:
* **__/__**: Create contact on datos.mx. Parameters:
   * _tel_ : Uuid of contact on io
   * _flow_ : Optional parameter, only if must to run a flow
   * _to_ : site to migrate contact (io,datos)
   > /?tel=@contact.tel&to=datos

* _**/search_contact**_ : Search contact on io. Parameters:
  * _tel_ :cellnumber of contact on io
  > /search_contact?tel=@contac.tel

* _**/cancel**_ : Remove contact from all groups and add it to _AltoPd_. Parameters:
  * _tel_ :cellnumber of contact
  * _to_: site to remove from group (datos,io)
  > /cancel?tel=@contac.tel&to=io

* _**/create_empty**_: Create new contact without variables and add it to _Unconfirmed_ group. Parameters:
  * _tel_ :cellnumber of contact
  > /create_empty?tel=@contact.tel

* _**/start_flow**_: Search a contact and begin a flow. Parameters:
  * _tel_ :cellnumber of contact
  * _to_: site to start flow  (datos,io)
  * _flow_ : Flow to run
  > /start_flow?tel=@contact.tel&to=datos&flow=flow_id

* _**/migrate_fb**_: Search a contact with phone number to migrate on fb contact. Parameters:
    * _tel_ :cellnumber of contact
    * _uuid_: contact uuid
    > /migrate_fb?tel=@contact.tel&uuid=@contact.uuid
