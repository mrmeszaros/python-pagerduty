#!/usr/bin/env python3

try:
    import json
except ImportError:
    import simplejson as json

from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen

import base64

from upagerduty.version import VERSION

__version__ = VERSION

class SchedulesError(HTTPError):
    def __init__(self, http_error):
        HTTPError.__init__(self, http_error.filename, http_error.code, http_error.msg, http_error.hdrs, http_error.fp)

        try:
            data = self.read()
        
            j = json.loads(data)
            error = j['error']
            self.statuscode = error['code']
            self.statusdesc = ' | '.join(error.get('errors', []))
            self.errormessage = error['message']
        except:
            pass

    def __repr__(self):
        return 'Pagerduty Schedules Error: HTTP {0} {1} returned with message, "{2}"'.format(self.statuscode, self.statusdesc, self.errormessage)

    def __str__(self):
        return self.__repr__()

class SchedulesRequest(Request):
    def __init__(self, connection, resource, params):
        """Representation of a Pagerduty Schedules API HTTP request.
        
        :type connection: :class:`Schedules`
        :param connection: Schedules connection object populated with a username, password and base URL
        
        :type resource: string
        :param resource: Pagerduty resource to query (lowercase)
        
        :type params: dict
        :param params: Params to be sent with a GET request
        
        """

        encoded_params = urlencode(params)
        url = connection.base_url + resource + '?' + encoded_params
        Request.__init__(self, url)

        # Add auth header
        base64string = base64.encodestring('%s:%s' % (connection.username, connection.password)).replace('\n','')
        self.add_header("Authorization", "Basic %s" % base64string)

    
    def __repr__(self):
        return 'SchedulesRequest: {0} {1}' % (self.get_method(), self.get_full_url())
        
        
    def fetch(self):
        """Execute the request."""
        try:
            response = urlopen(self)
        except HTTPError as e:
            raise SchedulesError(e)
        else:
            return SchedulesResponse(response)
        

class SchedulesResponse(object):
    def __init__(self, response):
        """Representation of a Pagerduty Schedules API HTTP response."""
        self.data = response.read()

        self.headers = response.headers
        self.content = json.loads(self.data)
        
        if 'error' in self.content:
            raise SchedulesError(self.content)


    def __repr__(self):
        return 'SchedulesResponse: {0}'.format(list(self.content.items()))

class Schedules(object):
    """ Interface to Pagerduty Schedule API.
    """
    def __init__(self, subdomain, schedule_id, username, password):

        self.username = username
        self.password = password

        self.base_url = 'https://{0}.pagerduty.com/api/v1/schedules/{1}/'.format(subdomain, schedule_id)

    def entries(self, since, until, overflow=False):
        """ Query schedule entries.  
            The maximum range queryable at once is three months. Error raised if this is violated.

            :type since: string
            :param since: date in ISO 8601 format, the time element is optional 
            (ie. '2011-05-06' is understood as at midnight ) 
        
            :type until: string
            :param until: date in ISO 8601 format, the time element is optional 
            (ie. '2011-05-06' is understood as at midnight )

            :type overflow: boolean
            :param overflow: if True on call schedules are returned the way they are entered
                             if False only the overlaps of the on call schedules 
                                with the time period between since and until are returned
        """
        params = {'since' : since, 'until' : until}
        if overflow:
            params.update({'overflow' : True})

        request = SchedulesRequest(self, 'entries', params)
        response = request.fetch()

        return response.content['entries']


class PagerDutyException(Exception):
    def __init__(self, status, message, errors):
        super(PagerDutyException, self).__init__(message)
        self.msg = message
        self.status = status
        self.errors = errors
    
    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.status, self.msg, self.errors)
    
    def __str__(self):
        txt = "%s: %s" % (self.status, self.msg)
        if self.errors:
            txt += "\n" + "\n".join("* %s" % x for x in self.errors)
        return txt

