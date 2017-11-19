from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

import json
import operator
from operator import itemgetter

app = Flask(__name__)
"""
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'kindred'
"""
app.config['MYSQL_HOST'] = 'us-cdbr-iron-east-05.cleardb.net'
app.config['MYSQL_DB'] = 'heroku_1d4c5e991701de4'
app.config['MYSQL_USER'] = 'b44770823be61d'
app.config['MYSQL_PASSWORD'] = '576610ef'

mysql = MySQL(app)

@app.route("/")
def hello():
    return "Hello World!"


# get all devices assignmed to a given student
# TODO: error handling of any kind
# TODO: what if two students have the same name?
# TODO: delete device

@app.route("/devices/<student_name>")
def getDevicesByStudent(student_name):

    # is this limited by student?
    print(student_name)
    devices = getDevicesByStudent(student_name, 20)

    # set up response data
    response = []
   
    for device in devices:    

        data = {}
        data["device_uuid"] = device[2]
        data["device_msg"] = device[3]
        data["device_label"] = device[4]
        data["device_icon"] = device[5]
        response.append(data) 

    return jsonify(response)

@app.route("/devices")
def getDevices():

    # is this limited by student?
    student_name = request.args.get('student_name')
    limit = request.args.get('limit')

    # limit default is 5
    if(limit is None):
        limit = 5
    
    # get all student devices
    if(student_name is not None):
        devices = getDevicesByStudent(student_name, limit)
    else:    
        devices = getAllDevices(limit)
    

    # set up response data
    response = {}
   
    # TODO: this should be real data 
    requestInfo = {}
    requestInfo["status"] = "200 OK";
    requestInfo["request type"] = "GET"
    
    response["request info"] = requestInfo;
    
    deviceInfo = []
    for device in devices:    

        data = {}
        data["device_uuid"] = device[2]
        data["device_msg"] = device[3]
        data["device_label"] = device[4]
        data["device_icon"] = device[5]
        data["student_name"] = device[0]
        deviceInfo.append(data) 

    response["device info"] = deviceInfo;

    return jsonify(response)

@app.route("/studentList")
def getStudentList():

    students = getStudentListData()

    # set up response data
    response = []
   
    student_info = []
    for student in students:
        data = {}
        data["student_name"] = student[0].capitalize()
        data["device_count"] = student[1]
        response.append(data)    

    # sort alphabetically
    sorted_response = sorted(response, key=itemgetter('student_name'))

    return jsonify(sorted_response)


@app.route("/device", methods=["POST"])
def addDevice():

    # student name
    data = json.loads(request.data)
    student_name = data["student_name"]
    device_uuid = data["device_uuid"]
    device_label = data["device_label"]
    device_msg = data["device_msg"]
    device_icon = data["device_icon"]

    # create student if new
    student = getStudent(student_name) 
    print(student)
    if student is None:
        addStudent(student_name);
        student = getStudent(student_name) 
        print(student)
    student_id = student[0]
    print(student_id);

    # create/reassign device
    device = getDeviceByUUID(device_uuid);
    if(not device):
        addDevice(student_id, device_uuid, device_label, device_msg, device_icon);
    else:
        updateDevice(device[0], student_id, device_label, device_msg, device_icon);
    
    response = {}
    
    requestInfo = {}
    requestInfo["status"] = "200 OK";
    requestInfo["request type"] = "GET"
    
    response["request info"] = requestInfo;
    
    return jsonify(response)

@app.route("/device/<device_uuid>", methods=["DELETE"])
def deleteDevice(device_uuid):

    deleteDeviceByUUID(device_uuid)

    response = {}
    
    requestInfo = {}
    requestInfo["status"] = "200 OK";
    requestInfo["request type"] = "DELETE"
    
    response["request info"] = requestInfo;
    
    return jsonify(response)

@app.route("/student/<student_name>", methods=["DELETE"])
def deleteStudent(student_name):

    # delete student devices
    deleteAllStudentDevices(student_name)

    # delete student
    deleteStudentByName(student_name)

    response = {}
    
    requestInfo = {}
    requestInfo["status"] = "200 OK";
    requestInfo["request type"] = "DELETE"
    
    response["request info"] = requestInfo;
    
    return jsonify(response)

def getStudent(student_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students WHERE student_name = '%s'" % student_name)
    return cur.fetchone()

def getStudentListData():
    cur = mysql.connection.cursor()
    sql_statement = "select students.student_name, COUNT(devices.id) AS NumberOfDevices from devices, students where students.id = devices.student_id group by students.id"
    cur.execute(sql_statement)
    return cur.fetchall()

def getAllDevices(limit):
    cur = mysql.connection.cursor()
    sql_statement = "select students.student_name, devices.* from devices, students where students.id = devices.student_id limit %s" % (limit);
    cur.execute(sql_statement)
    return cur.fetchall()

def getDevicesByStudent(student_name, limit):
    cur = mysql.connection.cursor()
    sql_statement = "select devices.* from devices, students where students.student_name = '%s' and students.id = devices.student_id limit %s" % (student_name, limit);
    cur.execute(sql_statement)
    return cur.fetchall()

def getDeviceByUUID(device_uuid):
    cur = mysql.connection.cursor()
    sql_statement = "select id from devices where device_uuid = '%s'" % (device_uuid);
    cur.execute(sql_statement)
    return cur.fetchone()
   

def addStudent(student_name):
    conn = mysql.connection
    cur = conn.cursor()
    sql_statement = "INSERT INTO students (student_name) VALUES ('%s')" % student_name.capitalize();
    cur.execute(sql_statement)
    conn.commit()

def addDevice(student_id, device_uuid, device_label, device_msg, device_icon):
    conn = mysql.connection
    cur = conn.cursor()
    sql_statement = "insert into devices (student_id, device_uuid, device_label, device_message, device_icon) values (%s, '%s', '%s', '%s', '%s')" % (student_id, device_uuid, device_label, device_msg, device_icon);
    print(sql_statement);
    cur.execute(sql_statement); 
    conn.commit()

def updateDevice(device_uuid, student_id, device_label, device_msg, device_icon):
    conn = mysql.connection
    cur = conn.cursor()
    sql_statement = "UPDATE devices SET student_id=%s, device_label='%s', device_message='%s', device_icon='%s' where id=%s"  % (student_id, device_label, device_msg, device_icon, device_uuid);
    print(sql_statement);
    cur.execute(sql_statement); 
    conn.commit()
   
def deleteDeviceByUUID(device_uuid):
    conn = mysql.connection
    cur = conn.cursor()
    sql_statement = "delete from devices where device_uuid = '%s'" % device_uuid;
    cur.execute(sql_statement); 
    conn.commit()

def deleteStudentByName(student_name):
    conn = mysql.connection
    cur = conn.cursor()
    sql_statement = "delete from students where student_name = '%s'" % student_name.capitalize();
    cur.execute(sql_statement); 
    conn.commit()

def deleteAllStudentDevices(student_name):
    conn = mysql.connection
    cur = conn.cursor()
    sql_statement = "DELETE devices FROM devices INNER JOIN students ON students.id = devices.student_id WHERE students.student_name = '%s'" % student_name.capitalize()
    cur.execute(sql_statement); 
    conn.commit()

if __name__ == "__main__":
    app.run(host='0.0.0.0')
