# Import the needed Ignition calls
from system.net import httpPost, httpPut, httpGet, httpDelete

from twilio.compat.six import (
    integer_types,
    string_types,
    binary_type,
    iteritems
)
from urllib import urlencode
from urlparse import urlparse, urljoin

class IgnitionHttpRequest(object):
    """Class for replacing httplib2 with Ignition calls.

    Proxy info is stored for convenience.
    """
    _proxy_info = None

    @staticmethod
    def get_status_code(exception):
        """Scans the exception and attempts to parse out the response code.
        """
        import re
        
        pattern = 'HTTP response code: ([0-9]{3}) for URL: (http[s]?://.*)'
        regex = re.compile(pattern)
        match = regex.findall(str(exception))
        if match:
            return int(match[0][0])
        else:
            return 466

    @classmethod
    def set_proxy_info(cls, proxy_host, proxy_port='8080'):
        '''Set proxy configuration for future REST API calls.

        NOTE: this currently is only for naive proxy implementations!
        There's no authorization going on here!

        :param str proxy_host: Hostname of the proxy to use.
        :param int proxy_port: Port to connect to. Defaults to 8080.
        '''

        cls._proxy_info = (proxy_host, proxy_port)
    
    @classmethod
    def proxy_info(cls):
        '''Returns the currently-set proxy information
        as an httplib2.ProxyInfo object.
        '''
        return cls._proxy_info

    @classmethod
    def make_request(cls, method, url, 
                     connectTimeout=10000, readTimeout=60000,
                     headerValues=None, 
                     contentType=None, data=None, queryParams=None,
                     username=None, password=None,
                     proxy_host=None, proxy_port='8080',
                     bypassCertValidation=False):
        """Performs an HTTP request using the Ignition network library.

        data will be encoded via urlencode if it's a dict 
            as well as set contentType (if it's None)
   
        :param str method: The HTTP method to use
        :param str url: The URL to request

        :param int connectTimeout: Time in milliseconds to wait to timeout the connection attempt
        :param int readTimeout: Time in milliseconds to wait to timeout waiting for a response
        :param dict headers: HTTP Headers to send with the request (if username and password as included, the authorization header will be set automatically)

        :param dict data: Parameters to go in the body of the HTTP request (can be a pre-munged string)
        :param dict params: Query parameters to append to the URL
        
        :param str username: The endpoint's username to send
        :param str password: Paired with username for endpoint

        :return: An http response
        :rtype: A :class:`Response <models.Response>` object

        We'll be using the built-in Ignition system.net function calls for these requests.
        This is a migration from httplib2.
        """
        if not proxy_host and cls.proxy_info():
            proxy_host, proxy_port = cls.proxy_info()

        if data is not None:

            if isinstance(data, (dict,)):
                # encode the dictionary
                def encode_atom(atom):
	                if isinstance(atom, (integer_types, binary_type)):
	                    return atom
	                elif isinstance(atom, string_types):
	                    return atom.encode('utf-8')
	                else:
	                    raise ValueError('list elements should be an integer, '
	                                     'binary, or string')                

                udata = {}
                for k, v in iteritems(data):
                    key = k.encode('utf-8')
                    if isinstance(v, (list, tuple, set)):
                        udata[key] = [encode_atom(x) for x in v]
                    elif isinstance(v, (integer_types, binary_type, string_types)):
                        udata[key] = encode_atom(v)
                    else:
                        raise ValueError('data should be an integer, '
                                         'binary, or string, or sequence ')
                data = urlencode(udata, doseq=True)

                # We just encoded the data in this way, but still, make sure an override wasn't provided
                if not contentType:
                    contentType = "application/x-www-form-urlencoded"

        if queryParams is not None:
            enc_params = urlencode(queryParams, doseq=True)
            if urlparse(url).query:
                url = '%s&%s' % (url, enc_params)
            else:
                url = '%s?%s' % (url, enc_params)                

        #Assume failure, so at least *something* can get logged.
        content = '{"Error":"Incomplete request."}'
        response_status_code = 421 #I made this up - it's a placeholder failure.

        try:
            if method == 'POST':
                
                content = httpPost(url, headerValues=headerValues,
                                   contentType=contentType, postData=data,
                                   username=username, password=password,
                                   connectTimeout=connectTimeout, readTimeout=readTimeout,
                                   proxyUrl=proxy_host, proxyPort=proxy_port,
                                   bypassCertValidation=bypassCertValidation)
            
            elif method == 'PUT':

                content = httpPut (url, headerValues=headerValues,
                                   contentType=contentType, putData=data,
                                   username=username, password=password,
                                   connectTimeout=connectTimeout, readTimeout=readTimeout,
                                   proxyUrl=proxy_host, proxyPort=proxy_port,
                                   bypassCertValidation=bypassCertValidation)

            elif method == 'GET':

                content = httpGet (url, headerValues=headerValues,
                                   username=username, password=password,
                                   connectTimeout=connectTimeout, readTimeout=readTimeout,
                                   proxyUrl=proxy_host, proxyPort=proxy_port,
                                   bypassCertValidation=bypassCertValidation)

            elif method == 'DELETE':

                content = httpDelete (url, headerValues=headerValues,
                                      username=username, password=password,
                                      connectTimeout=connectTimeout, readTimeout=readTimeout,
                                      proxyUrl=proxy_host, proxyPort=proxy_port,
                                      bypassCertValidation=bypassCertValidation)

            else:
                raise NotImplementedError, "Only POST, PUT, GET, and DELETE methods are valid."

            response_status_code = 200

        except IOError, e:
            response_status_code = int(cls.get_status_code(e))
            content = '{"Error":"%s"}' % str(e)

        return response_status_code, content, url



