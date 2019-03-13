import os
import sys
from uuid import getnode as get_mac

class ClientInformation():

    def __init__(self):

        self.addon = "temp"

    def logMsg(self, msg, lvl=1):

        className = self.__class__.__name__
        # utils.logMsg("%s %s" % (self.addonName, className), msg, int(lvl))
        if lvl < 1:
            print >> sys.stderr, msg
    
    def getVersion(self):

        return "0.1.0"

    def getDeviceName(self):

        return "TurnkeyLinux"
    
    def getMachineId(self):
    
        return "%012X"%get_mac()
        
    def getPlatform(self):

        return "Linux/RPi"

import requests
import json
import logging

#from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable requests logging
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#logging.getLogger("requests").setLevel(logging.WARNING)

class DownloadUtils():
    
    # Borg - multiple instances, shared state
    _shared_state = {}
    clientInfo = ClientInformation()

    # Requests session
    s = None
    timeout = 60

    def __init__(self):

        self.__dict__ = self._shared_state

    def logMsg(self, msg, lvl=1):

        self.className = self.__class__.__name__
        # utils.logMsg("%s %s" % (self.addonName, self.className), msg, int(lvl))
        if lvl < 1:
            print >> sys.stderr, msg

    def setUsername(self, username):
        # Reserved for UserClient only
        self.username = username
        self.logMsg("Set username: %s" % username, 2)

    def setUserId(self, userId):
        # Reserved for UserClient only
        self.userId = userId
        self.logMsg("Set userId: %s" % userId, 2)

    def setServer(self, server):
        # Reserved for UserClient only
        self.server = server
        self.logMsg("Set server: %s" % server, 2)

    def setToken(self, token):
        # Reserved for UserClient only
        self.token = token
        self.logMsg("Set token: %s" % token, 2)

    def setSSL(self, ssl, sslclient):
        # Reserved for UserClient only
        self.sslverify = ssl
        self.sslclient = sslclient
        self.logMsg("Verify SSL host certificate: %s" % ssl, 2)
        self.logMsg("SSL client side certificate: %s" % sslclient, 2)

    def startSession(self):

        self.deviceId = self.clientInfo.getMachineId()

        # User is identified from this point
        # Attach authenticated header to the session
        verify = None
        cert = None
        header = self.getHeader(json=True)

        # Start session
        self.s = requests.Session()
        self.s.headers = header
        self.s.verify = verify
        self.s.cert = cert
        # Retry connections to the server
        self.s.mount("http://", requests.adapters.HTTPAdapter(max_retries=1))
        self.s.mount("https://", requests.adapters.HTTPAdapter(max_retries=1))

        self.logMsg("Requests session started on: %s" % self.server)

    def stopSession(self):
        try:
            self.s.close()
        except:
            self.logMsg("Requests session could not be terminated.", 1)

    def getHeader(self, json=False, authenticate=True):

        clientInfo = self.clientInfo

        deviceName = clientInfo.getDeviceName()
        deviceId = clientInfo.getMachineId()
        version = clientInfo.getVersion()

        content = 'application/x-www-form-urlencoded; charset=UTF-8'
        if json:
            content = 'application/json; charset=UTF-8'

        if not authenticate:
            # If user is not authenticated
            auth = 'MediaBrowser Client="PC", Device="%s", DeviceId="%s", Version="%s"' % (deviceName, deviceId, version)
            header = {'Content-type': content, 'Accept-encoding': 'gzip', 'Accept-Charset': 'UTF-8,*', 'Authorization': auth}      
            
            self.logMsg("Header: %s" % header, 2)
            return header
        
        else:
            userId = self.userId
            token = self.token
            # Attached to the requests session
            auth = 'MediaBrowser UserId="%s", Client="PC", Device="%s", DeviceId="%s", Version="%s"' % (userId, deviceName, deviceId, version)
            header = {'Content-type': content, 'Accept-encoding': 'gzip', 'Accept-Charset': 'UTF-8,*', 'Authorization': auth, 'X-MediaBrowser-Token': token}        
                    
            self.logMsg("Header: %s" % header, 2)
            return header

    def downloadUrl(self, url, postBody=None, type="GET", json=True, authenticate=True):
        
        self.logMsg("=== ENTER downloadUrl ===", 2)

        timeout = self.timeout
        default_link = ""

        try:

            # If user is authenticated
            if (authenticate):
                # Get requests session
                try: 
                    s = self.s
                    s.headers = self.getHeader(json=json)

                    # Replace for the real values and append api_key
                    url = url.replace("{server}", self.server, 1)
                    url = url.replace("{UserId}", self.userId, 1)

                    self.logMsg("URL: %s" % url, 2)
                    # Prepare request
                    if type == "GET":
                        if json:
                            r = s.get(url, json=postBody, timeout=timeout)
                        else:
                            r = s.get(url, data=postBody, timeout=timeout)
                    elif type == "POST":
                        if json:
                            r = s.post(url, json=postBody, timeout=timeout)
                        else:
                            r = s.post(url, data=postBody, timeout=timeout)
                    elif type == "DELETE":
                        if json:
                            r = s.delete(url, json=postBody, timeout=timeout)
                        else:
                            r = s.delete(url, data=postBody, timeout=timeout)
                
                except AttributeError:
                    
                    # Get user information
                    # self.username = WINDOW.getProperty('currUser')
                    # self.userId = WINDOW.getProperty('userId%s' % self.username)
                    # self.server = WINDOW.getProperty('server%s' % self.username)
                    # self.token = WINDOW.getProperty('accessToken%s' % self.username)
                    header = self.getHeader(json=json)
                    verifyssl = False
                    cert = None

                    # Replace for the real values and append api_key
                    url = url.replace("{server}", self.server, 1)
                    url = url.replace("{UserId}", self.userId, 1)

                    self.logMsg("URL: %s" % url, 2)
                    # Prepare request
                    if type == "GET":
                        if json:
                            r = requests.get(url, json=postBody, headers=header, timeout=timeout, cert=cert, verify=verifyssl)
                        else:
                            r = requests.get(url, data=postBody, headers=header, timeout=timeout, cert=cert, verify=verifyssl)
                    elif type == "POST":
                        if json:
                            r = requests.post(url, json=postBody, headers=header, timeout=timeout, cert=cert, verify=verifyssl)
                        else:
                            r = requests.post(url, data=postBody, headers=header, timeout=timeout, cert=cert, verify=verifyssl)
                    elif type == "DELETE":
                        if json:
                            r = requests.delete(url, json=postBody, headers=header, timeout=timeout, cert=cert, verify=verifyssl)
                        else:
                            r = requests.delete(url, data=postBody, headers=header, timeout=timeout, cert=cert, verify=verifyssl)
                
            # If user is not authenticated
            elif not authenticate:
                
                self.logMsg("URL: %s" % url, 2)
                self.logMsg("Data: %s" % postBody, 2)
                header = self.getHeader(json=json, authenticate=False)
                verifyssl = False

                # Prepare request
                if type == "GET":
                    if json:
                        r = requests.get(url, json=postBody, headers=header, timeout=timeout, verify=verifyssl)
                    else:
                        r = requests.get(url, data=postBody, headers=header, timeout=timeout, verify=verifyssl)
                elif type == "POST":
                    if json:
                        r = requests.post(url, json=postBody, headers=header, timeout=timeout, verify=verifyssl)
                    else:
                        r = requests.post(url, data=postBody, headers=header, timeout=timeout, verify=verifyssl)
        
            # Process the response
            if r.status_code == 204:
                # No body in the response
                self.logMsg("====== 204 Success ======", 2)
                return default_link

            elif r.status_code == requests.codes.ok:
                try: 
                    # UTF-8 - JSON object
                    r = r.json()
                    self.logMsg("====== 200 Success ======", 2)
                    self.logMsg("Response: %s" % r, 2)
                    return r
                except:
                    if "text/html" in r.headers['content-type']:
                        self.logMsg("====== 200 Success ======", 2)
                        if url != r.url:
                            self.logMsg("Request URL: %s" % url, 2)
                            self.logMsg("Response URL: %s" % r.url, 2)
                            return "Redirect"
                        pass
                    else:
                        self.logMsg("Unable to convert the response for: %s" % url, 1)
                        self.logMsg("Content-type: %s" % r.headers['content-type'], 1)
            else:
                self.logMsg("Status: %s" % r.status_code, 2)
                r.raise_for_status()

            return default_link
        
        # TO REVIEW EXCEPTIONS
        except requests.exceptions.ConnectionError as e:
            # Make the addon aware of status
            self.logMsg("Server unreachable at: %s" % url, 0)
            self.logMsg(e, 2)
            pass

        except requests.exceptions.ConnectTimeout as e:
            self.logMsg("Server timeout at: %s" % url, 0)
            self.logMsg(e, 1)

        except requests.exceptions.HTTPError as e:

            if r.status_code == 401:
                # Unauthorized
                if 'x-application-error-code' in r.headers:
                    if r.headers['X-Application-Error-Code'] == "ParentalControl":
                        # Parental control - access restricted
                        return False
                    elif r.headers['X-Application-Error-Code'] == "UnauthorizedAccessException":
                        # User tried to do something his jellyfin account doesn't allow - admin restricted in some way
                        pass

                else:
                    # Tell UserClient token has been revoked.
                    self.logMsg("HTTP Error: %s" % e, 0)
                    return 401

            elif (r.status_code == 301) or (r.status_code == 302):
                # Redirects
                return r.status_code
            elif r.status_code == 400:
                # Bad requests
                pass

        except requests.exceptions.SSLError as e:
            self.logMsg("Invalid SSL certificate for: %s" % url, 0)
            self.logMsg(e, 1)

        except requests.exceptions.RequestException as e:
            self.logMsg("Unknown error connecting to: %s" % url, 0)
            self.logMsg(e, 1)

        return default_link

