from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Contact, Client
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(os.path.dirname(__file__))}/app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('view_contacts_paginated', page=1))

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
    # Retrieve contacts not linked to this client
    available_contacts = Contact.query.filter(~Contact.clients.any(client_id=client.id)).all()
    return render_template('client_form.html', client=client, editing=True, available_contacts=available_contacts)



@app.route('/clients/delete/<int:id>', methods=['POST'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!')
    return redirect(url_for('view_clients_paginated', page=1))

# Route to create a new contact
@app.route('/contacts/new', methods=['GET', 'POST'])
def create_contact():
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')

        # Server-side validation
        if not name or not surname or not email:
            flash('All fields are required!', 'danger')
            return render_template('contact_form.html', editing=False)

        # Check for duplicate email
        if Contact.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return render_template('contact_form.html', editing=False)

        try:
            # Add new contact to the database
            new_contact = Contact(name=name, surname=surname, email=email)
            db.session.add(new_contact)
            db.session.commit()
            flash('Contact created successfully!', 'success')
            return redirect(url_for('view_contacts_paginated', page=1))
        except Exception as e:
            app.logger.error(f"Error creating contact: {e}")
            flash('An error occurred while creating the contact. Please try again.', 'danger')
            return render_template('contact_form.html', editing=False)

    return render_template('contact_form.html', editing=False)




# Route to edit an existing contact
@app.route('/contacts/edit/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    contact = Contact.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')

        # Server-side validation
        if not name or not surname or not email:
            flash('All fields are required!', 'danger')
            return render_template('contact_form.html', contact=contact, editing=True)

        # Check for duplicate email (if changed)
        if email != contact.email and Contact.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return render_template('contact_form.html', contact=contact, editing=True)

        try:
            # Update contact details
            contact.name = name
            contact.surname = surname
            contact.email = email
            db.session.commit()
            flash('Contact updated successfully!', 'success')
            return redirect(url_for('view_contacts_paginated', page=1))
        except Exception as e:
            app.logger.error(f"Error updating contact: {e}")
            flash('An error occurred while updating the contact. Please try again.', 'danger')
            return render_template('contact_form.html', contact=contact, editing=True)

    return render_template('contact_form.html', contact=contact, editing=True)


@app.route('/contacts/delete/<int:id>', methods=['POST'])
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!')
    return redirect(url_for('view_contacts_paginated', page=1))

# Paginated view of contacts
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
    return redirect(url_for('edit_client', id=client_id))


@app.route('/clients/unlink/<int:link_id>', methods=['POST'])
def unlink_contact(link_id):
    link = ClientContact.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash('Contact unlinked successfully!')
    return redirect(url_for('edit_client', id=link.client_id))

@app.route('/contacts/link/<int:contact_id>', methods=['POST'])
def link_client(contact_id):
    client_id = request.form['client_id']
    link = ClientContact(client_id=client_id, contact_id=contact_id)
    db.session.add(link)
    db.session.commit()
    flash('Client linked successfully!')
    return redirect(url_for('edit_contact', id=contact_id))


@app.route('/contacts/unlink/<int:link_id>', methods=['POST'])
def unlink_client(link_id):
    link = ClientContact.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash('Client unlinked successfully!')
    return redirect(url_for('edit_contact', id=link.contact_id))

def generate_client_code(name):
    prefix = ''.join(filter(str.isalpha, name.upper()))[:3].ljust(3, 'A')
    existing_codes = [c.code for c in Client.query.filter(Client.code.like(f"{prefix}%")).all()]
    num = max([int(code[3:]) for code in existing_codes] or [0]) + 1
    return f"{prefix}{str(num).zfill(3)}"

# Initialize the database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure database tables are created
    app.run(debug=True)
