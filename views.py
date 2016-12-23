# -*- coding: utf-8 -*-
import json
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.http import HttpResponse
from .utils import CsvIo
import pandas as pd
import os
import numpy as np

csv.register_dialect('csv', delimiter='|')

def get_from_csv():
	path = '/csv_source/'
	mgt = 'gt_network_prefix_map.csv'
	mccmnc ='mcc_mnc_map.csv'
	file_mgt = os.path.join(path, mgt)
	file_mccmnc = os.path.join(path, mccmnc)
	encod = 'utf8'

	#Read MGT
	dtypes = {'gt': 'str', 'mcc': 'str','mnc': 'str', 'name': 'str'}
	df_gt = pd.read_csv(file_mgt,header=None,  names=['gt','mcc','mnc','name'], sep='|',dtype=dtypes, encoding = encod)
	#set Index
	#df_gt = df_gt['mnc'].fillna('')
	#remove white space
	df_gt.loc[df_gt['mnc'] == '' , ['mnc']] = ' '
	#df_gt = df_gt['mnc'].fillna(' ')
	df_gt['mccmnc'] = df_gt['mcc'] + df_gt['mnc']
	df_gt = df_gt.set_index(['mccmnc'], append=False)

	#Read mccmnc
	dtypes = {'mcc': 'str', 'mnc': 'str', 'country': 'str', 'name': 'str'}
	df_mnc = pd.read_csv(file_mccmnc,header=None, names=['mcc','mnc','country','name'], sep='|', dtype=dtypes, encoding = encod)
	#remove white space
	df_mnc.loc[df_mnc['mnc'] == '' , ['mnc']] = ' '
	#df_mnc = df_mnc['mnc'].fillna(' ')


	#set Index
	df_mnc['mccmnc'] = df_mnc['mcc'] + df_mnc['mnc']
	df_mnc = df_mnc.set_index(['mccmnc'], append=False)

	#df_gt.join(df_mnc,how='left')
	df_web = df_mnc.join(df_gt,how='outer',lsuffix='_l', rsuffix='_r')
	#slice so we get data for json for jquery table
	df_web = df_web[["mcc_l","mnc_l","country","name_l","gt"]]
	df_web =df_web.reset_index()
	#df_web.reset_index(level=0, inplace=True)
	df_web = df_web.rename(columns={'mcc_l': 'mcc', 'mnc_l': 'mnc', 'name_l': 'operator', 'gt': 'number'})
	df_web['mnc'] = df_web['mnc'].fillna('')
	df_web['mcc'] = df_web['mcc'].fillna('')
	df_web['country'] = df_web['country'].fillna('')
	df_web['operator'] = df_web['operator'].fillna('')
	return df_web
	
	
def save_to_csv(df):
	path = './csv_source/'
	mgt = 'gt_network_prefix_map.csv'
	mccmnc ='mcc_mnc_map.csv'
	file_mgt = os.path.join(path, mgt)
	file_mccmnc = os.path.join(path, mccmnc)
	encod = 'utf8'
	print "save"
	#df['mnc'] = df['mnc'].fillna('')
	df['mcc'] = df['mcc'].fillna('')
	df['country'] = df['country'].fillna('')
	df['operator'] = df['operator'].fillna('')
	df.dropna()	#get unique mcc mnc and remove empty number rows
	print df
	#df['mccmnc'] = df['mcc'] + df['mnc']
	mcc_mnc_from_web = df.drop_duplicates(['mccmnc'])
	print mcc_mnc_from_web
	mcc_mnc_from_web.to_csv(file_mccmnc, sep='|', encoding='utf-8', header=False, index= False, columns=["mcc","mnc","country","operator"])
	#remove rows with empty number
	df.dropna(subset=['number'], inplace=True)
	print df
	df.to_csv(file_mgt, sep='|', encoding='utf-8', header=False, index= False, columns=["number","mcc","mnc","operator"])

	
	


