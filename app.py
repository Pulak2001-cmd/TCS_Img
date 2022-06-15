import json
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flask_cors import CORS
import pyrebase, os
import urllib3

app = Flask(__name__)
cors = CORS(app, resources={r"/v1/api/*": {"origins": "*"}})
api = Api(app)
confirg = {
    "apiKey": "AIzaSyDhBvV540CfM6J7MhaeLK3ss6D57zwCc_o",
    "authDomain": "watermeasurement-8bdae.firebaseapp.com",
    "databaseURL": "https://watermeasurement-8bdae-default-rtdb.firebaseio.com",
    "projectId": "watermeasurement-8bdae",
    "storageBucket": "watermeasurement-8bdae.appspot.com",
    "messagingSenderId": "885543244986",
    "appId": "1:885543244986:web:2b224feca11d6f6cbf5e83",
    "measurementId": "G-QVXLF7N2DV"
}

firebase = pyrebase.initialize_app(confirg)
db = firebase.database()

def error(message):
    result = {
        "error": message,
        "status": False,
    }
    return jsonify(result)

def Activated_sludge(time, volume_of_reactor, recycle_ratio, area_of_clarifier, height_of_clarifier, bod_cod_ratio):
    total = volume_of_reactor + recycle_ratio + height_of_clarifier + area_of_clarifier 
    bod = total * (bod_cod_ratio + 1)
    cod = total - bod
    tss = total*time
    result = {
        'bod': bod*time,
        'cod': cod*time,
        'tss': tss,
        'total_caliform': total*time,
        'time': time
    }
    return result

def Hydrodynamic_cavitation(bod, cod, batch_volume, number_of_passes, time_cavitation, pH, pressure_cavitation):
    total = batch_volume + number_of_passes + pH + pressure_cavitation
    tss = total*time_cavitation
    total_caliform = total + pH*pressure_cavitation
    result = {
        'bod': total*time_cavitation + bod,
        'cod': total*time_cavitation + cod,
        'tss': tss,
        'total_caliform': total_caliform,
        'time': time_cavitation
    }
    return result

def Disinfection(bod, cod, time_disinfection, concentration_disinfection):
    result = {
        'bod': bod + time_disinfection*concentration_disinfection,
        'cod': cod + time_disinfection*concentration_disinfection,
        'tss': bod+cod,
        'total_caliform': (bod+cod)*time_disinfection,
        'time': time_disinfection
    }
    return result

class SignUp(Resource):
    def post(self):
        data = request.get_json()
        name = data["name"]
        password = data["password"]
        dict = db.child('users').get().val()
        json_string = json.dumps(dict)
        obj = json.loads(json_string)
        user_list = obj.values()
        for user in user_list:
            if user['name'] == name:
                return error('User already exists with this username')
        new_user = {
            "name": name,
            "password": password
        }
        db.child('users').push(new_user)
        result = {
            "error": "",
            "status": True,
            "name": name
        }
        return jsonify(result)

class Login(Resource):
    def post(self):
        data = request.get_json()
        name = data["name"]
        password = data["password"]
        dict = db.child('users').get().val()
        json_string = json.dumps(dict)
        obj = json.loads(json_string)
        user_list = obj.values()
        for user in user_list:
            if user['name'] == name and user['password'] == password:
                result = {
                    "error": "",
                    "status": True,
                    "name": name,
                }
                return jsonify(result)
        return error("Wrong username or password")

class Test(Resource):
    def get(self):
        result = {
            "message": "This is a test api",
        }
        return jsonify(result)

class OutputEstimations(Resource):
    def post(self):
        data = request.get_json()
        res_time_sludge = int(data["res_time_sludge"])
        volume_of_reactor = int(data["volume_of_reactor"])
        recycle_ratio = int(data["recycle_ratio"])
        area_of_clarifier = int(data["area_of_clarifier"])
        height_of_clarifier = int(data["height_of_clarifier"])
        bod_cod_ratio = int(data["bod_cod_ratio"])
        batch_volume = int(data["batch_volume"])
        number_of_passes = int(data["number_of_passes"])
        time_cavitation = int(data["time_cavitation"])
        pH = int(data["pH"])
        pressure_cavitation = int(data["pressure_cavitation"])
        time_disinfection = int(data["time_disinfection"])
        concentration_disinfection = int(data["concentration_disinfection"])
        result_activated_sludge = Activated_sludge(res_time_sludge, volume_of_reactor, recycle_ratio, area_of_clarifier, height_of_clarifier, bod_cod_ratio)
        result_hydrodynamic_cavitation = Hydrodynamic_cavitation(result_activated_sludge['bod'], result_activated_sludge['cod'], batch_volume, number_of_passes, time_cavitation, pH, pressure_cavitation)
        result_disinfection = Disinfection(result_hydrodynamic_cavitation['bod'], result_hydrodynamic_cavitation['cod'], time_disinfection, concentration_disinfection)
        list = {
            'result_activated_sludge': result_activated_sludge,
            'result_hydrodynamic_cavitation': result_hydrodynamic_cavitation,
            'result_disinfection': result_disinfection,
        }
        result = {
            "error": "",
            "status": True,
            "result": list,
            "total_time": res_time_sludge+time_cavitation+time_disinfection
        }
        return jsonify(result)


api.add_resource(SignUp, '/v1/api/signup')
api.add_resource(Login, '/v1/api/login')
api.add_resource(Test, '/v1/api/test')
api.add_resource(OutputEstimations, '/v1/api/outputEstimations')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port= port, host='0.0.0.0')