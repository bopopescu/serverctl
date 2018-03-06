#!/usr/bin/python3

import greenstalk
import msgpack
import signal
import time
import sys
import os
import shutil
from lxml import etree
from io import StringIO, BytesIO
import mysql.connector

db_config = {
        'user': 'root',
        'password': 'MY_GamB1t',
        'host': 'localhost',
        'database': 'ftpd',
        'charset': 'utf8',
        'use_unicode': True,
        'get_warnings': True,
    }

queue = greenstalk.Client(host='127.0.0.1', port=11300, encoding=None)
exitProcess = False

dbCnx = None
#dbCur = None

dbCnx = mysql.connector.connect(**db_config)
dbCur = dbCnx.cursor(buffered=True)

def exit_process(signum, frame):
    print('\nExit or Interrupt received, exiting!')
    global exitProcess
    exitProcess = True
    return

def main():
    signal.signal(signal.SIGINT, exit_process)
    signal.signal(signal.SIGTERM, exit_process)

    while True:
        if exitProcess:
            break

        try:
            job = queue.reserve(5)
            data = msgpack.unpackb(job.body)
            filename = data.decode('utf-8')
            print('Received: ', filename)

            # Check the file ends with .xml
            if not filename.endswith('.xml'):
                print('File: ', filename, ' is invalid')
            else:
                # Send file to parse function
                parse_cmdfile(filename)

            # Either way the file needs to be deleted
            try:
                os.remove(filename)
            except Exception as e:
                print('Error deleting file')


            # Remove the job from the job queue
            queue.delete(job)
        except Exception as e:
            pass

def parse_cmdfile(filename):
    # TODO: Parse the cmdfile
    print('Parsing file: ', filename)
   
    if not os.path.isfile(filename):
        print('CommandFile not found: ', filename)
        return

    # Load the xml file into memory
    tree = etree.parse(filename)
    root = tree.getroot()

    # Check this is a CmdFile
    if (root.tag != 'CommandFile'):
        print('File: ', filename, ' is XML however, not a CommandFile!')

    # Continue to process each command
    for child in root:
        print('Command Found: ', child.tag, ' ', child.attrib)
        
        # Call the function to handle this
        globals()['cmd_' + child.tag](child)

    return

def cmd_DeleteHost(el):
    print('Called Command: DeleteHost')
    for child in el:
        if child.tag == 'Domain':
            domain = child.text
        elif child.tag == 'Password':
            password = child.text

    try:
        delete_host(domain, password)
        delete_homedir(domain)
    except Exception as e:
        print(e)

    return

def cmd_NewHost(el):
    print('Called Command: NewHost')

    features = {}

    # Get domain and settings
    for child in el:
        if child.tag == 'Domain':
            domain = child.text
        elif child.tag == 'Password':
            password = child.text
        elif child.tag == 'Features':
            for feature in child:
                features[feature.tag.lower()] = feature.text

    if not domain or not password:
        print('Error: Domain and Password are required in NewHost Command!')

    try:
        # Check if domain already in DB
        if host_exists(domain):
            print('The host already exists, ', domain)
            return
    except Exception as e:
        print(e)
        return

    # We are good to insert a new host record
    

    # TODO: insert domain/host features
    #  This is skipped for now, but may be needed for some features, maybe "Editable Content"

    # Create directory

    inserted = insert_host(domain, password)

    if not inserted:
        print('Error creating record in database.')

    if inserted:
        create_homedir(domain)
        #print('Error creating homedir.')

    print('Domain: ', domain)
    print('Password: ', password)
    print('Features: ', features)
    return

def host_exists(domain):
    print('SELECT * FROM ftpuser WHERE userid = \'%s\'' % (domain))
    cursor = dbCnx.cursor(buffered=True)
    cursor.execute('SELECT * FROM ftpuser WHERE userid = \'%s\'' % (domain))
    
    count = cursor.rowcount
    cursor.close()

    if count > 0:
        return True

    return False

def get_hosts():
    cursor = dbCnx.cursor(buffered=True)
    cursor.execute('SELECT * FROM ftpuser')
    for row in cursor.fetchall():
        print(row)

    cursor.close()
    return

def insert_host(domain, password):

    res = False
    homedir = '/var/www/hosts/' + domain
    # Insert into DB
    try:
        cursor = dbCnx.cursor(buffered=True)
        cursor.execute('INSERT INTO ftpuser (userid, passwd, homedir, accessed, modified) VALUES (\'%s\', \'%s\', \'%s\', NOW(), NOW())' % (domain, password, homedir))

        dbCnx.commit()
        
        res = True
    except Exception as e:
        print(e)

    finally:
        cursor.close()

    return res

def delete_host(domain, password):

    res = False
    try:
        cursor = dbCnx.cursor(buffered=True)
        cursor.execute('DELETE FROM ftpuser WHERE userid = \'%s\' AND passwd = \'%s\'' % (domain, password))

        dbCnx.commit()
        res = True
    except:
        print(e)
    finally:
        cursor.close()

    return res

def create_homedir(domain):
    homedir = '/var/www/hosts/' + domain

    res = False

    try:
        os.mkdir(homedir)
        os.chmod(homedir, 0o775)
        os.chown(homedir, 5500, 5500)
        #shutil.chown(homedir, user=5500, group=5500)
        
        #import subprocess
        #subprocess.run(['expect', 'script.exp', domain])
        #subprocess.call(['python', 'chown.py', domain])
        
        res = True
    except Exception as e:
        print('Error creating homedir: ', e)

    return res

def delete_homedir(domain):
    homedir = '/var/www/hosts/' + domain

    res = False

    try:
        shutil.rmtree(homedir)
        res = True
    except Exception as e:
        print(e)

    return res



if __name__ == '__main__':
    main()