class JsonTableView(LoginRequiredMixin, generic.ListView):

    def get(self, request):
	
	df = get_from_csv()
	# create json for jquery table....
	to_web = df.to_json(path_or_buf = None, orient = 'records',force_ascii = True, double_precision= False)
        return HttpResponse(to_web, content_type="application/json")


class IndexView(LoginRequiredMixin, generic.TemplateView):
    login_url = 'login'
    redirect_field_name = 'redirect_to'
    template_name = 'csv_table/index.html'


class AddFormView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if len(request.POST["mcc"]) != 0 and len(request.POST['mnc']) != 0:
            class HelperClass:
                pass
			#get data frame
            df  = get_from_csv()
            #Only need to 0 pad mnc
            request_dict = dict(request.POST)
            request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
            if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
                request_dict["mnc"] = "0"+request_dict["mnc"]                
    			
    		#Add operator mcc + mnc from web form.
            web_mnc = request_dict["mnc"]
            web_mcc = request_dict["mcc"]
            web_mccmnc = request_dict["mcc"] + request_dict["mnc"]
            	
            #and optional parameters
            web_number = request_dict["number"]
            web_country = request_dict["country"]
            web_operator = request_dict["operator"]
         
            if df[(df['mcc']+df['mnc'] == web_mccmnc) & (df['number'] == web_number)].shape[0] > 0 :
            	return HttpResponse("Row allready added for this MCC, MNC and MGT use edit to change ")
            else:
            	#rockenroll lets add row.
            	df_add = pd.DataFrame ({'mcc': [web_mcc],
                         				'mnc': [web_mnc],
                         				'operator': [web_operator],
                         				'country': [web_country],
                         				'number': [web_number]
                         				})
                df = pd.concat([df_add,df])
                #names are global so update all rows:
                #update country changes all
                df.loc[df['mcc'] == web_mcc, 'country'] = web_country
                #update operator names
                df.loc[df['mccmnc'] == web_mccmnc, 'name'] = web_operator
                save_to_csv(df)

        return HttpResponse("Data was successfully added ")
       


class EditFormView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
		#get data frame
		df  = get_from_csv()
		# only need to 0 pad mnc
		request_dict = dict(request.POST)
		request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
		if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
			request_dict["mnc"] = "0"+request_dict["mnc"]                
		if request_dict["mnc"] == '':
			request_dict["mnc"] = ' '             	
		#Add operator mcc + mnc from web form.
		web_mnc = request_dict["mnc"]
		web_mcc = request_dict["mcc"]
		web_mccmnc = request_dict["mcc"] + request_dict["mnc"]
			
		#and optional parameters
		web_number = request_dict["number"]
		web_country = request_dict["country"]
		web_operator = request_dict["operator"]
		web_old_number = request_dict["which_number"]
	 
		print df

		#Did the number allready exist for a operator?
		if df[(df['mcc']+ df['mnc'] == web_mccmnc) & (df['number'] == web_number)].shape[0] > 0 :
			#update only country and names
			df.loc[df['mcc'] == web_mcc, 'country'] = web_country
			df.loc[df['mccmnc'] == web_mccmnc, 'operator'] = web_operator
			print "TIEM TO SAVE"
			print df
			save_to_csv(df)
			return HttpResponse("Record is successfully edited. Updated only names!")
		else:
			print web_operator
			print web_mccmnc
			print web_old_number

			#update old row with new number from web form
			df.loc[(df['mccmnc'] == web_mccmnc) & (df['number'] == web_old_number), 'number'] = web_number
			#update countries and operator names
			df.loc[df['mcc'] == web_mcc, 'country'] = web_country
			df.loc[df['mccmnc'] == web_mccmnc, 'operator'] = web_operator
			print df
			save_to_csv(df)
			return HttpResponse("Record is successfully edited")