class PagerDuty(object):
    def __init__(self, service_key, https=True, timeout=15):
        self.service_key = service_key
        self.api_endpoint = ("http", "https")[https] + "://events.pagerduty.com/generic/2010-04-15/create_event.json"
        self.timeout = timeout
    
    def trigger(self, description, incident_key=None, details=None):
        return self._request("trigger", description=description, incident_key=incident_key, details=details)
    
    def acknowledge(self, incident_key, description=None, details=None):
        return self._request("acknowledge", description=description, incident_key=incident_key, details=details)
    
    def resolve(self, incident_key, description=None, details=None):
        return self._request("resolve", description=description, incident_key=incident_key, details=details)
    
    def _request(self, event_type, **kwargs):
        event = {
            "service_key": self.service_key,
            "event_type": event_type,
        }
        for k, v in kwargs.items():
            if v is not None:
                event[k] = v
        encoded_event = json.dumps(event).encode('utf-8')
        try:
            res = urlopen(self.api_endpoint, encoded_event, self.timeout)
        except HTTPError as exc:
            if exc.code != 400:
                raise
            res = exc
        
        result = json.loads(res.read())
        
        if result['status'] != "success":
            raise PagerDutyException(result['status'], result['message'], result['errors'])
        
        # if result['warnings]: ...
        
        return result.get('incident_key')

class IncidentsError(HTTPError):
    def __init__(self, http_error):
        HTTPError.__init__(self, http_error.filename, http_error.code, http_error.msg, http_error.hdrs, http_error.fp)

        self.statuscode = http_error.code
        self.statusdesc = http_error.msg
        self.errormessage = ''

        try:
            data = self.read()
        
            j = json.loads(data)
            error = j['error']
            self.statuscode = error['code']
            self.statusdesc = ' | '.join(error.get('errors', []))
            self.errormessage = error['message']
        except:
            pass

    def __repr__(self):
        return 'Pagerduty Incidents Error: HTTP {0} {1} returned with message, "{2}"'.format(self.statuscode, self.statusdesc, self.errormessage)

    def __str__(self):
        return self.__repr__()

class IncidentsRequest(Request):
    def __init__(self, connection, params):
        """Representation of a Pagerduty Incidents API HTTP request.

        :type connection: :class:`Incidents`
        :param connection: Incidents connection object populated with a username, password and base URL

        :type params: dict
        :param params: Params to be sent with a GET request

        """

        encoded_params = urlencode(params)
        url = connection.base_url + '?' + encoded_params
        Request.__init__(self, url)

        # Add auth header
        base64string = base64.encodestring('%s:%s' % (connection.username, connection.password)).replace('\n','')
        self.add_header("Authorization", "Basic %s" % base64string)

    def __repr__(self):
        return 'IncidentsRequest: {0} {1}' % (self.get_method(), self.get_full_url())

    def fetch(self):
        """Execute the request."""
        try:
            response = urlopen(self)
        except HTTPError as e:
            raise IncidentsError(e)
        else:
            return IncidentsResponse(response)

class IncidentsResponse(object):
    def __init__(self, response):
        """Representation of a Pagerduty Incidents API HTTP response."""
        self.data = response.read()

        self.headers = response.headers
        self.content = json.loads(self.data)

        if 'error' in self.content:
            raise IncidentsError(self.content)

    def __repr__(self):
        return 'IncidentsResponse: {0}'.format(list(self.content.items()))

class Incidents(object):
    """ Interface to Pagerduty Incident API.
    """
    def __init__(self, subdomain, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://{0}.pagerduty.com/api/v1/incidents'.format(subdomain)

    def _make_request(self, since, until, limit, offset):
        params = {'since' : since, 'until' : until, 'limit' : limit, 'offset' : offset}

        request = IncidentsRequest(self, params)
        response = request.fetch()

        return response.content['total'], response.content['incidents']

    def all(self, since, until):
        """ Query incidents.
            The maximum range queryable at once is 100 incidents.
            This function returns an iterator that handles pagination for you.

            :type since: string
            :param since: date in ISO 8601 format, the time element is optional 
            (ie. '2011-05-06' is understood as at midnight ) 

            :type until: string
            :param until: date in ISO 8601 format, the time element is optional 
            (ie. '2011-05-06' is understood as at midnight )
        """
        limit = 100

        total, incidents = self._make_request(since, until, limit, 0)

        for i in incidents:
            yield i

        if total > limit:
            num_pages = (total / limit) + 1
            for page in range(1, num_pages):
                offset = page * limit
                total, incidents = self._make_request(since, until, limit, offset)
                for i in incidents:
                    yield i
