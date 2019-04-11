from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields


class File(MongoModel):
    input = fields.CharField(primary_key=True, required=True)
    output = fields.CharField(required=True)
    source = fields.CharField(required=True)

    # meta = fields.EmbeddedDocumentField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'app'
