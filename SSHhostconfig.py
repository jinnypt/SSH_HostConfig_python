#/usr/bin/env pyhton

import sys
import paramiko
import os.path
import re
import threading
import subprocess
import time
import argparse

def main(argv):
  global ips_file
  global users_file
  global commands_file
 
  parser = argparse.ArgumentParser(add_help=True)
  parser.add_argument('-i', action='store', dest='ips_file', type=str, help='File with IP addresses for hosts.')
  parser.add_argument('-u', action='store', dest='users_file', type=str, help='File with user/password.')
  parser.add_argument('-c', action='store', dest='commands_file', type=str, help='File with commands to run in hosts.')

  arguments = parser.parse_args()

  if (arguments.ips_file is None) or (arguments.users_file is None) or (arguments.commands_file is None):
    print parser.print_help()
    sys.exit()

  ips_file = arguments.ips_file
  users_file = arguments.users_file
  commands_file = arguments.commands_file

  #print ips_file,users_file,commands_file

  # Check that the files provided actually exist
  if os.path.isfile(ips_file) == False:
    print "\n*** File: %s does not exists. Check file name." % ips_file
    sys.exit()
  elif os.path.isfile(users_file) == False:
    print "\n*** File: %s does not exists. Check file name." % users_file
    sys.exit()
  elif os.path.isfile(commands_file) == False:
    print "\n*** File: %s does not exists. Check file name." % commands_file
    sys.exit()

  try:
    ip_addresses_list = read_file(ips_file,'r')

    #print "address: " + str(ip_addresses_list)
  
    for ip in ip_addresses_list:
      if not ip_is_valid(ip):
        print "\n*** One of the IP addresses is INVALID. Please check your file and try again.\n"
        sys.exit()

    # Check if IP addresses are reachable 
    reachable_ip_list = []
    for ip in ip_addresses_list:
      if is_pingable(ip) == 0:
        reachable_ip_list.append(ip)
      elif is_pingable(ip) == 2:
        print "\nHost not responding at %s - Returns 2" % ip
      else:
        print "\nPing at address %s FAILED." % ip
    #print reachable_ip_list

    # Get username and password
    users_list = read_file(users_file,'r')
    username = users_list[0].split(',')[0]
    password = users_list[0].split(',')[1]
    #print "User/Password: ", username, password 
    
    # Run commands from command file
    commands_list = read_file(commands_file, 'r')
    
    threads = []
    for ip in reachable_ip_list:
      th = threading.Thread(target = run_over_ssh, args = (ip,username,password,commands_list))
      th.start()
      threads.append(th)

    for th in threads:
      th.join()

  except KeyboardInterrupt:
    print "\n\n* Program aborted by user. Exiting..."
    sys.exit()


#################################################################

def read_file(file_name,mode):
  try:
    file_obj = open(file_name,'r') 
  except IOError:
    print "\n* File %s does NOT exists. Check the name and try again. \n" % ips_file
    sys.exit() 

  file_obj.seek(0)
  output_list = file_obj.read().splitlines()
  file_obj.close()
  return output_list

def is_pingable(ip):
  ping_output = subprocess.call(['ping', '-c', '2', '-w', '2', '-q', '-n', ip])
  return ping_output

def ip_is_valid(ip_address):
  ip = ip_address.split('.')

  if (len(ip) == 4) and \
      (1 <= int(ip[0]) <= 223) and \
      (int(ip[0]) != 127) and \
      (int(ip[0]) != 169 or int(a[1]) != 254) and \
      (0 <= int(ip[1]) <= 255 and 0 <= int(ip[2]) <= 255 and 0 <= int(ip[3]) <= 255):
    valid = True   
  else:
    print "The IP Address: '%s' is invalid. Please retry\n" % ".".join(ip)

    valid = False
  return valid

def run_over_ssh(ip, username,password,commands_list):
  session = paramiko.SSHClient()

  # Accepts unknown host keys. For testing environment only. Not for production
  session.set_missing_host_key_policy(paramiko.AutoAddPolicy())

  session.connect(ip, username = username, password = password)
  connection = session.invoke_shell()

  for command in commands_list:
    #print command
    connection.send(command + '\n')
    time.sleep(3)
  
  output = connection.recv(65535)
  print output

if __name__ == "__main__":
    main(sys.argv)
