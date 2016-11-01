# std lib
import time
import traceback
import logging
import os

try:
    import json
except ImportError:
    import simplejson as json

# django
from django.conf import settings
from django.http import Http404

# third party
from datadog import api, initialize, statsd
from six import integer_types, string_types
import psutil


logger = logging.getLogger(__name__)

try:
    dj_debug = settings.DJ_DATADOG_DEBUG
except AttributeError:
    dj_debug = False

# init datadog api
if not dj_debug:
    initialize(api_key=settings.DATADOG_API_KEY,
               app_key=settings.DATADOG_APP_KEY)
else:
    logger.info('Intializing dj_datadog')


def send_metric(*args, **kwargs):
    """Sends datadog api metric if non-debug mode

    Accepts the same parameters as `datadog.api.Metric.send`
    In debug mode, the metrics are sent to log file instead"""

    if not dj_debug:
        api.Metric.send(*args, **kwargs)
    else:
        logger.info("datadog metrics: %r %r " % (args, kwargs,))


def create_event(*args, **kwargs):
    """Creates a datadog event if non-debug mode

    Accepts the same parameters as `datadog.api.Event.create`
    In debug mode, the metrics are sent to log file instead"""

    if not dj_debug:
        api.Event.create(*args, **kwargs)
    else:
        logger.info("datadog event: %r %r" % (args, kwargs,))


class MemoryUsageMiddleware(object):
    DD_MEM_ATTR = '_datadog_mem'
    MEM_METRIC = '{0}.memory_usage'.format(settings.DATADOG_APP_NAME)

    def process_request(self, request):
        mem_info = psutil.Process(os.getpid()).memory_info()
        setattr(request, self.DD_MEM_ATTR, mem_info)

    def process_response(self, request, response):
        """Submit metrics on memory usage spike"""

        if not hasattr(request, self.DD_MEM_ATTR):
            return response

        curr = psutil.Process(os.getpid()).memory_info()
        prev = getattr(request, self.DD_MEM_ATTR)
        diff = curr.rss - prev.rss
        mb = float(diff) / 1000000

        tags = self._get_metric_tags(request)

        send_metric(metric=self.MEM_METRIC,
                    points=mb, tags=tags)

        return response

    def _get_metric_tags(self, request):
        return ['path:{0}'.format(request.path)]


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

        send_metric(metric=self.timing_metric,
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
        create_event(title=title,
                     text=text,
                     tags=self.event_tags,
                     aggregation_key=request.path,
                     alert_type='error')

        # Increment our errors metric
        tags = self._get_metric_tags(request)
        statsd.increment(self.error_metric, tags=tags)

    def _get_metric_tags(self, request):
        return ['path:{0}'.format(request.path)]
