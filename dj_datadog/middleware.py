# std lib
import time
import traceback

try:
    import json
except ImportError:
    import simplejson as json

# six
from six import integer_types, string_types

# django
from django.conf import settings
from django.http import Http404

# datadog
from datadog import api, initialize, statsd


# init datadog api
initialize(api_key=settings.DATADOG_API_KEY, app_key=settings.DATADOG_APP_KEY)


class DatadogMiddleware(object):
    DD_TIMING_ATTRIBUTE = '_datadog_start_time'

    def __init__(self):
        app_name = settings.DATADOG_APP_NAME
        self.error_metric = '{0}.errors'.format(app_name)
        self.timing_metric = '{0}.request_time'.format(app_name)
        self.event_tags = [app_name, 'exception']

    def process_request(self, request):
        setattr(request, self.DD_TIMING_ATTRIBUTE, time.time())

    def process_response(self, request, response):
        """ Submit timing metrics from the current request """
        if not hasattr(request, self.DD_TIMING_ATTRIBUTE):
            return response

        # Calculate request time and submit to Datadog
        response_time = time.time() - getattr(request,
                                              self.DD_TIMING_ATTRIBUTE)
        tags = self._get_metric_tags(request)

        api.Metric.send(metric=self.timing_metric,
                        points=response_time, tags=tags)

        return response

    def process_exception(self, request, exception):
        """ Captures Django view exceptions as Datadog events """

        # ignore the Http404 exception
        if isinstance(exception, Http404):
            return

        # Get a formatted version of the traceback.
        exc = traceback.format_exc()

        # Make request.META json-serializable.
        szble = {}
        for k, v in request.META.items():
            if isinstance(v,
                          string_types + integer_types + (list, bool, float)):
                # TODO: check within the list
                szble[k] = v
            else:
                szble[k] = str(v)

        title = 'Exception from {0}'.format(request.path)
        text = "Traceback:\n@@@\n{0}\n@@@\nMetadata:\n@@@\n{1}\n@@@" \
            .format(exc, json.dumps(szble, indent=2))

        # Submit the exception to Datadog
        api.Event.create(title=title,
                         text=text,
                         tags=self.event_tags,
                         aggregation_key=request.path,
                         alert_type='error')

        # Increment our errors metric
        tags = self._get_metric_tags(request)
        statsd.increment(self.error_metric, tags=tags)

    def _get_metric_tags(self, request):
        return ['path:{0}'.format(request.path)]