class DeleteFormView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):
		#get data frame
		df  = get_from_csv()
		# only need to 0 pad mnc
		request_dict = dict(request.POST)
		request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
		if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
			request_dict["mnc"] = "0"+request_dict["mnc"]                
			
		#Add operator mcc + mnc from web form.
		web_mnc = request_dict["mnc"]
		web_mcc = request_dict["mcc"]
		web_mccmnc = request_dict["mcc"] + request_dict["mnc"]
			
		#and optional parameters
		web_number = request_dict["number"]
		web_country = request_dict["country"]
		web_operator = request_dict["operator"]
		web_old_number = request_dict["which_number"]
		
		#find the row and delete 
		row = df[(df['number'] == web_old_number) & (df['mccmnc'] == web_mccmnc)].index
		del_row = df.index.isin(row)
		df = df[~del_row]
		print df
		save_to_csv(df)
		return HttpResponse("Record was successfully deleted")

# -*- coding: utf-8 -*-
import json
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.http import HttpResponse
from .utils import CsvIo
import pandas as pd
import os
import numpy as np

csv.register_dialect('csv', delimiter='|')

def get_from_csv():
	path = './csv_source/'
	mgt = 'gt_network_prefix_map.csv'
	mccmnc ='mcc_mnc_map.csv'
	file_mgt = os.path.join(path, mgt)
	file_mccmnc = os.path.join(path, mccmnc)
	encod = 'utf8'

	#Read MGT
	dtypes = {'gt': 'str', 'mcc': 'str','mnc': 'str', 'name': 'str'}
	df_gt = pd.read_csv(file_mgt,header=None,  names=['gt','mcc','mnc','name'], sep='|',dtype=dtypes, encoding = encod)
	#set Index
	#df_gt = df_gt['mnc'].fillna('')

	df_gt['mccmnc'] = df_gt['mcc'] + df_gt['mnc']
	df_gt = df_gt.set_index(['mccmnc'], append=False)


	#Read mccmnc
	dtypes = {'mcc': 'str', 'mnc': 'str', 'country': 'str', 'name': 'str'}
	df_mnc = pd.read_csv(file_mccmnc,header=None, names=['mcc','mnc','country','name'], sep='|', dtype=dtypes, encoding = encod)

	#set Index
	df_mnc['mccmnc'] = df_mnc['mcc'] + df_mnc['mnc']
	df_mnc = df_mnc.set_index(['mccmnc'], append=False)


	#df_gt.join(df_mnc,how='left')
	df_web = df_mnc.join(df_gt,how='outer',lsuffix='_l', rsuffix='_r')

	#slice so we get data for json for jquery table
	df_web = df_web[["mcc_l","mnc_l","country","name_l","gt"]]
	df_web =df_web.reset_index()
	#df_web.reset_index(level=0, inplace=True)
	df_web = df_web.rename(columns={'mcc_l': 'mcc', 'mnc_l': 'mnc', 'name_l': 'operator', 'gt': 'number'})
	df_web = df_web.fillna('')
	return df_web
	
	
def save_to_csv(df):
	path = './csv_source/'
	mgt = 'gt_network_prefix_map.csv'
	mccmnc ='mcc_mnc_map.csv'
	file_mgt = os.path.join(path, mgt)
	file_mccmnc = os.path.join(path, mccmnc)
	encod = 'utf8'
	df = df.fillna('')
	#get unique mcc mnc
	df['mccmnc'] = df['mcc'] + df['mnc']
	mcc_mnc_from_web = df.drop_duplicates(['mccmnc'])
	mcc_mnc_from_web.to_csv(file_mccmnc, sep='|', encoding='utf-8', header=False, index= False, columns=["mcc","mnc","country","operator"])
	df.to_csv(file_mgt, sep='|', encoding='utf-8', header=False, index= False, columns=["number","mcc","mnc","operator"])

	
	


class JsonTableView(LoginRequiredMixin, generic.ListView):

    def get(self, request):
	
	df = get_from_csv()
	# create json for jquery table....
	to_web = df.to_json(path_or_buf = None, orient = 'records',force_ascii = True, double_precision= False)
        return HttpResponse(to_web, content_type="application/json")


class IndexView(LoginRequiredMixin, generic.TemplateView):
    login_url = 'login'
    redirect_field_name = 'redirect_to'
    template_name = 'csv_table/index.html'


