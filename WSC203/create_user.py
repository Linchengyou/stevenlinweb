from app import db, models

u = models.User(username='')
u.set_password('')
db.session.add(u)
db.session.commit()
