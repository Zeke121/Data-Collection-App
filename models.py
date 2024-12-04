from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(6), unique=True, nullable=False)
    contacts = db.relationship('ClientContact', back_populates='client')

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    clients = db.relationship('ClientContact', back_populates='contact')

class ClientContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    client = db.relationship('Client', back_populates='contacts')
    contact = db.relationship('Contact', back_populates='clients')
