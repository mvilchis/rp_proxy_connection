# Webhook
## Connection between rapidpro.datos.gob.mx and app.rapidpro.io 
Use TOKEN_MX and TOKEN_IO as environment variables. 


The webhook expose three directions:
* **__/__**: Create contact on datos.mx. Parameters _uuid_ and _flow_ 
* _**/search_contact**_ : Search contact on io. Parameters _tel_ (cellnumber of contact on io)
* _**/cancel**_ : Remove contact from all groups and add it to _AltoPd_. PArameters _tel_ (cellnumber of contact), _to_ (site to remove from group)
