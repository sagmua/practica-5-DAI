# -*- coding: utf-8 -*-

from flask import Flask, render_template, session, redirect, url_for, escape, request, g
from flask import jsonify
import shelve, queue

from bson.json_util  import dumps

import pymongo



app = Flask(__name__)


app.secret_key = 'any random string'

@app.before_first_request
def start():
	session['last_visited'] = []





@app.route('/',  methods  = ['GET', 'POST'])			# decorador, varia los parametros
def index():

	

	data_page = {
		'title' : 'pagina personal',
		'header_title': 'Soluciones Domótica',
		'header_subtitle' : 'Haciendo más facil la vida',
		'logo' : 'static/img/logo.png',
		'menu' : [
			('Home', '/'),
			('Contact', '/contact'),
			('About us', '/about'),

		],

		'last_visited' : session['last_visited'],
		'table_header' : ('Nombre', 'Tipo de restaurante', 'Calle')
	}

	



	

	#comprobamos si el usuario y la contraseña introducidas coinciden con algún usuario del sistema:
	if request.method == 'POST':

		select = request.form.get('criterio')
		
		if select != None:
			#obtenemos el criterio de búsqueda:
			criterio = select
			#buscamos en la base de datos en función de ese campo:
			termino = request.form.get('termino')
			resultado_busqueda = restaurants_search(criterio, termino)

			print(resultado_busqueda.count())
			data_page['restaurants'] = resultado_busqueda
			data_page['criterios'] = [criterio, termino]


		else:
		
			data_base = shelve.open("data_base.dat")
			user = data_base.get(request.form['username'], None)

			if user != None and user['password'] == request.form['password']:
				session['username'] = request.form['username']
				
				return redirect(url_for('index'))

	#Si esta logeado:
	if 'username' in session:
		username = session['username']
		return render_template('welcome.html', data_page=data_page,logged=True)

	#en caso de no estar registrado:
	else:
		return render_template('welcome.html',data_page=data_page, logged=False)




@app.route('/about')
def about():
	return render_template('about.html')

#ruta para registrarse en caso de no estarlo:
@app.route('/signup', methods= ['GET', 'POST'])
def signup():
	return render_template('signup.html')

@app.route('/register', methods= ['GET', 'POST'])
def register():
	if request.method == 'POST':
		#sacamos los datos del formulario:
		data_base = shelve.open('data_base.dat')
		user = request.form['username']
		password = request.form['password']

		#descripción inicial:
		descripcion = 'Esta es una descripción de mi usuario'
		#creamos una nueva instancia del user en la base de datos:
		data_base[user] = {'username': user, 'password': password, 'descripcion': descripcion}
		session['username'] = user

		#cerramos la base de datos:
		data_base.close()

	return redirect(url_for('index'))

@app.after_request
def store_visted_urls(response):
	if not request.url in session['last_visited']:
		if len(session['last_visited']) < 3 :
			session['last_visited'].append(request.url)
		else:
			session['last_visited'].pop(0)
			session['last_visited'].append(request.url)
	
	return response


	


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

	



@app.route('/logout')
def logout():
	# remove the username from the session if it is there
   session.pop('username', None)
   return redirect(url_for('index'))



#Permitimos al usuario visualizar los datos de su cuenta:
@app.route('/userInfo')
def user_info():
	#sacamos los datos del formulario:
	data_base = shelve.open('data_base.dat')
	user = data_base[session['username']]

	print(user['username'])

	data_page = {
			'user': user['username'],
			'descripcion' : user['descripcion']
	}

	return render_template('user_info.html', data_page=data_page)



#Función en la cuál permitiremos al usuario modificar los datos de su cuenta:
@app.route('/setting')
def setting():

	return render_template('settings.html')



#Función para actualizar los datos del usuario:
@app.route('/update', methods =['GET', 'POST'])
def update_info():

	if(request.method == 'POST'):
		if request.form['password'] != request.form['confirm_password']:
			return redirect(url_for('setting'))
		else:
			#sacamos los datos del formulario:
			data_base = shelve.open('data_base.dat')
			user = request.form['username']
			password = request.form['password']

			#descripción inicial:
			descripcion = request.form['descripcion']
			#creamos una nueva instancia del user en la base de datos:
			data_base[user] = {'username': user, 'password': password, 'descripcion': descripcion}
			session['username'] = user

			#cerramos la base de datos:
			data_base.close()
			return redirect(url_for('index'))
			



#Función para obtener los resultados de una búsqueda de restaurantes:
def restaurants_search(criterio = 'borough', termino = ''):
	#obtenemos la colección:
	
	try:
		con = pymongo.MongoClient()
		print ('Connected succesfully')
	except pymongo.errors.ConnectionFailure:
		print ('Error during connecting mongo database')

	
	db = con.test

	if criterio == 'zipcode':
		search = db.restaurants.find({ 'address.'+criterio : termino }).limit(10)
	else:
		search = db.restaurants.find({ criterio : termino }).limit(10)
	

	



	#buscamos los restaurantes con los criterios introducidos:
	return search


#Función para obtener la paginacion de los restaurantes:
@app.route('/find_ajax', methods=['GET'])
def find_ajax():
	try:
		con = pymongo.MongoClient()
		print ('Connected succesfully')
	except pymongo.errors.ConnectionFailure:
		print ('Error during connecting mongo database')

	db = con.test

	#obtenemos los parametros de busqueda anteriores:
	data_page = request.args.get('data_page', '')

	criterio=data_page['criterios'][0]
	termino=data_page['criterios'][1]

	#obtenemos el número de página:
	num_pagina = int(request.args.get('num_pagina',1))-1


	if criterio == 'zipcode':
		search = db.restaurants.find({ 'address.'+criterio : termino }).skip(num_pagina*10).limit(10)
	else:
		search = db.restaurants.find({ criterio : termino }).skip(num_pagina*10).limit(10)






	return dumps(search)


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)

