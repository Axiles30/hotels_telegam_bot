import peewee as pw

db = pw.SqliteDatabase('database/peewee/search_history.db')

class BaseModel(pw.Model):
    class Meta:
        database = db


class UserModel(BaseModel):
    user_name = pw.CharField()
    telegram_id = pw.IntegerField(unique=True)
    searching_date = pw.DateTimeField()


class City(BaseModel):
    city_id = pw.IntegerField(unique=True)
    name = pw.CharField()
    country = pw.CharField()


class Hotel(BaseModel):
    hotel_id = pw.IntegerField(unique=True)
    name = pw.CharField()
    image = pw.CharField()
    check_in_date = pw.CharField()
    check_out_date = pw.CharField()
    price_per_night = pw.FloatField()
    price_all = pw.FloatField()


class UserSearchHistory(BaseModel):
    telegram_id = pw.ForeignKeyField(UserModel, backref='search_history')
    city_id = pw.ForeignKeyField(City, backref='search_history')
    hotel_id = pw.ForeignKeyField(Hotel, backref='search_history')
    total_price = pw.FloatField()
    searching_date = pw.DateTimeField()


db.connect()
db.create_tables([UserModel, City, Hotel, UserSearchHistory])
db.close()
