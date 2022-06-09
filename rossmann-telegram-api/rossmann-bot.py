import os
import pandas as pd
import json
import requests
from flask import Flask, request, Response

#constants
TOKEN = '5372561015:AAFPbfH4oWx5hu-mxqRxKSbtebblrKYB0H4'

#info about bot
#https://api.telegram.org/bot5372561015:AAFPbfH4oWx5hu-mxqRxKSbtebblrKYB0H4/getMe


def send_message( chat_id, text ):
	url = 'https://api.telegram.org/bot{}/'.format( TOKEN )
	url = url + 'sendMessage?chat_id={}'.format( chat_id )
	#text
	r = requests.post( url, json={'text':text} )
	print( 'Status Code {}'.format(r.status_code) )
	return None

#loading
def load_dataset( store_id):
	#loading datasets heroku
	df10 = pd.read_csv( 'test.csv' )
	df_store_raw = pd.read_csv( 'store.csv' )
	
	#loading datasets local
	#df10 = pd.read_csv( '/home/deivison/Documentos/projetos/dsrossmann/notebooks/data/test.csv' )
	#df_store_raw = pd.read_csv( '/home/deivison/Documentos/projetos/dsrossmann/notebooks/data/store.csv' )


	#merge test dataset + store 
	df_test = pd.merge( df10, df_store_raw, how = 'left', on = 'Store' )

	#choose store for prediction
	df_test = df_test[ df_test['Store'] == store_id  ]
	
	#testar se existe o id da loja no df_test
	if not df_test.empty:
		#limpeza lojas fechadas 
		df_test = df_test[ df_test['Open'] != 0 ]
		df_test = df_test[ ~df_test['Open'].isnull() ]
		df_test = df_test.drop( 'Id', axis = 1 )

		# convert Dataframe to json
		data = json.dumps( df_test.to_dict( orient = 'records') )
	
	else:
		data = 'error'
		
	return data

def predict( data ):
	#API call
	#url = 'http://0.0.0.0:5000/rossmann/predict'
	url = 'https://rossmann-model-2022.herokuapp.com/rossmann/predict'
	header ={'Content-type':'application/json'}
	data = data
	r = requests.post( url, data = data, headers = header )
	print('Status Code {}'.format( r.status_code ) )

	d1 = pd.DataFrame( r.json(), columns = r.json()[0].keys() )
	
	return d1
	
def parse_message( message ):
	chat_id = message['message']['chat']['id']
	store_id = message['message']['text']
	
	store_id = store_id.replace( '/','' )
	
	try:
		store_id = int( store_id) 

	except ValueError:
		store_id = 'error'
	
	return chat_id, store_id
	


#API initialize
app = Flask( __name__ )

#rota
@app.route( '/', methods=['GET','POST'] )

def index():
	if request.method == 'POST':
		message = request.get_json()
		
		chat_id, store_id = parse_message( message )
		
		if store_id != 'error':
			#loading data
			data = load_dataset( store_id )
			
			if data != 'error':
				
			
				#prediction
				d1 = predict( data )
				#calculation
				
				d2 = d1[['store','prediction']].groupby('store').sum().reset_index()

				#send message
				msg = 'Store Number {} vendera R${:,.2f} nas proximas 6 semanas'.format( 
					        d2['store'].values[0],
					        d2['prediction'].values[0] )
				
				send_message( chat_id, msg )
				
				return Response( 'ok', status = 200 )
				
				
			else:
				send_message( chat_id, 'Store not Available' )
				return Response( 'ok', status = 200 )
				
		else:
			send_message( chat_id, 'Store ID is Wrong')
			
			return Response( 'ok', status = 200 )
	else:
		return '<h1> Rossmann Telegram BOT </h1>'

if __name__ == '__main__':
	#host local
	#app.run( host= '0.0.0.0', port=5000 )
	
	#host heroku
	port = os.environ.get( 'PORT', 5000 )
	app.run( host= '0.0.0.0', port=port )
	

    
