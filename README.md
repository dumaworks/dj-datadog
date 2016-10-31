# Django Datadog

A simple Django middleware for submitting timings and exceptions to Datadog.

This is a derivative work of conorbranagan's package 
https://github.com/conorbranagan/django-datadog updated to use the latest python
datadog API.

## Installation

Download the code into your project and install it.

```bash
git clone git://github.com/krmboya/dj-datadog.git
cd dj-datadog
python setup.py install
```

Add `dj_datadog` to your list of installed apps.

```python
INSTALLED_APPS += ('dj_datadog',)
```

Add the following configuration to your projects' `settings.py` file:

```python
DATADOG_API_KEY = 'YOUR_API_KEY'
DATADOG_APP_KEY = 'YOUR_APP_KEY'
DATADOG_APP_NAME = 'my_app' # Used to namespace metric names
```

The API and app keys can be found at https://app.datadoghq.com/account/settings#api

Add the Datadog request handler to your middleware in `settings.py`.

```python
MIDDLEWARE_CLASSES += ('dj_datadog.middleware.DatadogMiddleware',)
```

For local development, you can add this to your `settings.py` file:

```python
DJ_DATADOG_DEBUG = True
```

The metrics will then be logged locally instead of making requests to Datadog.

## Usage

Once the middlewhere installed, you'll start receiving events in your Datadog
stream in the case of an app exception.

You will also have new timing metrics available:

- `my_app.request_time.{avg,max,min}`
- `my_app.errors`

Metrics are tagged with `path:/path/to/view`

Note: `my_app` will be replaced by whatever value you give for `DATADOG_APP_NAME`.