class AddFormView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if len(request.POST["mcc"]) != 0 and len(request.POST['mnc']) != 0:
            class HelperClass:
                pass
			#get data frame
            df  = get_from_csv()
            #Only need to 0 pad mnc
            request_dict = dict(request.POST)
            request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
            if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
                request_dict["mnc"] = "0"+request_dict["mnc"]                
    			
    		#Add operator mcc + mnc from web form.
            web_mnc = request_dict["mnc"]
            web_mcc = request_dict["mcc"]
            web_mccmnc = request_dict["mcc"] + request_dict["mnc"]
            	
            #and optional parameters
            web_number = request_dict["number"]
            web_country = request_dict["country"]
            web_operator = request_dict["operator"]
         
            if df[(df['mcc']+df['mnc'] == web_mccmnc) & (df['number'] == web_number)].shape[0] > 0 :
            	return HttpResponse("Row allready added for this MCC, MNC and MGT use edit to change ")
            else:
            	#rockenroll lets add row.
            	df_add = pd.DataFrame ({'mcc': [web_mcc],
                         				'mnc': [web_mnc],
                         				'operator': [web_operator],
                         				'country': [web_country],
                         				'number': [web_number]
                         				})
                df = pd.concat([df_add,df])
                #names are global so update all rows:
                #update country changes all
                df.loc[df['mcc'] == web_mcc, 'country'] = web_country
                #update operator names
                df.loc[df['mccmnc'] == web_mccmnc, 'name'] = web_operator
                save_to_csv(df)

        return HttpResponse("Data was successfully added ")
       


class EditFormView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if len(request.POST["mcc"]) != 0 and len(request.POST['mnc']) != 0:
			#get data frame
            df  = get_from_csv()
            # only need to 0 pad mnc
            request_dict = dict(request.POST)
            request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
            if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
                request_dict["mnc"] = "0"+request_dict["mnc"]                
    			
    		#Add operator mcc + mnc from web form.
            web_mnc = request_dict["mnc"]
            web_mcc = request_dict["mcc"]
            web_mccmnc = request_dict["mcc"] + request_dict["mnc"]
            	
            #and optional parameters
            web_number = request_dict["number"]
            web_country = request_dict["country"]
            web_operator = request_dict["operator"]
            web_old_number = request_dict["which_number"]
         
            
            #Did the number allready exist for a operator?
            if df[(df['mcc']+df['mnc'] == web_mccmnc) & (df['number'] == web_number)].shape[0] > 0 :
            	#update only country and names
            	df.loc[df['mcc'] == web_mcc, 'country'] = web_country
            	df.loc[df['mccmnc'] == web_mccmnc, 'operator'] = web_operator
            	print df
            	save_to_csv(df)
            	return HttpResponse("Record is successfully edited. Updated only names!")
            else:
            	#update old row with new number from web form
            	df.loc[(df['mccmnc'] == web_mccmnc) & (df['number'] == web_old_number), 'number'] = web_number
            	#update countries and operator names
            	df.loc[df['mcc'] == web_mcc, 'country'] = web_country
            	df.loc[df['mccmnc'] == web_mccmnc, 'operator'] = web_operator
            	print df
            	save_to_csv(df)
            	return HttpResponse("Record is successfully edited")


class DeleteFormView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):
		#get data frame
		df  = get_from_csv()
		# only need to 0 pad mnc
		request_dict = dict(request.POST)
		request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
		if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
			request_dict["mnc"] = "0"+request_dict["mnc"]                
			
		#Add operator mcc + mnc from web form.
		web_mnc = request_dict["mnc"]
		web_mcc = request_dict["mcc"]
		web_mccmnc = request_dict["mcc"] + request_dict["mnc"]
			
		#and optional parameters
		web_number = request_dict["number"]
		web_country = request_dict["country"]
		web_operator = request_dict["operator"]
		web_old_number = request_dict["which_number"]
		
		#find the row and delete 
		row = df[(df['number'] == web_old_number) & (df['mccmnc'] == web_mccmnc)].index
		del_row = df.index.isin(row)
		df = df[~del_row]
		print df
		save_to_csv(df)
		return HttpResponse("Record was successfully deleted")
