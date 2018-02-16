import os


################## Sites constants #######################
DATOS_SITE="datos"
IO_SITE="io"

ONE_WAY="ow"
TWO_WAY="tw"

TRIGGER_DATOS_CHANGE_BIRTH="changebirth"

################## Rapidpro constants ####################
TOKEN_IO=os.getenv('TOKEN_IO', "")
TOKEN_MX=os.getenv('TOKEN_MX', "")
RP_URL = os.getenv('RP_URL',"")

################## Once time variables ###################
# Cliente io
io_client = TembaClient('rapidpro.io',TOKEN_IO)
#Cliente gob.mx
mx_client = TembaClient('rapidpro.datos.gob.mx', TOKEN_MX)

VARIABLES_MX = [f.key for f in mx_client.get_fields().all()]
VARIABLES_IO = [f.key for f in io_client.get_fields().all()]
VALID_GROUPS_MX= [group.name for group in mx_client.get_groups().all()]
VALID_GROUPS_IO= [group.name for group in io_client.get_groups().all()]
