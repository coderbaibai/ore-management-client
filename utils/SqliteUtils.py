from pathlib import Path
from config.GConfig import gConfig
from peewee import SqliteDatabase, Model, IntegerField, TextField, AutoField,PrimaryKeyField
# 上传记录数据库
up_db = SqliteDatabase(Path.cwd()/gConfig['client']['upload-db-path'])

class UploaderItem(Model):
    id = TextField(primary_key=True)
    sign = TextField(null=True)
    count = IntegerField(null=True)
    local = TextField(null=True)
    bucket = TextField(null=True)
    cloud = TextField(null=True)
    eTag = TextField(null=True)

    class Meta:
        database = up_db
        table_name = 'tb_uploader'

up_db.connect()
up_db.create_tables([UploaderItem])

# 传输完成记录数据库

transport_db = SqliteDatabase(Path.cwd()/gConfig['client']['transport-db-path'])

class TransportRecord(Model):
    id = PrimaryKeyField()
    name = TextField(null=True)
    type = IntegerField(null=True)
    size = IntegerField(null=True)
    state = IntegerField(null=True)
    time = TextField(null=True)
    local = TextField(null=True)
    bucket = TextField(null=True)
    cloud = TextField(null=True)
    finish = IntegerField(null=True)
    market_id = IntegerField(null=True)

    class Meta:
        database = transport_db
        table_name = 'tb_transport'

transport_db.connect()
transport_db.create_tables([TransportRecord])