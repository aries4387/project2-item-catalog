# Project 2. Item Catalog - Udacity
### Creating the web application for Baby products
_______________________


## SETUP:

Installed Vagrant and VirtualBox
Clone the fullstack-nanodegree-vm
Launch the Vagrant VM : run vagrant up
vagrant ssh
write the FLASK application into /vagrant/catalog dir

## Create and populatre database:

run Database_Setup.py to create the database
run populate_db to populate the tables

run : python /vagrant/catalog/project2-item-catalog.py

### visit http:localhost:5000 to test application

Using OAuth 2.0 to Access Google APIs.
You can login using your google account.

## Authorization
Download the client_secrets.json from console.developers.google.com and put it into catalog folder
Project2-item-catalog.py -  add CLIENT_ID and CLIENT_SECRET at lines 32 and 33

## Features

If user is not logged in he can view all the categories and items for that categoty
If User is logged in he can add, edit or can delete the items for the category