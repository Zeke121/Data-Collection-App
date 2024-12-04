from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Client, Contact, ClientContact
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('view_clients_paginated', page=1))

@app.route('/clients/page/<int:page>')
def view_clients_paginated(page=1):
    per_page = 10
    pagination = Client.query.order_by(Client.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('clients.html', clients=pagination.items, pagination=pagination)

@app.route('/clients/new', methods=['GET', 'POST'])
def create_client():
    if request.method == 'POST':
        name = request.form['name']
        code = generate_client_code(name)
        new_client = Client(name=name, code=code)
        db.session.add(new_client)
        db.session.commit()
        flash('Client created successfully!')
        return redirect(url_for('view_clients_paginated', page=1))
    return render_template('client_form.html', editing=False)

@app.route('/clients/edit/<int:id>', methods=['GET', 'POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        client.name = request.form['name']
        db.session.commit()
        flash('Client updated successfully!')
        return redirect(url_for('view_clients_paginated', page=1))
    return render_template('client_form.html', client=client, editing=True)

@app.route('/clients/delete/<int:id>', methods=['POST'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!')
    return redirect(url_for('view_clients_paginated', page=1))

@app.route('/contacts/new', methods=['GET', 'POST'])
def create_contact():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        if Contact.query.filter_by(email=email).first():
            flash('Email already exists!')
            return redirect(url_for('create_contact'))
        new_contact = Contact(name=name, surname=surname, email=email)
        db.session.add(new_contact)
        db.session.commit()
        flash('Contact created successfully!')
        return redirect(url_for('view_contacts_paginated', page=1))
    return render_template('contact_form.html', editing=False)

@app.route('/contacts/edit/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    contact = Contact.query.get_or_404(id)
    if request.method == 'POST':
        contact.name = request.form['name']
        contact.surname = request.form['surname']
        contact.email = request.form['email']
        db.session.commit()
        flash('Contact updated successfully!')
        return redirect(url_for('view_contacts_paginated', page=1))
    return render_template('contact_form.html', contact=contact, editing=True)

@app.route('/contacts/delete/<int:id>', methods=['POST'])
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!')
    return redirect(url_for('view_contacts_paginated', page=1))

@app.route('/contacts/page/<int:page>')
def view_contacts_paginated(page=1):
    per_page = 10
    pagination = Contact.query.order_by(Contact.surname.asc(), Contact.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('contacts.html', contacts=pagination.items, pagination=pagination)

@app.route('/clients/link/<int:client_id>', methods=['POST'])
def link_contact(client_id):
    contact_id = request.form['contact_id']
    link = ClientContact(client_id=client_id, contact_id=contact_id)
    db.session.add(link)
    db.session.commit()
    flash('Contact linked successfully!')
    return redirect(url_for('view_clients_paginated', page=1))

@app.route('/clients/unlink/<int:link_id>', methods=['POST'])
def unlink_contact(link_id):
    link = ClientContact.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash('Contact unlinked successfully!')
    return redirect(url_for('view_clients_paginated', page=1))

def generate_client_code(name):
    prefix = ''.join(filter(str.isalpha, name.upper()))[:3].ljust(3, 'A')
    existing_codes = [c.code for c in Client.query.filter(Client.code.like(f"{prefix}%")).all()]
    num = max([int(code[3:]) for code in existing_codes] or [0]) + 1
    return f"{prefix}{str(num).zfill(3)}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