import hashlib
import json as json

class UserClient():

    # Borg - multiple instances, shared state
    _shared_state = {}

    clientInfo = ClientInformation()
    doUtils = DownloadUtils()
    
    stopClient = False
    logLevel = 2
    auth = True
    retry = 0

    currUser = None
    currUserId = None
    currServer = None
    currToken = None
    HasAccess = True
    currPass = ""

    def __init__(self):

        self.__dict__ = self._shared_state

    def logMsg(self, msg, lvl=1):
        
        className = self.__class__.__name__
        # utils.logMsg("%s %s" % (self.addonName, className), str(msg), int(lvl))
        if lvl < 1:
            print >> sys.stderr, msg

    def getUsername(self):

        return "jellyfin"

    def getUserId(self):

        return self.currUserId

    def getServer(self, prefix=True):

        # For https support
        HTTPS = "false"
        host = "127.0.0.1"
        port = "8096"
            
        server = host + ":" + port
        
        if host == "":
            self.logMsg("No server information saved.", 2)
            return ""

        # If https is true
        if prefix and (HTTPS == "true"):
            server = "https://%s" % server
            return server
        # If https is false
        elif prefix and (HTTPS == "false"):
            server = "http://%s" % server
            return server
        # If only the host:port is required
        elif (prefix == False):
            return server

    def getToken(self):

        return self.currToken

    def getSSLverify(self):

        return False

    def getSSL(self):

        return None

    def getPublicUsers(self):

        server = self.getServer()

        # Get public Users
        url = "%s/mediabrowser/Users/Public?format=json" % server
        result = self.doUtils.downloadUrl(url, authenticate=False)
        
        users = []
        
        if (result != ""):
            users = result
        else:
            # Server connection failed
            return False

        return users

    def hasAccess(self):

        url = "{server}/mediabrowser/Users"
        result = self.doUtils.downloadUrl(url)
        
        if result is False:
            # Access is restricted
            self.logMsg("Access is restricted.")
            self.HasAccess = False
            return

        self.HasAccess = True
        return

    def hashPassword(self, password=""):
        sha1 = hashlib.sha1(password)
        return sha1.hexdigest()    

    def loadCurrUser(self, authenticated=False):

        doUtils = self.doUtils
        username = self.getUsername()

        # Only to be used if token exists
        self.currUserId = self.getUserId()
        self.currServer = self.getServer()
        self.currToken = self.getToken()
        self.ssl = self.getSSLverify()
        self.sslcert = self.getSSL()

        # Test the validity of current token
        if authenticated == False:
            url = "%s/mediabrowser/Users/%s" % (self.currServer, self.currUserId)
            result = doUtils.downloadUrl(url)
            if result == 401:
                # Token is no longer valid
                self.resetClient()
                return False

        # Set DownloadUtils values
        doUtils.setUsername(username)
        doUtils.setUserId(self.currUserId)
        doUtils.setServer(self.currServer)
        doUtils.setToken(self.currToken)
        doUtils.setSSL(self.ssl, self.sslcert)
        # parental control - let's verify if access is restricted
        self.hasAccess()
        # Start DownloadUtils session
        doUtils.startSession()

        self.currUser = username

    def authenticate(self):

        username = self.getUsername()
        server = self.getServer()

        # If no user information
        if (server == "") or (username == ""):
            self.logMsg("Missing server information.")
            self.auth = False
            return
        # If there's a token
        if (self.getToken() != None):
            result = self.loadCurrUser()

            if result == False:
                pass
            else:
                self.logMsg("Current user: %s" % self.currUser, 0)
                self.logMsg("Current userId: %s" % self.currUserId, 0)
                self.logMsg("Current accessToken: %s" % self.currToken, 0)
                return
        
        users = self.getPublicUsers()
        password = ""
        
        # Find user in list
        for user in users:
            name = user[u'Name']
            userHasPassword = False

            if (unicode(username, 'utf-8') in name):
                # Verify if user has a password
                if (user.get("HasPassword") == True):
                    userHasPassword = True
                # If user has password
                if (userHasPassword):
                    password = self.currPass
                break
        else:
            # Manual login, user is hidden
            password = self.currPass
            
        sha1 = self.hashPassword(password)

        # Authenticate username and password
        url = "%s/mediabrowser/Users/AuthenticateByName?format=json" % server
        data = {'username': username, 'password': sha1}
        self.logMsg(data, 2)

        result = self.doUtils.downloadUrl(url, postBody=data, type="POST", authenticate=False)

        accessToken = None
        try:
            self.logMsg("Auth_Reponse: %s" % result, 1)
            accessToken = result[u'AccessToken']
        except:
            pass

        if (result != None and accessToken != None):
            self.currUser = username
            userId = result[u'User'][u'Id']
            self.currToken = accessToken
            self.currUserId = userId
            self.logMsg("User Authenticated: %s" % accessToken)
            self.loadCurrUser(authenticated=True)
            self.retry = 0
            return
        else:
            self.logMsg("User authentication failed.")
            self.currToken = None
            self.currUserId = None
            
            # Give two attempts at entering password
            self.retry += 1
            if self.retry == 2:
                self.logMsg("Too many retries.")
            
            self.auth = False
            return

    def resetClient(self):

        username = self.getUsername()
        self.logMsg("Reset UserClient authentication.", 1)
        if (self.currToken != None):
            # In case of 401, removed saved token
            self.currToken = None
            self.logMsg("User token has been removed.", 1)
        
        self.auth = True
        self.currUser = None
        return


